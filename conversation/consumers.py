import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message
import uuid

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """Enhanced consumer for chat room functionality with database integration"""

    async def connect(self):
        # Get conversation ID from URL
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        
        # Check if user is authenticated
        if self.scope["user"].is_anonymous:
            await self.close()
            return
        
        self.user = self.scope["user"]
        
        # Verify user is participant in this conversation
        is_participant = await self.check_conversation_access()
        if not is_participant:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Mark messages as read when user connects
        await self.mark_messages_as_read()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type", "chat_message")
            
            if message_type == "chat_message":
                message_content = text_data_json.get("message", "").strip()
                
                if message_content:
                    # Save message to database
                    message = await self.save_message(message_content)
                    
                    # Send message to room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "chat_message",
                            "message": message_content,
                            "username": self.user.username,
                            "user_id": self.user.id,
                            "user_avatar": self.user.img.url if self.user.img else "",
                            "timestamp": message["timestamp"],
                            "message_id": str(message["id"]),
                            "is_verified": self.user.verified if hasattr(self.user, 'verified') else False,
                            "is_admin": self.user.is_admin if hasattr(self.user, 'is_admin') else False,
                        }
                    )
            
            elif message_type == "typing":
                # Handle typing indicators
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "typing_indicator",
                        "username": self.user.username,
                        "user_id": self.user.id,
                        "is_typing": text_data_json.get("is_typing", False)
                    }
                )
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON"
            }))

    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": event["message"],
            "username": event["username"],
            "user_id": event["user_id"],
            "user_avatar": event["user_avatar"],
            "timestamp": event["timestamp"],
            "message_id": event["message_id"],
            "is_verified": event["is_verified"],
            "is_admin": event["is_admin"],
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator back to the person typing
        if event["user_id"] != self.user.id:
            await self.send(text_data=json.dumps({
                "type": "typing",
                "username": event["username"],
                "user_id": event["user_id"],
                "is_typing": event["is_typing"]
            }))

    @database_sync_to_async
    def check_conversation_access(self):
        """Check if user has access to this conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            
            # Update conversation's updated_at field
            conversation.save()
            
            return {
                "id": message.id,
                "timestamp": message.timestamp.strftime("%H:%M"),
            }
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark all messages in this conversation as read for current user"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            Message.objects.filter(
                conversation=conversation
            ).exclude(sender=self.user).update(read=True)
        except Conversation.DoesNotExist:
            pass
