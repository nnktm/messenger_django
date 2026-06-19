import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        await self.send(text_data=json.dumps({'message': message}))


class PrivateChatConsumer(AsyncWebsocketConsumer):
    """個人チャット用。room_id でグループに参加し、メッセージをDB保存して相手にも配信。"""

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'private_room_{self.room_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = (data.get('message') or '').strip()
        if not content:
            return
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            return
        username = user.username
        avatar_url = await self.get_avatar_url(user)
        msg = await self.save_message(content)
        created = msg.created_at.isoformat() if msg else None
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': content,
                'username': username,
                'avatar_url': avatar_url,
                'created_at': created,
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'avatar_url': event.get('avatar_url'),
            'created_at': event.get('created_at'),
        }))

    @database_sync_to_async
    def get_avatar_url(self, user):
        from .models import get_avatar_url_for_user
        return get_avatar_url_for_user(user)

    @database_sync_to_async
    def save_message(self, content):
        from .models import private_room, private_message
        try:
            room = private_room.objects.get(pk=self.room_id)
        except private_room.DoesNotExist:
            return None
        return private_message.objects.create(
            room=room, sender=self.scope['user'], content=content
        )


class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'group_room_{self.room_id}'
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        is_member = await self.user_is_member(user)
        if not is_member:
            await self.close()
            return
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = (data.get('message') or '').strip()
        if not content:
            return
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            return
        if not await self.user_is_member(user):
            return
        username = user.username
        avatar_url = await self.get_avatar_url(user)
        msg = await self.save_message(content)
        created = msg.created_at.isoformat() if msg else None
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': content,
                'username': username,
                'avatar_url': avatar_url,
                'created_at': created,
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'avatar_url': event.get('avatar_url'),
            'created_at': event.get('created_at'),
        }))

    @database_sync_to_async
    def user_is_member(self, user):
        from .models import private_group_room
        return private_group_room.objects.filter(pk=self.room_id, members=user).exists()

    @database_sync_to_async
    def get_avatar_url(self, user):
        from .models import get_avatar_url_for_user
        return get_avatar_url_for_user(user)

    @database_sync_to_async
    def save_message(self, content):
        from .models import private_group_room, private_group_message
        try:
            room = private_group_room.objects.get(pk=self.room_id)
        except private_group_room.DoesNotExist:
            return None
        return private_group_message.objects.create(
            room=room, sender=self.scope['user'], content=content
        )


class AIChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        if not await self.user_owns_room(user):
            await self.close()
            return
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = (data.get('message') or '').strip()
        if not content:
            return
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            return

        room = await self.get_room()
        if not room:
            return

        user_avatar_url = await self.get_avatar_url(user)
        ai_icon_url = await self.get_ai_icon_url(room)
        user_msg = await self.save_message('user', content)
        await self.send(text_data=json.dumps({
            'message': content,
            'username': user.username,
            'avatar_url': user_avatar_url,
            'created_at': user_msg.created_at.isoformat() if user_msg else None,
            'is_ai': False,
        }))

        try:
            ai_content = await self.generate_reply(content)
        except Exception as exc:
            ai_content = f'（エラー: {exc}）'

        ai_msg = await self.save_message('assistant', ai_content)
        await self.send(text_data=json.dumps({
            'message': ai_content,
            'username': room.name,
            'avatar_url': ai_icon_url,
            'created_at': ai_msg.created_at.isoformat() if ai_msg else None,
            'is_ai': True,
        }))

    @database_sync_to_async
    def user_owns_room(self, user):
        from .models import ai_character_room
        return ai_character_room.objects.filter(pk=self.room_id, owner=user).exists()

    @database_sync_to_async
    def get_room(self):
        from .models import ai_character_room
        try:
            return ai_character_room.objects.get(pk=self.room_id)
        except ai_character_room.DoesNotExist:
            return None

    @database_sync_to_async
    def get_avatar_url(self, user):
        from .models import get_avatar_url_for_user
        return get_avatar_url_for_user(user)

    @database_sync_to_async
    def get_ai_icon_url(self, room):
        from .models import get_ai_icon_url_for_room
        return get_ai_icon_url_for_room(room)

    @database_sync_to_async
    def save_message(self, role, content):
        from .models import ai_character_room, ai_character_message
        try:
            room = ai_character_room.objects.get(pk=self.room_id)
        except ai_character_room.DoesNotExist:
            return None
        return ai_character_message.objects.create(
            room=room,
            role=role,
            content=content,
        )

    @database_sync_to_async
    def generate_reply(self, user_message):
        from .models import ai_character_room, ai_character_message
        from .ai import generate_ai_reply

        room = ai_character_room.objects.get(pk=self.room_id)
        history = list(
            ai_character_message.objects.filter(room=room).order_by('created_at')[:50]
        )
        if history and history[-1].role == ai_character_message.Role.USER:
            history = history[:-1]
        return generate_ai_reply(room, history, user_message)