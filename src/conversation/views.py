from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .serializers import ConversationSerializer, WebhookBaseSerializer
from .models import Conversation
from .repository import Repository


class WebhookView(APIView):
    def post(self, request):
        serializer = WebhookBaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.data
        try:
            return Repository.handle_hook(payload)
        except (KeyError, ValueError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ConversationDetailView(APIView):
    def get(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)
