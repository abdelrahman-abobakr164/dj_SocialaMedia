from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Prefetch, Count, Max, Case, When
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import transaction

from accounts.models import Follow
from core.validations import *

from conversation.utils import message_handler
from conversation.forms import CreateForm
from conversation.models import *


def only_admin(user, conversation):
    return (
        conversation.admin.count() == 1
        and conversation.admin.filter(id=user.id).exists()
    )


def get_connection_ids(user, conversation=None):
    accepted = Follow.objects.filter(status=Follow.Status.ACCEPTED)

    followers = accepted.filter(following=user).values("follower_id")
    followings = accepted.filter(follower=user).values("following_id")

    condition = Q(pk__in=followers) | Q(pk__in=followings)

    if conversation:
        condition |= Q(pk__in=conversation.participants.values("pk"))

    return get_user_model().objects.filter(condition).exclude(pk=user.pk)


@login_required
def group(request, pk=None):
    conversation = None

    if pk:
        conversation = get_object_or_404(
            Conversation.objects.prefetch_related("admin", "participants"), pk=pk
        )

        if not conversation.admin.filter(pk=request.user.pk).exists():
            messages.warning(request, "You're not an admin of this group.")
            return redirect("conversations")

    candidates = get_connection_ids(request.user, conversation)

    instance = conversation or Conversation(is_group=True)

    if request.method == "POST":
        form = CreateForm(
            request.POST, request.FILES, instance=instance, candidates=candidates
        )

        with transaction.atomic():
            if form.is_valid():
                saved = form.save()
                saved.participants.add(request.user)
                saved.admin.add(request.user)

                messages.success(
                    request,
                    f"{form.cleaned_data['group_name']} has been "
                    f"{'created' if pk is None else 'updated'} successfully!",
                )
                return redirect("conversations")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = CreateForm(instance=instance, candidates=candidates)

    context = {
        "users": candidates,
        "form": form,
        "conversation": conversation,
        "pk": pk,
    }
    return render(request, "conversation/group.html", context)


@login_required
def leave(request, pk):
    group = get_object_or_404(Conversation, pk=pk)

    if only_admin(request.user, group):
        group.delete()

    if group.is_group and request.user in group.participants.all():
        group.participants.remove(request.user)
        group.admin.remove(request.user)
        group.save()

    return redirect("conversations")


@login_required
def delete_group(request, pk):
    group = get_object_or_404(Conversation, pk=pk)
    if group.is_group and request.user in group.admin.all():
        group.delete()
        return redirect("conversations")


@login_required
def conversations(request):
    messages_filter = Message.objects.filter(conversation__participants=request.user)

    Convs = (
        Conversation.objects.prefetch_related(
            Prefetch("messages", queryset=messages_filter, to_attr="messages_filter")
        )
        .filter(participants=request.user)
        .annotate(
            latest_message=Max("messages__timestamp"),
            unread_count=Case(
                When(
                    is_group=False,
                    then=Count(
                        "messages",
                        filter=Q(messages__read=False)
                        & ~Q(messages__sender=request.user),
                        distinct=True,
                    ),
                ),
                When(
                    is_group=True,
                    then=Count(
                        "messages",
                        filter=~Q(messages__sender=request.user)
                        & ~Q(messages__read_by=request.user),
                        distinct=True,
                    ),
                ),
            ),
        )
        .exclude(
            conversation_status__user=request.user,
            conversation_status__status="Block",
        )
        .order_by("-latest_message")
        .distinct()
    )

    if request.method == "POST":
        conversation = get_object_or_404(
            Conversation, id=request.POST.get("convid"), participants=request.user
        )
        block_action(request.user, conversation)
        return redirect("conversations")

    return render(request, "conversation/conversations.html", {"Convs": Convs})


@login_required
def chat_room(request, pk):
    chat = get_object_or_404(
        Conversation.objects.prefetch_related("participants"), pk=pk
    )

    if request.user not in chat.participants.all():
        return redirect("conversations")

    other_user = chat.other_participants(request.user)

    chat.mark_as_read_by(request.user)

    follow_exists = Follow.objects.filter(
        Q(follower=request.user, following=other_user)
        | Q(following=request.user, follower=other_user),
        status=Follow.Status.ACCEPTED,
    ).exists()

    is_blocked = UserStatus.objects.filter(conversation=chat, status="Block").exists()

    if is_blocked or not follow_exists:
        CheckUserStatus = True
        messages.warning(request, "You Can't Message This User")

    else:
        CheckUserStatus = False

    msgs = (
        Message.objects.select_related("conversation", "sender")
        .filter(conversation=chat)
        .order_by("timestamp")
    )

    if request.method == "POST":
        if not is_blocked and follow_exists:
            create_message(request, chat)

    context = {"chat": chat, "msgs": msgs, "CheckUserStatus": CheckUserStatus}
    return render(request, "conversation/chat.html", context)


def create_message(request, chat):
    url = request.META.get("HTTP_REFERER")

    files = request.FILES.getlist("attachment")
    content = request.POST.get("content", "").strip()

    if not files and not content:
        messages.error(request, "content and file/s are required")
        return redirect(url)

    try:
        validated = [(file, file_validation(file)) for file in files]
    except ValidationError as e:
        messages.error(request, " ".join(e.messages))
        return redirect(url)

    with transaction.atomic():
        message = Message.objects.create(
            conversation=chat,
            content=content,
            sender=request.user,
        )
        for file, file_type in validated:
            MessageAttachment.objects.create(
                file=file,
                message=message,
                file_name=file.name,
                file_type=file_type,
            )

        transaction.on_commit(lambda: message_handler(message))
        chat.save()
    return redirect(url)


@login_required
def delete_chat(request, pk):
    Message.objects.get(id=pk).delete()
    return redirect(request.META.get("HTTP_REFERER"))


@login_required
def block_page(request):
    blocked_conversations = Conversation.objects.filter(
        participants=request.user,
        conversation_status__user=request.user,
        conversation_status__status="Block",
    ).prefetch_related("participants", "messages")

    if request.method == "POST":
        conversation = get_object_or_404(
            Conversation, id=request.POST.get("convid"), participants=request.user
        )
        block_action(request.user, conversation)
        return redirect("block")

    context = {
        "Convs": blocked_conversations,
    }
    return render(request, "conversation/block.html", context)


def block_action(user, conversation):
    with transaction.atomic():
        if not conversation.is_group:
            status_obj, created = UserStatus.objects.get_or_create(
                user=user,
                conversation=conversation,
                defaults={"status": "Block"},
            )

            if not created:
                status_obj.delete()

        elif only_admin(user, conversation):
            conversation.delete()
        else:
            conversation.admin.remove(user)
            conversation.participants.remove(user)
