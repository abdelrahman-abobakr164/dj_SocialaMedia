from django.urls import path, include
from conversation.routing import websocket_urlpatterns as conversation_patterns

# WebSocket URL patterns for chat only
websocket_urlpatterns = conversation_patterns