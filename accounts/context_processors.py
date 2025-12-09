from accounts.utils import generate_follow_suggestions
from accounts.models import Follow
from notifications.models import Notification


def follow_suggestions(request):
    if "superuser" in request.path:
        return {}
    else:
        if request.user.is_authenticated:
            friends = Follow.objects.filter(
                following=request.user, status=Follow.Status.PENDING
            )
            users = generate_follow_suggestions(request.user)
            alerts = (
                Notification.objects.filter(recipient=request.user, read=False)
                .select_related("actor", "content_type")
                .prefetch_related("content_object")
            )

            return {
                "users": users,
                "alerts": alerts,
                "friends": friends,
            }
        else:
            return {}
