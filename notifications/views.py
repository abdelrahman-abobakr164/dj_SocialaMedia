from django.shortcuts import get_object_or_404, redirect, render
from notifications.utils import filter_notifications_by_date_range
from django.contrib.auth.decorators import login_required
from notifications.models import Notification
from django.db.models import Q


@login_required
def alerts(request):
    notifications = Notification.objects.filter(
        recipient=request.user, read=False
    ).select_related("actor")
    today_notifs = filter_notifications_by_date_range(
        notifications, request.GET.get("date_filter")
    )

    return render(
        request, "notifications/notifications.html", {"today_notifs": today_notifs}
    )


@login_required
def mark_as_read(request, id):
    url = request.META.get("HTTP_REFERER")
    get_object_or_404(Notification, id=id).delete()
    return redirect(url)


@login_required
def mark_all_as_read(request):
    url = request.META.get("HTTP_REFERER")
    notifications = Notification.objects.filter(
        recipient=request.user, read=False
    ).order_by("-created_at")[:5]

    # for noti in notifications:
    #     mark_as_read(request, noti.id)

    Notification.objects.filter(
        Q(id__in=notifications) & Q(recipient=request.user)
    ).update(read=True)

    return redirect(url)


@login_required
def delete_all(request):
    Notification.objects.filter(recipient=request.user, read=False).delete()
    return redirect("notifications")
