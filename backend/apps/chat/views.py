from django.db.models import Q
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matching.models import Match
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationListView(generics.ListAPIView):
    """GET /api/chat/conversations/ — US-028"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            Conversation.objects.filter(
                Q(match__user1=user) | Q(match__user2=user)
            )
            .select_related('match__user1__profile', 'match__user2__profile')
            .prefetch_related('messages__sender')
            .order_by('-updated_at')
        )


class ConversationDetailView(generics.RetrieveAPIView):
    """GET /api/chat/conversations/<pk>/"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            Q(match__user1=user) | Q(match__user2=user)
        ).select_related('match__user1__profile', 'match__user2__profile')


class MessageListView(generics.ListAPIView):
    """GET /api/chat/conversations/<id>/messages/ — US-028"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        user = self.request.user
        conv_id = self.kwargs['conversation_id']
        conv = Conversation.objects.filter(
            id=conv_id
        ).filter(
            Q(match__user1=user) | Q(match__user2=user)
        ).first()

        if not conv:
            return Message.objects.none()

        # Marquer comme lus
        Message.objects.filter(
            conversation=conv, is_read=False
        ).exclude(sender=user).update(is_read=True)

        return Message.objects.filter(conversation=conv).select_related('sender')


class CreateConversationView(APIView):
    """POST /api/chat/conversations/create/ — { match_id }"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        match_id = request.data.get('match_id')
        user = request.user
        try:
            match = Match.objects.get(id=match_id, status='active')
        except Match.DoesNotExist:
            return Response({'detail': 'Match introuvable.'}, status=404)

        if match.user1 != user and match.user2 != user:
            return Response({'detail': 'Accès non autorisé.'}, status=403)

        conv, created = Conversation.objects.get_or_create(match=match)
        return Response(
            ConversationSerializer(conv, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class UnreadCountView(APIView):
    """GET /api/chat/unread/ — US-027"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        count = Message.objects.filter(
            conversation__match__user1=user, is_read=False
        ).exclude(sender=user).count()
        count += Message.objects.filter(
            conversation__match__user2=user, is_read=False
        ).exclude(sender=user).count()
        return Response({'unread_count': count})
