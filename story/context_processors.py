from django.utils import timezone
from accounts.models import Follow
from .models import Story, StoryView
from django.db.models import Q, Exists, OuterRef


def user_stories(request):
    if "superuser" in request.path:
        return {}
    else:
        if request.user.is_authenticated:
            now = timezone.now()

            following_ids = Follow.objects.filter(
                follower=request.user, status=Follow.Status.ACCEPTED
            ).values_list("following_id", flat=True)

            stories = (
                Story.objects.filter(
                    Q(user__in=following_ids) | Q(user=request.user), expires_at__gt=now
                )
                .select_related("user")
                .order_by("user", "-created_at")
            )

            is_viewed = StoryView.objects.filter(
                story=OuterRef("pk"), viewer=request.user
            )

            stories = stories.annotate(is_viewed=Exists(is_viewed)).order_by(
                "is_viewed", "-created_at"
            )

            user_stories = {}
            for story in stories:
                if story.user not in user_stories:
                    user_stories[story.user] = []
                user_stories[story.user].append(story)

            return {"user_stories": user_stories}

        else:
            return {}
