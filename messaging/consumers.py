import json
from uuid import UUID
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()


def get_thread_name(user1_id, user2_id):
    ids = sorted([str(user1_id), str(user2_id)])
    return f"private_chat_{ids[0]}_{ids[1]}"


@database_sync_to_async
def get_user_by_id(user_id):
    return User.objects.get(id=user_id)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            print("WS reject: anonymous user")
            await self.close()
            return

        try:
            other_user_id = UUID(self.scope["url_route"]["kwargs"]["room_name"])
            self.other_user = await get_user_by_id(other_user_id)
        except Exception as e:
            print("WS reject: invalid room or user not found:", e)
            await self.close()
            return

        self.thread_name = get_thread_name(self.user.id, self.other_user.id)

        try:
            await self.channel_layer.group_add(self.thread_name, self.channel_name)
        except Exception as e:
            print("WS reject: channel layer error:", e)
            await self.close()
            return

        await self.accept()
        print(f"WS connection accepted: {self.user} <-> {self.other_user}")

    async def disconnect(self, code):
        if self.thread_name:
            await self.channel_layer.group_discard(self.thread_name, self.channel_name)
        print(f"WS disconnected: {self.user} <-> {self.other_user}")

    async def receive(self, text_data):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            print("Invalid JSON received:", text_data)
            return

        content = data.get("content")
        if not content:
            print("No content in message:", data)
            return

        message = await self.save_message(content)

        try:
            await self.channel_layer.group_send(
                self.thread_name,
                {
                    "type": "chat_message",
                    "message": {
                        "id": str(message.id),
                        "content": message.content,
                        "sender_id": str(message.sender.id),
                        "recipient_id": str(message.recipient.id),
                        "timestamp": message.timestamp.isoformat(),
                    },
                },
            )
            print(f"Message sent to group {self.thread_name}: {message.content}")
        except Exception as e:
            print("CHANNEL LAYER ERROR on group_send:", e)

    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps(event["message"]))
            print("Message sent to WebSocket:", event["message"])
        except Exception as e:
            print("WS SEND ERROR:", e)

    @database_sync_to_async
    def save_message(self, content):
        return Message.objects.create(
            content=content,
            sender=self.user,        # must be a User object
            recipient=self.other_user,
        )
