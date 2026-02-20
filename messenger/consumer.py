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
        msg = await self.save_message(content)
        created = msg.created_at.isoformat() if msg else None
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': content,
                'username': username,
                'created_at': created,
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'created_at': event.get('created_at'),
        }))

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