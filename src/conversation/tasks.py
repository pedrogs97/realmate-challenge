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
def buffer_message_until_conversation_exists(payload):
    conv_id = payload["data"]["conversation_id"]
    msg_id = payload["data"]["id"]
    cache_key = f"buffer:{conv_id}:{msg_id}"
    cache.set(cache_key, json.dumps(payload), timeout=BUFFER_TIMEOUT)


@shared_task
def process_buffer_for_conversation(conversation_id, timestamp):
    redis_conn = get_redis_connection("default")
    prefix = f"buffer:{conversation_id}:*"
    keys = redis_conn.keys(prefix)

    for key in keys:
        payload_str = cache.get(key)
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
        cache.delete(key)


@shared_task(bind=True)
def process_conversation_messages(self, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return

    # Agrupar mensagens INBOUND ainda não respondidas nos últimos ~5s
    time.sleep(5)  # tolerância para agrupamento
    five_seconds_ago = now() - timedelta(seconds=5)
    inbound_msgs = Message.objects.filter(
        conversation=conversation,
        type="INBOUND",
        timestamp__lte=five_seconds_ago,
    ).order_by("timestamp")

    if not inbound_msgs.exists():
        return

    latest_outbound = (
        Message.objects.filter(conversation=conversation, type="OUTBOUND")
        .order_by("-timestamp")
        .first()
    )

    if latest_outbound:
        # excluir mensagens já respondidas
        inbound_msgs = inbound_msgs.filter(timestamp__gt=latest_outbound.timestamp)

    if not inbound_msgs.exists():
        return

    ids = [str(m.id) for m in inbound_msgs]
    content = """Mensagens recebidas:\n{}\n""".format("\n".join(ids))

    Message.objects.create(
        conversation=conversation,
        type="OUTBOUND",
        content=content,
        timestamp=now(),
    )


def schedule_message_processing(conversation_id):
    process_conversation_messages.apply_async(args=[str(conversation_id)], countdown=5)
