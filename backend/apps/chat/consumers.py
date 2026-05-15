import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket: ws://localhost:8000/ws/chat/{conversation_id}/?token=JWT
    """

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close()
            return

        has_access = await self.check_access(user, self.conversation_id)
        if not has_access:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Envoyer l'historique des 50 derniers messages
        messages = await self.get_recent_messages(self.conversation_id)
        await self.send(text_data=json.dumps({'type': 'history', 'messages': messages}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type', 'message')
        user = self.scope['user']

        if msg_type == 'message':
            content = data.get('content', '').strip()
            if not content:
                return
            message = await self.save_message(user, self.conversation_id, content)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'chat_message', 'message': message}
            )

        elif msg_type == 'read':
            await self.mark_messages_read(self.conversation_id, user)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'type': 'message', 'message': event['message']}))

    @database_sync_to_async
    def check_access(self, user, conversation_id):
        from .models import Conversation
        from django.db.models import Q
        return Conversation.objects.filter(
            id=conversation_id
        ).filter(
            Q(match__user1=user) | Q(match__user2=user)
        ).exists()

    @database_sync_to_async
    def save_message(self, user, conversation_id, content):
        from .models import Conversation, Message
        conv = Conversation.objects.get(id=conversation_id)
        msg = Message.objects.create(conversation=conv, sender=user, content=content)
        # Touch updated_at
        conv.save(update_fields=['updated_at'])
        return {
            'id': msg.id,
            'sender_id': user.id,
            'sender_name': user.first_name,
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'is_read': msg.is_read,
        }

    @database_sync_to_async
    def get_recent_messages(self, conversation_id, limit=50):
        from .models import Message
        msgs = (
            Message.objects.filter(conversation_id=conversation_id)
            .select_related('sender')
            .order_by('-created_at')[:limit]
        )
        return [
            {
                'id': m.id,
                'sender_id': m.sender.id,
                'sender_name': m.sender.first_name,
                'content': m.content,
                'created_at': m.created_at.isoformat(),
                'is_read': m.is_read,
            }
            for m in reversed(list(msgs))
        ]

    @database_sync_to_async
    def mark_messages_read(self, conversation_id, user):
        from .models import Message
        Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(sender=user).update(is_read=True)


class GroupChatConsumer(AsyncWebsocketConsumer):
    """
    US-042 : Chat de groupe temps réel.
    URL: ws://localhost:8000/ws/group/<group_id>/?token=JWT
    Seuls les membres status='accepted' peuvent se connecter.
    """

    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'group_{self.group_id}'
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close()
            return

        if not await self.check_membership(user, self.group_id):
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        messages = await self.get_recent_messages(self.group_id)
        await self.send(text_data=json.dumps({'type': 'history', 'messages': messages}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get('type') == 'message':
            content = data.get('content', '').strip()
            if not content:
                return
            user = self.scope['user']
            message = await self.save_message(user, self.group_id, content)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'group_message', 'message': message},
            )

    async def group_message(self, event):
        await self.send(text_data=json.dumps({'type': 'message', 'message': event['message']}))

    @database_sync_to_async
    def check_membership(self, user, group_id):
        from apps.matching.models import GroupMember
        return GroupMember.objects.filter(group_id=group_id, user=user, status='accepted').exists()

    @database_sync_to_async
    def save_message(self, user, group_id, content):
        from apps.matching.models import Group, GroupMessage
        group = Group.objects.get(id=group_id)
        msg = GroupMessage.objects.create(group=group, sender=user, content=content)
        group.save(update_fields=['updated_at'])
        return {
            'id': msg.id,
            'sender_id': user.id,
            'sender_name': user.first_name,
            'content': msg.content,
            'is_system': msg.is_system,
            'created_at': msg.created_at.isoformat(),
        }

    @database_sync_to_async
    def get_recent_messages(self, group_id, limit=50):
        from apps.matching.models import GroupMessage
        msgs = (
            GroupMessage.objects.filter(group_id=group_id)
            .select_related('sender')
            .order_by('-created_at')[:limit]
        )
        return [
            {
                'id': m.id,
                'sender_id': m.sender.id,
                'sender_name': m.sender.first_name,
                'content': m.content,
                'is_system': m.is_system,
                'created_at': m.created_at.isoformat(),
            }
            for m in reversed(list(msgs))
        ]
