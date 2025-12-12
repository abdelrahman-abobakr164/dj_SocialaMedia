from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from notifications.models import Notification
from django.utils.timesince import timesince
from django.utils.timezone import now

User = get_user_model()


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f"notifications_{self.user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        unread_count = await self.get_unread_count()
        await self.send_json({"type": "unread_count", "count": unread_count})

    async def disconnect(self, close_code):
        try:
            if hasattr(self, "user") and not self.user.is_anonymous:
                await self.channel_layer.group_discard(
                    self.group_name, self.channel_name
                )
        except Exception:
            pass

    async def receive_json(self, content):
        message_type = content.get("type")

        if message_type == "get_notifications":
            notifications = await self.get_notifications()
            await self.send_json(
                {"type": "notifications_list", "notifications": notifications}
            )

        elif message_type == "get_unread_count":
            unread_count = await self.get_unread_count()
            await self.send_json({"type": "unread_count", "count": unread_count})

    async def notification_message(self, event):
        await self.send_json(
            {"type": "new_notification", "notification": event["notification"]}
        )

    @database_sync_to_async
    def get_notifications(self):
        notifications = (
            Notification.objects.filter(recipient=self.user)
            .select_related("actor", "content_type")
            .prefetch_related("content_object")
            .order_by("-created_at")
        )

        notification_list = []
        for n in notifications:
            content_object_data = {}
            if n.content_object:
                content_obj = n.content_object

                content_object_data = {
                    "content": getattr(content_obj, "content", ""),
                    "caption": getattr(content_obj, "caption", ""),
                    "body": getattr(content_obj, "body", ""),
                }

                if hasattr(content_obj, "conversation") and content_obj.conversation:
                    content_object_data["conversation"] = {
                        "id": str(content_obj.conversation.id)
                    }
                else:
                    content_object_data["conversation"] = {"id": ""}

            notification_list.append(
                {
                    "id": str(n.id),
                    "actor": {
                        "username": n.actor.username,
                        "slug": n.actor.slug,
                        "img": n.actor.img.url,
                    },
                    "ntype": n.ntype,
                    "content_object": content_object_data,
                    "created_at": n.created_at.isoformat(),
                    "created_at": f"{timesince(n.created_at, now())} ago",
                    "object_id": str(n.object_id),
                }
            )

        return notification_list

    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(recipient=self.user, read=False).count()
