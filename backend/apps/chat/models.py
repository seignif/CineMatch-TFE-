from django.db import models
from django.conf import settings


class Conversation(models.Model):
    match = models.OneToOneField(
        'matching.Match',
        on_delete=models.CASCADE,
        related_name='conversation',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_conversation'

    def __str__(self):
        return f"Conversation #{self.pk}"

    def get_other_user(self, user):
        m = self.match
        return m.user2 if m.user1 == user else m.user1


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages_sent',
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'chat_message'
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.sender.email}] {self.content[:50]}"
