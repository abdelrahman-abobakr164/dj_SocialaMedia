from django.urls import path
from . import views
from .views import PostDetailView

urlpatterns = [
    path("", views.home, name="index"),
    path("upload/", views.upload, name="upload"),
    path("search/", views.search, name="search"),
    path("events/", views.events, name="events"),
    path("create-comment/", views.create_comment, name="create-comment"),
    path("like/<int:content_type_id>/<uuid:object_id>/", views.like, name="like"),
    path("detail/<uuid:pk>/", PostDetailView.as_view(), name="post-detail"),
    path("update/<uuid:pk>/", views.post_update, name="post-update"),
    path("delete/<uuid:id>/", views.post_delete, name="post-delete"),
    path("comment/delete/<uuid:id>/", views.delete_comment, name="comment-delete"),
    path("comment/update/<uuid:id>/", views.comment_update, name="comment-update"),
    path("events/<str:slug>", views.profile_event, name="profile_event"),
]
