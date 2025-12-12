import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


def message_handler(message):
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("Channel Layer Not COnfigured")
            return

        room_group_name = f"chat_{message.conversation.id}"

        sender_data = {
            "username": message.sender.username,
            "slug": message.sender.slug,
            "img": message.sender.img.url if message.sender.img else "",
            "verified": message.sender.verified,
            "is_admin": message.sender.is_admin,
        }

        attachments_data = []
        for att in message.attachments.all():
            attachment_info = {
                "url": att.file.url,
                "type": att.file_type,
                "name": att.file_name,
                "file_type": att.file_type,
            }
            attachments_data.append(attachment_info)

        time_str = message.timestamp.strftime("%I:%M %p")
        if time_str.startswith("0"):
            time_str = time_str[1:]
        formatted_time = time_str.lower()

        message_data = {
            "id": str(message.id),
            "sender": sender_data,
            "conv_id": str(message.conversation.id),
            "content": message.content or "",
            "is_group": message.conversation.is_group,
            "group_image": (
                message.conversation.group_image.url
                if message.conversation.is_group and message.conversation.group_image
                else None
            ),
            "read": message.read,
            "attachments": attachments_data,
            "timestamp": formatted_time,
        }

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "chat_message",
                "message": message_data,
                "sender_id": str(message.sender.id),
            },
        )

        logger.debug(f"Message {message.id} sent to WebSocket group {room_group_name}")

    except Exception as e:
        logger.error(f"Error sending Message: {str(e)}")
