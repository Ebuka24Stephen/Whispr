from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
import json
from .models import Message
from uuid import UUID

def get_thread_name(user1_id, user2_id):
    ids = sorted([str(user1_id), str(user2_id)])
    return f"private_chat_{ids[0]}_{ids[1]}"


@database_sync_to_async
def get_user_by_id(user_id):
    User = get_user_model()
    return User.objects.get(id=user_id)



class ChatConsumer(AsyncWebsocketConsumer):
    thread_name = None
    other_user = None

    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        try:
            other_user_id = UUID(self.scope["url_route"]["kwargs"]["room_name"])
            self.other_user = await get_user_by_id(other_user_id)
        except Exception:
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

        content = data.get("content")
        if not content:
            return

        message = await self.save_message(content)

        await self.channel_layer.group_send(
            self.thread_name,
            {
                "type": "chat_message",
                "message": {
                    "id": str(message.id),
                    "content": message.content,
                    "sender_id": str(message.sender_id),
                    "recipient_id": str(message.recipient_id),
                    "timestamp": message.timestamp.isoformat(),
                },
            },
        )

    @database_sync_to_async
    def save_message(self, content):
        return Message.objects.create(
            content=content,
            sender=self.scope["user"],
            recipient=self.other_user,
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
