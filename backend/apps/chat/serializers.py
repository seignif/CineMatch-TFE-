from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_name = serializers.CharField(source='sender.first_name', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender_id', 'sender_name', 'content', 'is_read', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    match_score = serializers.IntegerField(source='match.score_compatibilite', read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'other_user', 'last_message', 'unread_count', 'match_score', 'updated_at']

    def get_other_user(self, obj):
        user = self.context['request'].user
        other = obj.get_other_user(user)
        profile = getattr(other, 'profile', None)
        return {
            'id': other.id,
            'first_name': other.first_name,
            'city': other.city,
            'profile_picture': (
                profile.profile_picture.url
                if profile and profile.profile_picture else None
            ),
        }

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if not msg:
            return None
        return {
            'content': msg.content,
            'sender_name': msg.sender.first_name,
            'created_at': msg.created_at.isoformat(),
        }

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()
