from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from django.db import transaction, IntegrityError
from .models import Conversation, Message
from .tasks import (
    schedule_message_processing,
    buffer_message_until_conversation_exists,
    process_buffer_for_conversation,
)


@transaction.atomic
def handle_new_conversation(payload):
    data = payload["data"]
    if Conversation.objects.filter(id=data["id"]).exists():
        raise ValueError("Conversation already exists")
    Conversation.objects.create(id=data["id"], status="OPEN")
    process_buffer_for_conversation.delay(data["id"], payload["timestamp"])


@transaction.atomic
def handle_new_message(payload, from_buffer=False):
    data = payload["data"]
    conv_id = data["conversation_id"]
    ts = parse_datetime(payload["timestamp"])
    try:
        conversation = Conversation.objects.get(id=conv_id)
        if conversation.status == "CLOSED":
            raise ValueError("Conversation is closed")
    except Conversation.DoesNotExist:
        if from_buffer:
            raise ValueError("Conversation does not exist and exceeded delay tolerance")
        buffer_message_until_conversation_exists.delay(payload)
        return

    try:
        Message.objects.create(
            id=data["id"],
            conversation=conversation,
            type="INBOUND",
            content=data["content"],
            timestamp=ts,
        )
    except IntegrityError:
        raise ValueError("Message ID already exists")

    schedule_message_processing(conversation.id)


@transaction.atomic
def handle_close_conversation(payload):
    data = payload["data"]
    try:
        conv = Conversation.objects.get(id=data["id"])
        if conv.status == "CLOSED":
            raise ValueError("Already closed")
        conv.status = "CLOSED"
        conv.save()
    except Conversation.DoesNotExist:
        raise ValueError("Conversation not found")
