from django.urls import path
from . import views

urlpatterns = [
    path("settings/", views.settings, name="settings"),
    path("pending-requests/", views.pending_requests, name="pending-requests"),
    path("suggestions/", views.follow_suggestions, name="suggestions"),
    path("contact-us/", views.contact_us, name="contact-us"),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),
    path(
        "create_checkout_session/<uuid:user_id>/",
        views.create_checkout_session,
        name="create_checkout_session",
    ),
    path("viewers-list/<str:slug>/", views.viewers_list, name="viewers-list"),
    path("followers/<str:slug>/", views.user_followers, name="followers"),
    path("following/<str:slug>/", views.user_following, name="following"),
    path("send_follow/<uuid:id>/", views.send_follow, name="send_follow"),
    path(
        "respond_to_follow/<str:id>/<str:action>/",
        views.respond_to_follow,
        name="respond_to_follow",
    ),
    path("cancel_request/<uuid:id>/", views.cancel_request, name="cancel_request"),
    path("unfollow/<uuid:id>/", views.user_unfollow, name="unfollow"),
    path("remove/<uuid:id>/", views.remove, name="remove"),
    path("<str:slug>/videos/", views.videos, name="videos"),
    path("<str:slug>/", views.profile, name="profile"),
]
