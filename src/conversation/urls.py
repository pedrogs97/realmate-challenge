from django.urls import path
from .views import WebhookView, ConversationDetailView

urlpatterns = [
    path("webhook/", WebhookView.as_view(), name="webhook"),
    path(
        "conversations/<uuid:pk>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
]
