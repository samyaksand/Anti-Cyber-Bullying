import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from complaints.permissions import user_is_admin
from .models import Conversation, Message

ADMIN_GROUP = 'chat_admin_inbox'


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user = user
        self.is_admin = await database_sync_to_async(user_is_admin)(user)

        if self.is_admin:
            self.group_name = ADMIN_GROUP
        else:
            conversation = await database_sync_to_async(self._get_or_create_conversation)(user)
            self.conversation_id = conversation.id
            self.group_name = f'conversation_{conversation.id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        if self.is_admin:
            await self.channel_layer.group_add(ADMIN_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if getattr(self, 'is_admin', False):
            await self.channel_layer.group_discard(ADMIN_GROUP, self.channel_name)

    async def receive_json(self, content, **kwargs):
        event_type = content.get('type')

        if event_type == 'typing':
            await self._handle_typing(content)
        elif event_type == 'message':
            await self._handle_message(content)
        elif event_type == 'read':
            await self._handle_read(content)

    async def _handle_typing(self, content):
        if self.is_admin:
            conversation_id = content.get('conversation_id')
            group = f'conversation_{conversation_id}'
        else:
            conversation_id = self.conversation_id
            group = self.group_name

        await self.channel_layer.group_send(group, {
            'type': 'chat.typing',
            'is_from_admin': self.is_admin,
            'conversation_id': conversation_id,
        })

    async def _handle_message(self, content):
        body = (content.get('body') or '').strip()
        if not body:
            return

        if self.is_admin:
            conversation_id = content.get('conversation_id')
            if not conversation_id:
                return
            conversation = await database_sync_to_async(Conversation.objects.get)(pk=conversation_id)
        else:
            conversation = await database_sync_to_async(Conversation.objects.get)(pk=self.conversation_id)

        message = await database_sync_to_async(Message.objects.create)(
            conversation=conversation,
            is_from_admin=self.is_admin,
            sender=self.user,
            body=body,
        )

        payload = {
            'type': 'chat.message',
            'id': message.id,
            'conversation_id': conversation.id,
            'is_from_admin': self.is_admin,
            'body': message.body,
            'created_at': message.created_at.isoformat(),
        }

        await self.channel_layer.group_send(f'conversation_{conversation.id}', payload)
        await self.channel_layer.group_send(ADMIN_GROUP, payload)

    async def _handle_read(self, content):
        if self.is_admin:
            conversation_id = content.get('conversation_id')
        else:
            conversation_id = getattr(self, 'conversation_id', None)
        if not conversation_id:
            return
        await database_sync_to_async(self._mark_read)(conversation_id)
        await self.channel_layer.group_send(f'conversation_{conversation_id}', {
            'type': 'chat.read',
            'conversation_id': conversation_id,
            'by_admin': self.is_admin,
        })

    def _mark_read(self, conversation_id):
        Message.objects.filter(
            conversation_id=conversation_id,
            is_from_admin=not self.is_admin,
            read_at__isnull=True,
        ).update(read_at=timezone.now())

    def _get_or_create_conversation(self, user):
        conversation, _ = Conversation.objects.get_or_create(user=user)
        return conversation

    async def chat_message(self, event):
        await self.send_json(event)

    async def chat_typing(self, event):
        await self.send_json(event)

    async def chat_read(self, event):
        await self.send_json(event)
