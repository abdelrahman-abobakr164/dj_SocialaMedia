from django.urls import path, include

websocket_urlpatterns = [
    path("ws/", include("notifications.routing.websocket_urlpatterns")),
    path("ws/", include("conversation.routing.websocket_urlpatterns")),
]