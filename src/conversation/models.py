import uuid
from django.db import models


class Conversation(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversations"


class Message(models.Model):
    TYPE_CHOICES = [
        ("INBOUND", "Inbound"),
        ("OUTBOUND", "Outbound"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField()

    class Meta:
        db_table = "messages"
