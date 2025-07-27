from django.urls import path
from . import views


urlpatterns = [
    path("", views.alerts, name="notifications"),
    path("mark_as_read/<int:id>", views.mark_as_read, name="delete-notification"),
    path("mark_all_as_read/", views.mark_all_as_read, name="mark_all_as_read"),
    path("delete-all-notifications/", views.delete_all, name="delete-all"),
]
