from celery import shared_task
from django.utils.timezone import now, timedelta
from .models import Conversation, Message
from django.utils.dateparse import parse_datetime
import time
from django.core.cache import cache
from django_redis import get_redis_connection
from .constants import BUFFER_TIMEOUT, INVALID_TIMEOUT
import json


@shared_task
def buffer_message_until_conversation_exists(payload: dict):
    """
    Buffers a message until the conversation exists.
    This task stores the message in a cache until the conversation is created.

    Args:
        payload (dict): The payload containing message data.
    Raises:
        ValueError: If the payload does not contain the required fields.
    """
    conv_id = payload["data"]["conversation_id"]
    msg_id = payload["data"]["id"]
    cache_key = f"buffer:{conv_id}:{msg_id}"
    cache.set(cache_key, json.dumps(payload), timeout=BUFFER_TIMEOUT)


@shared_task
def process_buffer_for_conversation(conversation_id: str, timestamp: str):
    """
    Processes buffered messages for a conversation.
    This task retrieves messages from the cache that were buffered while the conversation was being created.

    Args:
        conversation_id (str): The ID of the conversation.
        timestamp (str): The timestamp when the conversation was created.
    Raises:
        ValueError: If the conversation does not exist.
    """
    redis_conn = get_redis_connection("default")
    prefix = f"*:buffer:{conversation_id}:*"
    keys = redis_conn.keys(prefix)

    for key in keys:
        key_str = key.decode("utf-8")
        if key_str.startswith(":1:"):
            key_str = key_str[3:]
        payload_str = cache.get(key_str)
        if not payload_str:
            continue
        payload = json.loads(payload_str)
        message_timestamp = parse_datetime(payload["timestamp"])

        conversation_timestamp = parse_datetime(timestamp)
        diff_timestamp = (
            conversation_timestamp - message_timestamp
            if message_timestamp and conversation_timestamp
            else INVALID_TIMEOUT
        )
        total_seconds = (
            diff_timestamp.total_seconds()
            if isinstance(diff_timestamp, timedelta)
            else diff_timestamp
        )

        if total_seconds <= BUFFER_TIMEOUT:
            from .handlers import handle_new_message

            try:
                handle_new_message(payload, from_buffer=True)
            except Exception:
                pass
        cache.delete(key_str)


@shared_task(bind=True)
def process_conversation_messages(conversation_id: str, *args, **kwargs):
    """
    Processes messages in a conversation to group inbound messages
    that were received within 5 seconds of each other and creates an outbound message
    summarizing them.

    Args:
        conversation_id (str): The ID of the conversation to process messages for.
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return

    inbound_msgs = Message.objects.filter(
        conversation=conversation,
        type="INBOUND",
    ).order_by("timestamp")

    if not inbound_msgs.exists():
        return

    latest_outbound = (
        Message.objects.filter(conversation=conversation, type="OUTBOUND")
        .order_by("-timestamp")
        .first()
    )

    if latest_outbound:
        inbound_msgs = inbound_msgs.filter(timestamp__gt=latest_outbound.timestamp)

    if not inbound_msgs.exists():
        return

    grouped_ids = []
    current_group = []
    last_ts = None

    for msg in inbound_msgs:
        if not current_group:
            current_group = [msg]
            last_ts = msg.timestamp
            continue

        if last_ts and (msg.timestamp - last_ts).total_seconds() <= 5:
            current_group.append(msg)
        else:
            grouped_ids.append([str(m.id) for m in current_group])
            current_group = [msg]
        last_ts = msg.timestamp

    if current_group:
        grouped_ids.append([str(m.id) for m in current_group])

    content = "Mensagens recebidas:\n" + "\n".join(grouped_ids) + "\n"

    Message.objects.create(
        conversation=conversation,
        type="OUTBOUND",
        content=content,
        timestamp=now(),
    )


def schedule_message_processing(conversation_id):
    """
    Schedules the processing of messages in a conversation.
    This function is called after a new message is added to a conversation.
    It delays the processing of messages to allow for grouping of inbound messages.

    Args:
        conversation_id (str): The ID of the conversation to process messages for.
    """
    process_conversation_messages.apply_async(args=[str(conversation_id)], countdown=5)
