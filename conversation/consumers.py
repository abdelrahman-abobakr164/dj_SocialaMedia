import json
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message
from django.utils import timezone
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(WebsocketConsumer):

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        self.user = self.scope["user"]

        logger.info(
            f"WebSocket connection attempt for conversation {self.conversation_id}"
        )

        if self.user.is_anonymous:
            logger.warning(
                f"Anonymous user attempted to connect to conversation {self.conversation_id}"
            )
            await self.close()
            return

        logger.info(
            f"User {self.user.username} attempting to connect to conversation {self.conversation_id}"
        )

        is_participant = await self.check_conversation_access()
        if not is_participant:
            logger.warning(
                f"User {self.user.username} denied access to conversation {self.conversation_id}"
            )
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info(
            f"WebSocket connection established for user {self.user.username} in conversation {self.conversation_id}"
        )

        await self.mark_messages_as_read()

    async def disconnect(self, close_code):
        logger.info(
            f"WebSocket disconnecting with code {close_code} for conversation {getattr(self, 'conversation_id', 'unknown')}"
        )
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        try:
            logger.info(f"=== WEBSOCKET MESSAGE RECEIVED ===")
            logger.info(f"Raw data: {text_data}")
            logger.info(f"User: {self.user.username}")
            logger.info(f"Conversation: {self.conversation_id}")

            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type", "chat_message")
            logger.info(f"Message type: {message_type}")

            if message_type == "chat_message":
                message_content = text_data_json.get("message", "").strip()
                logger.info(f"Processing chat message: '{message_content}'")

                if message_content:
                    # Save message to database
                    message = await self.save_message(message_content)
                    if message:
                        logger.info(
                            f"Message saved to database with ID: {message['id']}"
                        )

                        # Send message to room group
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                "type": "chat_message",
                                "message": message_content,
                                "username": self.user.username,
                                "user_id": self.user.id,
                                "user_avatar": (
                                    self.user.img.url if self.user.img else ""
                                ),
                                "timestamp": message["timestamp"],
                                "message_id": str(message["id"]),
                            },
                        )
                        logger.info(
                            f"Message broadcasted to room group: {self.room_group_name}"
                        )
                    else:
                        logger.error(f"Failed to save message to database")
                else:
                    logger.warning(f"Empty message content received")

            elif message_type == "typing":
                logger.info(f"Processing typing indicator from {self.user.username}")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "typing_indicator",
                        "username": self.user.username,
                        "user_id": self.user.id,
                        "is_typing": text_data_json.get("is_typing", False),
                    },
                )
            else:
                logger.warning(f"Unknown message type received: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}. Raw data: {text_data}")
            await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
        except Exception as e:
            logger.error(f"Unexpected error in receive: {e}", exc_info=True)
            await self.send(text_data=json.dumps({"error": "Server error"}))

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": event["message"],
                    "username": event["username"],
                    "user_id": event["user_id"],
                    "user_avatar": event["user_avatar"],
                    "timestamp": event["timestamp"],
                    "message_id": event["message_id"],
                }
            )
        )

    async def typing_indicator(self, event):
        if event["user_id"] != self.user.id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "typing",
                        "username": event["username"],
                        "user_id": event["user_id"],
                        "is_typing": event["is_typing"],
                    }
                )
            )

    @database_sync_to_async
    def check_conversation_access(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        try:
            logger.info(
                f"Attempting to save message to conversation {self.conversation_id}"
            )
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation, sender=self.user, content=content
            )

            conversation.updated_at = timezone.now()
            conversation.save()
            logger.info(f"Message saved successfully with ID {message.id}")
            return {
                "id": message.id,
                "timestamp": message.timestamp.strftime("%H:%M"),
            }
        except Conversation.DoesNotExist:
            logger.error(f"Conversation {self.conversation_id} does not exist")
            return None
        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)

    @database_sync_to_async
    def mark_messages_as_read(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            Message.objects.filter(conversation=conversation).exclude(
                sender=self.user
            ).update(read=True)
        except Conversation.DoesNotExist:
            pass
