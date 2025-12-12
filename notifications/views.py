from notifications.utils import filter_notifications_by_date_range
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from notifications.models import Notification


@login_required
def alerts(request):
    notifications = (
        Notification.objects.filter(recipient=request.user)
        .select_related("actor", "content_type")
        .prefetch_related("content_object")
        .order_by("read")
    )
    today_notifs = filter_notifications_by_date_range(
        notifications, request.GET.get("date_filter")
    )

    return render(
        request, "notifications/notifications.html", {"today_notifs": today_notifs}
    )


@login_required
def mark_as_read(request, id):
    url = request.META.get("HTTP_REFERER")
    notification = get_object_or_404(Notification, id=id, read=False)
    notification.read = True
    notification.save()
    return redirect(url)


@login_required
def mark_all_as_read(request):
    url = request.META.get("HTTP_REFERER")
    notifications = Notification.objects.filter(
        recipient=request.user, read=False
    ).order_by("-created_at")[:5]

    Notification.objects.filter(
        id__in=notifications, recipient=request.user, read=False
    ).update(read=True)

    return redirect(url)


@login_required
def delete_all(request):
    Notification.objects.filter(recipient=request.user).delete()
    return redirect("notifications")
