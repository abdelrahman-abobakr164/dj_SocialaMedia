from django.urls import path
from . import views

app_name = "story"

urlpatterns = [
    path("", views.story_list, name="story_list"),
    path("create/", views.create_story, name="create_story"),
    path("view/<uuid:story_id>/", views.view_story, name="view_story"),
    path("delete/<uuid:story_id>/", views.delete_story, name="delete_story"),
    path("viewers/<uuid:story_id>/", views.story_viewers, name="story_viewers"),
]
