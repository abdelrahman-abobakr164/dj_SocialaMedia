from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from asgiref.sync import async_to_sync
from django.utils.timesince import timesince
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def send_notification_to_user(notification):
    try:
        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.warning("Channel layer not configured")
            return

        group_name = f"notifications_{notification.recipient.id}"
        from .consumers import NotificationConsumer

        notification_data = {
            "id": str(notification.id),
            "actor": {
                "username": notification.actor.username,
                "slug": notification.actor.slug,
                "img": notification.actor.img.url,
            },
            "ntype": notification.ntype,
            "content_object": NotificationConsumer.serialize_content_object(
                notification.content_object
            ),
            "created_at": f"{timesince(notification.created_at, now())} ago",
            "object_id": str(notification.object_id),
        }

        unread_count = Notification.objects.filter(
            recipient=notification.recipient, read=False
        ).count()

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notification_message",
                "notification": notification_data,
                "unread_count": unread_count,
            },
        )

        logger.info(f"Notification sent to user {notification.recipient.id}")

    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")


def filter_notifications_by_date_range(queryset, date_range):
    today = timezone.now().date()

    if date_range == "today":
        return queryset.filter(created_at__date=today)
    elif date_range == "yesterday":
        yesterday = today - timedelta(days=1)
        return queryset.filter(created_at__date=yesterday)
    elif date_range == "last_30_days":
        thirty_days_ago = today - timedelta(days=30)
        return queryset.filter(created_at__date__gte=thirty_days_ago)
    else:
        return queryset.all()
