import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer for real-time notifications"""

    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user = self.scope["user"]
            self.user_group_name = f"notifications_{self.user.id}"

            await self.channel_layer.group_add(self.user_group_name, self.channel_name)

            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "user_group_name"):
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )

    async def notification_message(self, event):
        # Send notification to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "message": event["message"],
                    "data": event.get("data", {}),
                }
            )
        )
