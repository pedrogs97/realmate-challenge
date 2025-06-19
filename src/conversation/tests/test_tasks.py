from django.test import TestCase
from unittest.mock import patch
from conversation.tasks import (
    buffer_message_until_conversation_exists,
    process_buffer_for_conversation,
    process_conversation_messages,
    schedule_message_processing,
)
from conversation.models import Conversation, Message
from django.utils.timezone import now, timedelta
import json
import uuid
from src.conversation.constants import BUFFER_TIMEOUT


class TasksTestCase(TestCase):
    def setUp(self):
        self.conv_id = uuid.uuid4()
        self.msg_id = uuid.uuid4()
        self.timestamp = now().isoformat()
        self.payload = {
            "data": {
                "conversation_id": self.conv_id.hex,
                "id": self.msg_id.hex,
                "content": "Oi",
            },
            "timestamp": self.timestamp,
        }

    @patch("conversation.tasks.cache")
    def test_buffer_message_until_conversation_exists(self, mock_cache):
        buffer_message_until_conversation_exists(self.payload)
        cache_key = f"buffer:{self.conv_id.hex}:{self.msg_id.hex}"
        mock_cache.set.assert_called_once_with(
            cache_key,
            json.dumps(self.payload),
            timeout=BUFFER_TIMEOUT,
        )

    @patch("conversation.tasks.cache")
    @patch("conversation.tasks.get_redis_connection")
    @patch("conversation.handlers.handle_new_message")
    def test_process_buffer_for_conversation_calls_handle_new_message(
        self, mock_handle, mock_redis, mock_cache
    ):
        mock_redis.return_value.keys.return_value = [b"buffer:conv1:msg1"]
        mock_cache.get.return_value = json.dumps(self.payload)
        mock_cache.delete.return_value = None

        process_buffer_for_conversation(self.conv_id.hex, self.timestamp)
        mock_handle.assert_called_once()
        mock_cache.delete.assert_called_once()

    @patch("conversation.tasks.process_conversation_messages.apply_async")
    def test_schedule_message_processing(self, mock_apply_async):
        schedule_message_processing(self.conv_id.hex)
        mock_apply_async.assert_called_once()
