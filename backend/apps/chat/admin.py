from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['match', 'created_at', 'updated_at']
    raw_id_fields = ['match']
    ordering = ['-updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'content_preview', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['sender__email', 'content']
    raw_id_fields = ['conversation', 'sender']
    ordering = ['-created_at']

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = 'Message'
