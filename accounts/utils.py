from django.contrib.auth import get_user_model
from django.db.models import Count
from collections import Counter
from .models import Follow


User = get_user_model()


def generate_follow_suggestions(user, max_results=5):
    suggestions = []

    UIfollowing = (
        Follow.objects.filter(follower=user, status="accepted")
        .values_list("following", flat=True)
        .exclude(following=user)
    )

    if UIfollowing.exists():
        FriendsOfUsers = (
            Follow.objects.filter(follower__in=UIfollowing, status="accepted")
            .values_list("following", flat=True)
            .exclude(following=user)
        )

        if FriendsOfUsers.exists():
            counter = Counter(FriendsOfUsers)
            top_suggestions = [
                user_id for user_id, count in counter.most_common(max_results)
            ]
            suggestions.extend(top_suggestions)

        if len(suggestions) < max_results:
            remaining = max_results - len(suggestions)
            popular_user = (
                User.objects.filter(id__in=UIfollowing)
                .annotate(follower_count=Count("followers"))
                .order_by("-follower_count")
                .exclude(id=user.id)[:remaining]
                
            )
            suggestions.extend(popular_user.values_list("id", flat=True))

    if len(suggestions) < max_results:
        remaining = max_results - len(suggestions)
        popular_users = (
            User.objects.exclude(id=user.id)
            .annotate(high_followers=Count("followers"))
            .order_by("-high_followers")[:remaining]
        )
        suggestions.extend(popular_users.values_list("id", flat=True))

    return User.objects.filter(id__in=suggestions).exclude(id__in=UIfollowing)
