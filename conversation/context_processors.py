from .models import *
from django.db.models import (
    Prefetch,
    Max,
    Count,
    Q,
    When,
    Case,
    Value,
    IntegerField,
    BooleanField,
)


def conversations_count(request):
    if "superuser" in request.path:
        return {}
    else:
        if request.user.is_authenticated:
            inbox = (
                Message.objects.annotate(
                    is_unread_for_user=Case(
                        When(
                            conversation__is_group=True, then=~Q(read_by=request.user)
                        ),
                        When(conversation__is_group=False, then=Q(read=False)),
                        default=Value(False),
                        output_field=BooleanField(),
                    )
                )
                .filter(~Q(sender=request.user), is_unread_for_user=True)
                .exclude(conversation__conversation_status__status="Block")
            )

            block_chats = UserStatus.objects.filter(
                status="Block",
                user=request.user,
                conversation__participants=request.user,
            )

            UserMessages = Message.objects.filter(
                conversation__participants=request.user
            ).select_related("sender")

            UserChats = (
                Conversation.objects.prefetch_related(
                    Prefetch("messages", queryset=UserMessages)
                )
                .filter(participants=request.user)
                .annotate(
                    latest_message=Max("messages__timestamp"),
                    unread_count=Case(
                        When(
                            is_group=True,
                            then=Count(
                                "messages",
                                filter=~Q(messages__sender=request.user)
                                & ~Q(messages__read_by=request.user),
                                distinct=True,
                            ),
                        ),
                        When(
                            is_group=False,
                            then=Count(
                                "messages",
                                filter=~Q(messages__sender=request.user)
                                & Q(messages__read=False),
                                distinct=True,
                            ),
                        ),
                        default=Value(0),
                        output_field=IntegerField(),
                    ),
                )
                .order_by("-latest_message")
                .distinct(),
            )

            return {
                "UserChats": UserChats,
                "inbox": inbox,
                "block_chats": block_chats,
            }
        else:
            return {}
