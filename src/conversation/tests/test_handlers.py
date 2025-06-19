from django.test import TestCase
from django.utils.timezone import now
from unittest.mock import patch
import uuid

from conversation.models import Conversation, Message
from conversation.handlers import (
    handle_new_conversation,
    handle_new_message,
    handle_close_conversation,
)


class HandlersTestCase(TestCase):
    def setUp(self):
        self.conversation_id = uuid.uuid4()
        self.message_id = uuid.uuid4()
        self.timestamp = now().isoformat()
        self.conversation_data = {
            "data": {"id": self.conversation_id},
            "timestamp": self.timestamp,
        }
        self.message_data = {
            "data": {
                "id": self.message_id,
                "conversation_id": self.conversation_id,
                "content": "Hello!",
            },
            "timestamp": self.timestamp,
        }

    @patch("conversation.handlers.process_buffer_for_conversation.delay")
    def test_handle_new_conversation_creates_conversation(self, mock_delay):
        handle_new_conversation(self.conversation_data)
        conv = Conversation.objects.get(id=self.conversation_id)
        self.assertEqual(conv.status, "OPEN")
        mock_delay.assert_called_once_with(self.conversation_id, self.timestamp)

    def test_handle_new_conversation_raises_if_exists(self):
        Conversation.objects.create(id=self.conversation_id, status="OPEN")
        with self.assertRaises(ValueError):
            handle_new_conversation(self.conversation_data)

    @patch("conversation.handlers.buffer_message_until_conversation_exists.delay")
    def test_handle_new_message_buffers_if_conversation_missing(self, mock_delay):
        handle_new_message(self.message_data)
        mock_delay.assert_called_once_with(self.message_data)

    def test_handle_new_message_raises_if_conversation_missing_from_buffer(self):
        with self.assertRaises(ValueError):
            handle_new_message(self.message_data, from_buffer=True)

    def test_handle_new_message_raises_if_conversation_closed(self):
        Conversation.objects.create(id=self.conversation_id, status="CLOSED")
        with self.assertRaises(ValueError):
            handle_new_message(self.message_data)

    @patch("conversation.handlers.schedule_message_processing")
    def test_handle_new_message_creates_message(self, mock_schedule):
        Conversation.objects.create(id=self.conversation_id, status="OPEN")
        handle_new_message(self.message_data)
        msg = Message.objects.get(id=self.message_id)
        self.assertEqual(msg.content, "Hello!")
        mock_schedule.assert_called_once_with(self.conversation_id)

    @patch("conversation.handlers.schedule_message_processing")
    def test_handle_new_message_raises_if_message_exists(self, mock_schedule):
        conv = Conversation.objects.create(id=self.conversation_id, status="OPEN")
        Message.objects.create(
            id=self.message_id,
            conversation=conv,
            type="INBOUND",
            content="Hello!",
            timestamp=now(),
        )
        with self.assertRaises(ValueError):
            handle_new_message(self.message_data)

    def test_handle_close_conversation_closes(self):
        conv = Conversation.objects.create(id=self.conversation_id, status="OPEN")
        handle_close_conversation(self.conversation_data)
        conv.refresh_from_db()
        self.assertEqual(conv.status, "CLOSED")

    def test_handle_close_conversation_raises_if_closed(self):
        Conversation.objects.create(id=self.conversation_id, status="CLOSED")
        with self.assertRaises(ValueError):
            handle_close_conversation(self.conversation_data)

    def test_handle_close_conversation_raises_if_not_found(self):
        with self.assertRaises(ValueError):
            handle_close_conversation(self.conversation_data)
