from django.test import TestCase
from unittest.mock import patch
from rest_framework import status
import uuid

from conversation.repository import Repository


class RepositoryTestCase(TestCase):
    def setUp(self):
        self.payload_base = {
            "data": {"id": uuid.uuid4().hex},
            "timestamp": "2024-06-19T12:00:00Z",
        }

    @patch("conversation.handlers.handle_new_conversation")
    def test_handle_hook_new_conversation_success(self, mock_handler):
        payload = {**self.payload_base, "type": "NEW_CONVERSATION"}
        response = Repository.handle_hook(payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_handler.assert_called_once_with(payload)

    @patch("conversation.handlers.handle_new_conversation", side_effect=ValueError)
    def test_handle_hook_new_conversation_error(self, mock_handler):
        payload = {**self.payload_base, "type": "NEW_CONVERSATION"}
        response = Repository.handle_hook(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("conversation.handlers.handle_new_message")
    def test_handle_hook_new_message_success(self, mock_handler):
        payload = {**self.payload_base, "type": "NEW_MESSAGE"}
        response = Repository.handle_hook(payload)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_handler.assert_called_once_with(payload)

    @patch("conversation.handlers.handle_new_message", side_effect=ValueError)
    def test_handle_hook_new_message_error(self, mock_handler):
        payload = {**self.payload_base, "type": "NEW_MESSAGE"}
        response = Repository.handle_hook(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("conversation.handlers.handle_close_conversation")
    def test_handle_hook_close_conversation_success(self, mock_handler):
        payload = {**self.payload_base, "type": "CLOSE_CONVERSATION"}
        response = Repository.handle_hook(payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_handler.assert_called_once_with(payload)

    @patch("conversation.handlers.handle_close_conversation", side_effect=ValueError)
    def test_handle_hook_close_conversation_error(self, mock_handler):
        payload = {**self.payload_base, "type": "CLOSE_CONVERSATION"}
        response = Repository.handle_hook(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_handle_hook_unknown_type(self):
        payload = {**self.payload_base, "type": "UNKNOWN_TYPE"}
        response = Repository.handle_hook(payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(response.data)
        self.assertIn("error", response.data)
