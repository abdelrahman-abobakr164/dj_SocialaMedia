from .models import *
from django.db.models import Q, Prefetch, Count, Max


def conversations_count(request):
    if request.user.is_authenticated:
        inbox = Message.objects.filter(
            ~Q(sender=request.user),
            read=False,
        ).exclude(
            conversation__conversation_status__status="Block",
        )

        block_chats = UserStatus.objects.filter(
            status="Block", user=request.user, conversation__participants=request.user
        )

        UserMessages = Message.objects.filter(conversation__participants=request.user)

        UserChats = (
            Conversation.objects.prefetch_related(
                Prefetch("messages", queryset=UserMessages, to_attr="UserMessages")
            )
            .filter(participants=request.user)
            .annotate(
                latest_message=Max("messages__timestamp"),
                unread_count=Count(
                    "messages",
                    filter=Q(messages__read=False) & ~Q(messages__sender=request.user),
                ),
            )
            .order_by("-latest_message")
            .distinct()
        )

        return {
            "UserChats": UserChats,
            "inbox": inbox,
            "block_chats": block_chats,
        }
    else:
        return {}
