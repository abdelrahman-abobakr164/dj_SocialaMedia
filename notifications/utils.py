from datetime import timedelta
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()
channel_layer = get_channel_layer()


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


def send_notification(actor, recipient, ntype, content_object=None, extra_data=None):
    """
    Send a notification and broadcast it via WebSocket
    """
    # Create notification in database
    notification = Notification.objects.create(
        actor=actor,
        recipient=recipient,
        ntype=ntype,
        content_object=content_object
    )
    
    # Prepare WebSocket message
    message_data = {
        "type": "notification_message",
        "notification_id": str(notification.id),
        "message": generate_notification_message(notification),
        "notification_type": ntype,
        "actor": {
            "id": actor.id,
            "username": actor.username,
            "avatar": actor.img.url if actor.img else "",
        },
        "timestamp": notification.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "read": False,
        "data": extra_data or {}
    }
    
    # Send to user's notification group
    async_to_sync(channel_layer.group_send)(
        f"notifications_{recipient.id}",
        message_data
    )
    
    return notification


def send_real_time_message(conversation_id, message_data):
    """
    Send a real-time chat message to all participants in a conversation
    """
    async_to_sync(channel_layer.group_send)(
        f"chat_{conversation_id}",
        {
            "type": "chat_message",
            **message_data
        }
    )


def generate_notification_message(notification):
    """
    Generate human-readable notification message
    """
    actor = notification.actor.username
    ntype = notification.ntype
    
    messages = {
        "Follow Request": f"{actor} sent you a follow request",
        "Follow Accepted": f"{actor} accepted your follow request",
        "New Follower": f"{actor} started following you",
        "Like": f"{actor} liked your post",
        "Comment": f"{actor} commented on your post",
        "Message": f"{actor} sent you a message",
    }
    
    return messages.get(ntype, f"{actor} performed an action")


def update_unread_count(user_id):
    """
    Send updated unread notification count to user
    """
    try:
        unread_count = Notification.objects.filter(
            recipient_id=user_id, 
            read=False
        ).count()
        
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user_id}",
            {
                "type": "unread_count_update",
                "count": unread_count
            }
        )
    except Exception as e:
        print(f"Error updating unread count: {e}")
