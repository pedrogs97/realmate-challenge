from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "type", "content", "timestamp"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "status", "created_at", "updated_at", "messages"]


class WebhookBaseSerializer(serializers.Serializer):
    FIELD_REQUIRED_ERROR = "This field is required"

    type = serializers.ChoiceField(
        choices=["NEW_CONVERSATION", "NEW_MESSAGE", "CLOSE_CONVERSATION"]
    )
    timestamp = serializers.DateTimeField()
    data = serializers.DictField()

    def validate(self, attrs) -> dict:
        event_type = attrs["type"]
        data = attrs["data"]

        if event_type == "NEW_CONVERSATION":
            if "id" not in data:
                raise serializers.ValidationError(
                    {"data": {"id": self.FIELD_REQUIRED_ERROR}}
                )

        elif event_type == "NEW_MESSAGE":
            for field in ["id", "content", "conversation_id"]:
                if field not in data:
                    raise serializers.ValidationError(
                        {"data": {field: self.FIELD_REQUIRED_ERROR}}
                    )

        elif event_type == "CLOSE_CONVERSATION" and "id" not in data:
            raise serializers.ValidationError(
                {"data": {"id": self.FIELD_REQUIRED_ERROR}}
            )

        return attrs
