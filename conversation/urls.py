from django.urls import path
from . import views

urlpatterns = [
    path("", views.conversations, name="conversations"),
    path("group", views.group, name="group"),
    path("block-chats", views.block, name="block"),
    path("<uuid:pk>/", views.chat_room, name="conversation"),
    path("delete/<uuid:pk>/", views.delete_chat, name="delete-chat"),
]
