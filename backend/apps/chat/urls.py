from django.urls import path
from .views import (
    ConversationListView, ConversationDetailView,
    MessageListView, CreateConversationView, UnreadCountView,
)

urlpatterns = [
    path('conversations/', ConversationListView.as_view()),
    path('conversations/create/', CreateConversationView.as_view()),
    path('conversations/<int:pk>/', ConversationDetailView.as_view()),
    path('conversations/<int:conversation_id>/messages/', MessageListView.as_view()),
    path('unread/', UnreadCountView.as_view()),
]
