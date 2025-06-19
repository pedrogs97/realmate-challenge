from . import handlers
from rest_framework import status
from rest_framework.response import Response


class Repository:
    """
    Repository class for handling conversation-related operations.
    This class provides methods to handle incoming webhook payloads for conversation events.
    """

    @staticmethod
    def handle_hook(payload: dict) -> Response:
        """
        Handle incoming webhook payloads for conversation events.

        Args:
            payload (dict): The payload containing event data.
        Returns:
            Response: HTTP response indicating the result of the operation.
        """
        hook_type = payload.get("type")
        if hook_type == "NEW_CONVERSATION":
            try:
                handlers.handle_new_conversation(payload)
                return Response(status=status.HTTP_201_CREATED)
            except ValueError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif hook_type == "NEW_MESSAGE":
            try:
                handlers.handle_new_message(payload)
                return Response(status=status.HTTP_202_ACCEPTED)
            except ValueError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif hook_type == "CLOSE_CONVERSATION":
            try:
                handlers.handle_close_conversation(payload)
                return Response(status=status.HTTP_200_OK)
            except ValueError:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Unknow type"}, status=status.HTTP_400_BAD_REQUEST)
