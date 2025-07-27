import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """Enhanced consumer for real-time notifications"""

    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            self.user = self.scope["user"]
            self.user_group_name = f"notifications_{self.user.id}"

            # Join user's notification group
            await self.channel_layer.group_add(self.user_group_name, self.channel_name)
            await self.accept()

            # Send unread notification count on connect
            unread_count = await self.get_unread_count()
            await self.send(text_data=json.dumps({
                "type": "unread_count",
                "count": unread_count
            }))

    async def disconnect(self, close_code):
        if hasattr(self, "user_group_name"):
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type")
            
            if message_type == "mark_read":
                notification_id = text_data_json.get("notification_id")
                if notification_id:
                    await self.mark_notification_read(notification_id)
                    # Send updated unread count
                    unread_count = await self.get_unread_count()
                    await self.send(text_data=json.dumps({
                        "type": "unread_count",
                        "count": unread_count
                    }))
            
            elif message_type == "mark_all_read":
                await self.mark_all_notifications_read()
                await self.send(text_data=json.dumps({
                    "type": "unread_count",
                    "count": 0
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON"
            }))

    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "id": event.get("notification_id"),
                    "message": event["message"],
                    "notification_type": event.get("notification_type", "general"),
                    "actor": event.get("actor", {}),
                    "data": event.get("data", {}),
                    "timestamp": event.get("timestamp"),
                    "read": event.get("read", False),
                }
            )
        )

    async def unread_count_update(self, event):
        """Send updated unread count"""
        await self.send(text_data=json.dumps({
            "type": "unread_count",
            "count": event["count"]
        }))

    @database_sync_to_async
    def get_unread_count(self):
        """Get count of unread notifications for the user"""
        return Notification.objects.filter(
            recipient=self.user, 
            read=False
        ).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a specific notification as read"""
        try:
            notification = Notification.objects.get(
                id=notification_id, 
                recipient=self.user
            )
            notification.read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read for the user"""
        Notification.objects.filter(
            recipient=self.user, 
            read=False
        ).update(read=True)
