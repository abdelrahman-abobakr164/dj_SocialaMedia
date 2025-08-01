from django.urls import path, include
from conversation.routing import websocket_urlpatterns as conversation_patterns
from notifications.routing import websocket_urlpatterns as notification_patterns

# Combine all WebSocket URL patterns
websocket_urlpatterns = conversation_patterns + notification_patterns