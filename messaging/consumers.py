from channels.generic.websocket import AsyncWebsocketConsumer
from accounts.models import User
from channels.db import database_sync_to_async
import json
from .models import Message

def get_thread_name(user1_id, user2_id):
    ids = sorted([str(user1_id), str(user2_id)])
    return f"private_chat_{ids[0]}_{ids[1]}"



class ChatConsumer(AsyncWebsocketConsumer):
    thread_name = None 
    other_user = None

    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
            return
        
        try:
            other_user_id = self.scope["url_route"]["kwargs"]["room_name"]
            self.other_user = await database_sync_to_async(User.objects.get)(id=other_user_id)
        except (ValueError, User.DoesNotExist):
            await self.close()
            return

        self.thread_name = get_thread_name(user.id, self.other_user.id)
        await self.channel_layer.group_add(self.thread_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if self.thread_name:
            await self.channel_layer.group_discard(self.thread_name, self.channel_name)

    async def receive(self, text_data):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        content = data.get('content')
        if not content:
            return
        message = await self.save_message(content)

        payload = {
            'type': 'chat_message',
            'message': {
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender.id if message.sender else None,
                'recipient_id': message.recipient.id if message.recipient else None,
                'timestamp': message.timestamp.isoformat() if getattr(message, 'timestamp', None) else None,
            }
        }
        await self.channel_layer.group_send(self.thread_name, payload)

    @database_sync_to_async
    def save_message(self, content):
        return Message.objects.create(
            content=content,
            sender=self.scope["user"],
            recipient=self.other_user
        )

    async def chat_message(self, event):
        # forward the message payload to WebSocket clients
        await self.send(text_data=json.dumps(event['message']))