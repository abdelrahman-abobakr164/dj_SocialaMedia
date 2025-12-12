from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation
import logging

User = get_user_model()

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        is_participant = await self.check_conversation_access()
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, "room_group_name") and not self.user.is_anonymous:
                await self.channel_layer.group_discard(
                    self.room_group_name, self.channel_name
                )
        except Exception:
            pass

    async def receive_json(self, content):
        pass

    async def chat_message(self, event):
        await self.send_json(
            {
                "type": "new_message",
                "message": event["message"],
            }
        )

    @database_sync_to_async
    def check_conversation_access(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False
