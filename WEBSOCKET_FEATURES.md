# WebSocket Features Implementation

This document describes the WebSocket features implemented for real-time notifications and chat functionality in the social media platform.

## Features Implemented

### 1. Real-Time Notifications
- **Browser notifications** with permission handling
- **In-app toast notifications** using Bootstrap components
- **Unread notification counter** with live updates
- **Notification badges** in the navigation
- **Auto-reconnection** on connection loss
- **Mark as read** functionality via WebSocket

### 2. Real-Time Chat
- **Instant message delivery** without page refresh
- **Typing indicators** showing when users are typing
- **Message delivery confirmation** with read status
- **Auto-scroll to bottom** with manual scroll override
- **User authentication** and conversation access control
- **Database integration** for persistent messaging

### 3. WebSocket Infrastructure
- **Django Channels** integration with ASGI
- **Channel layers** for message broadcasting
- **Authentication middleware** for secure connections
- **Connection management** with heartbeat and reconnection
- **Error handling** and graceful fallbacks

## Technical Implementation

### Backend Components

#### 1. WebSocket Consumers

**NotificationConsumer** (`notifications/consumers.py`)
- Handles user-specific notification channels
- Manages unread count updates
- Processes mark-as-read requests
- Sends real-time notifications to connected users

**ChatConsumer** (`conversation/consumers.py`)
- Manages chat room connections
- Handles message sending and receiving
- Implements typing indicators
- Provides conversation access control
- Integrates with database for message persistence

#### 2. Channel Routing

**Main Routing** (`social_media/routing.py`)
```python
websocket_urlpatterns = [
    path("ws/", include("notifications.routing.websocket_urlpatterns")),
    path("ws/", include("conversation.routing.websocket_urlpatterns")),
]
```

**Notification Routing** (`notifications/routing.py`)
```python
websocket_urlpatterns = [
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
]
```

**Chat Routing** (`conversation/routing.py`)
```python
websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<conversation_id>[\w-]+)/$", consumers.ChatConsumer.as_asgi()),
]
```

#### 3. Settings Configuration

**Channel Layers** (added to `settings.py`)
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",  # Development
        # For production, use Redis:
        # "BACKEND": "channels_redis.core.RedisChannelLayer",
        # "CONFIG": {
        #     "hosts": [("127.0.0.1", 6379)],
        # },
    },
}
```

#### 4. Utility Functions

**Notification Utils** (`notifications/utils.py`)
- `send_notification()` - Creates and broadcasts notifications
- `send_real_time_message()` - Broadcasts chat messages
- `generate_notification_message()` - Creates human-readable messages
- `update_unread_count()` - Updates notification counters

#### 5. Enhanced Signals

**Updated Signals** (`notifications/signals.py`)
- Integrated with WebSocket broadcasting
- Added extra data for better user experience
- Improved notification content and context

### Frontend Components

#### 1. Global Notification Manager

**WebSocket Notifications** (`static/js/websocket-notifications.js`)
- `NotificationManager` class for global notification handling
- Browser notification API integration
- Toast notification system
- Connection management and auto-reconnection
- Unread count updates and page title modifications

#### 2. Chat Interface

**Enhanced Chat Template** (`templates/conversation/chat.html`)
- Real-time message display
- Typing indicator UI
- Auto-scroll functionality
- WebSocket connection management
- Message sending and receiving

## WebSocket URLs

### Notification WebSocket
```
ws://localhost:8000/ws/notifications/
```
- User-specific notification channel
- Requires authentication
- Handles notification broadcasting and read status

### Chat WebSocket
```
ws://localhost:8000/ws/chat/{conversation_id}/
```
- Conversation-specific chat channel
- Requires authentication and conversation membership
- Handles real-time messaging and typing indicators

## Message Formats

### Notification Messages

**Incoming Notification:**
```json
{
    "type": "notification",
    "id": "notification-id",
    "message": "John liked your post",
    "notification_type": "Like",
    "actor": {
        "id": 1,
        "username": "john",
        "avatar": "/media/avatars/john.jpg"
    },
    "timestamp": "2024-01-01 12:00:00",
    "read": false,
    "data": {
        "action_url": "/post/123/",
        "content_type": "post"
    }
}
```

**Unread Count Update:**
```json
{
    "type": "unread_count",
    "count": 5
}
```

**Mark as Read:**
```json
{
    "type": "mark_read",
    "notification_id": "notification-id"
}
```

### Chat Messages

**Outgoing Message:**
```json
{
    "type": "chat_message",
    "message": "Hello, how are you?"
}
```

**Incoming Message:**
```json
{
    "type": "chat_message",
    "message": "Hello, how are you?",
    "username": "john",
    "user_id": 1,
    "user_avatar": "/media/avatars/john.jpg",
    "timestamp": "12:34",
    "message_id": "message-uuid",
    "is_verified": true,
    "is_admin": false
}
```

**Typing Indicator:**
```json
{
    "type": "typing",
    "is_typing": true
}
```

## Usage Examples

### Testing Notifications

Use the management command to test notifications:

```bash
python manage.py test_notifications --from-user sender --to-user recipient --type Like
```

### Frontend Integration

The notification system is automatically loaded in the base template and works globally across the site. No additional setup is required for basic functionality.

### Chat Integration

Chat functionality is automatically enabled in conversation templates. The WebSocket connection is established when users visit a chat page.

## Browser Support

- **WebSocket API**: Modern browsers (IE 10+, Chrome, Firefox, Safari)
- **Notification API**: Chrome, Firefox, Safari (requires user permission)
- **ES6 Features**: Modern browsers (IE 11+ with polyfills)

## Security Features

- **Authentication Required**: All WebSocket connections require user authentication
- **Conversation Access Control**: Users can only join conversations they're part of
- **Origin Validation**: WebSocket connections validate allowed hosts
- **Input Sanitization**: All user input is properly escaped and validated

## Performance Considerations

- **Channel Layers**: In-memory for development, Redis recommended for production
- **Connection Limits**: Monitor concurrent WebSocket connections
- **Message Broadcasting**: Efficient group-based message distribution
- **Auto-reconnection**: Prevents connection loss issues

## Deployment Notes

### For Production:

1. **Install Redis** for channel layers:
```bash
pip install channels-redis
```

2. **Update settings** to use Redis:
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

3. **Use ASGI server** (e.g., Daphne, Uvicorn):
```bash
daphne -b 0.0.0.0 -p 8000 social_media.asgi:application
```

4. **Configure reverse proxy** (Nginx) for WebSocket support:
```nginx
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Future Enhancements

- **Online/Offline Status**: User presence indicators
- **Voice Messages**: Audio message support in chat
- **File Sharing**: Real-time file upload progress
- **Message Reactions**: Emoji reactions to messages
- **Message Threading**: Reply to specific messages
- **Push Notifications**: Mobile push notification integration
- **Group Chat**: Enhanced group conversation features
- **Message Search**: Real-time message search functionality