from django.urls import path
from . import views

urlpatterns = [
    path("", views.conversations, name="conversations"),
    path("group/", views.group, name="group"),
    path("block-chats", views.block, name="block"),
    path("leave-group/<uuid:pk>/", views.leave, name="leave"),
    path("delete-group/<uuid:pk>/", views.delete_group, name="delete-group"),
    path("group/<uuid:pk>/", views.group, name="edit_group"),
    path("delete/<uuid:pk>/", views.delete_chat, name="delete-chat"),
    path("<uuid:pk>/", views.chat_room, name="conversation"),
]
