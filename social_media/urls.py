from django.conf.urls import handler404, handler500
from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
from django.contrib import admin

from django.http import HttpResponse


urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path("boda/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("accounts.urls")),
    path("notifications/", include("notifications.urls")),
    path("conversations/", include("conversation.urls")),
    path("story/", include("story.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = "core.views.handler_404"
handler500 = "core.views.handler_500"
