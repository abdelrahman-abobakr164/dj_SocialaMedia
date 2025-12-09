from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch, Count, Max
from django.contrib import messages
from datetime import datetime

from django.contrib.auth import get_user_model
from conversation.forms import CreateForm
from accounts.models import Follow
from conversation.models import *
from core.utils import *


@login_required
def group(request, pk=None):
    url = request.META.get("HTTP_REFERER")
    User = get_user_model()
    if pk:
        conversation = Conversation.objects.get(pk=pk)
        form = CreateForm(instance=conversation)
    else:
        conversation = None
        form = CreateForm()

    following = Follow.objects.filter(
        Q(follower=request.user.id, status=Follow.Status.ACCEPTED)
        | Q(following=request.user.id, status=Follow.Status.ACCEPTED)
    )

    user_ids = set()
    for f in following:
        if f.follower_id != request.user.id:
            user_ids.add(f.follower_id)
        if f.following_id != request.user.id:
            user_ids.add(f.following_id)

    if pk:
        for user in conversation.participants.all():
            if user.id != request.user.id:
                user_ids.add(user.id)
    users = User.objects.filter(id__in=user_ids)

    if request.user in conversation.admin.all() if pk else True:

        if request.method == "POST":
            create_form = CreateForm(request.POST, instance=conversation)
            participants = request.POST.getlist("participants")
            admins = request.POST.getlist("admins", [request.user])
            if create_form.is_valid():
                form_save = create_form.save(commit=False)
                form_save.is_group = True

                if not participants or participants == request.user.username:
                    messages.warning(request, "Please Select Participants")
                    return redirect(url)

                form_save.save()

                if pk == None:
                    conversation = Conversation.objects.get(
                        group_name=create_form.cleaned_data.get("group_name"),
                    )
                conversation.admin.set(admins) if pk else None
                conversation.admin.add(request.user)
                conversation.participants.set(participants + admins)
                conversation.participants.add(request.user)
                conversation.save()

                if "/conversations/group/" == request.path:
                    messages.success(request, "Group Created Successfully!")
                    return redirect("conversations")
                else:
                    messages.success(
                        request, "You'v been update Your Group Successfully!"
                    )
                return redirect(url)
            else:
                messages.error(request, f"Invalid form data ")
                return redirect(url)

    else:
        messages.warning(request, "You'r not admin to do this")
        return redirect(url)

    context = {
        "users": users,
        "form": form,
        "conversation": conversation,
        "pk": pk,
    }
    return render(request, "conversation/group.html", context)


@login_required
def leave(request, pk):
    group = get_object_or_404(Conversation, pk=pk)
    if group.is_group and request.user in group.participants.all():
        if request.user in group.admin.all():
            if request.user == group.admin.all():
                group.delete()
            else:
                group.admin.remove(request.user)
        group.participants.remove(request.user)
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
        .filter(
            participants=request.user,
        )
        .annotate(
            latest_message=Max("messages__timestamp"),
            unread_count=Count(
                "messages",
                filter=Q(messages__read=False) & ~Q(messages__sender=request.user),
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
        convid = request.POST.get("convid")
        if convid:
            conversation = get_object_or_404(Conversation, id=convid)

            if conversation.is_group:
                if request.user in conversation.participants.all():
                    if request.user == conversation.admin.first():
                        conversation.delete()
                    else:
                        (
                            conversation.admin.remove(request.user)
                            if request.user in conversation.admin.all()
                            else None
                        )
                        conversation.participants.remove(request.user)
                        conversation.save()
                    return redirect("conversations")

            ConvFilter = conversation.other_participants(request.user)
            if ConvFilter.is_superuser == False:

                UserStatus.objects.update_or_create(
                    user=request.user,
                    conversation=conversation,
                    defaults={"status": "Block"},
                )
            else:
                messages.warning(request, "You Can't Block This User")

            return redirect("conversations")

    return render(request, "conversation/conversations.html", {"Convs": Convs})


@login_required
def chat_room(request, pk):
    url = request.META.get("HTTP_REFERER")
    chat = get_object_or_404(Conversation, pk=pk)
    if request.user not in chat.participants.all():
        return redirect("conversations")

    other_user = chat.other_participants(request.user)
    print(other_user)
    mutual_follow_exists = Follow.objects.filter(
        Q(follower=request.user, following=other_user)
        | Q(following=request.user, follower=other_user),
        status=Follow.Status.ACCEPTED,
    )

    is_blocked = UserStatus.objects.filter(conversation=chat, status="Block").exists()

    if is_blocked:
        CheckUserStatus = True
        messages.warning(request, "This User In Block List")

    elif not mutual_follow_exists.exists():
        CheckUserStatus = True
        messages.warning(
            request, "This User Is No Longer Your Friend You Can't Chat With Him/her"
        )

    else:
        CheckUserStatus = False

    msgs = (
        Message.objects.select_related("conversation", "sender")
        .filter(conversation=chat)
        .order_by("timestamp")
    )
    Message.objects.filter(
        ~Q(sender=request.user),
        conversation=chat,
        read=False,
    ).update(read=True)

    if request.method == "POST":
        if not is_blocked and mutual_follow_exists:
            files = request.FILES.getlist("attachment")
            content = request.POST.get("content")

            if files or content:
                message = Message.objects.create(
                    conversation=chat,
                    content=content,
                    sender=request.user,
                )
                for file in files:
                    if file_validation(file):
                        if validate_file_size(file):
                            MessageAttachment.objects.create(
                                file=file,
                                message=message,
                                file_name=file.name,
                                file_type=file.content_type.split("/")[0],
                            )
                        else:
                            messages.warning(request, f"File size exceeds 10MB.")
                            message.delete()
                            return redirect(url)
                    else:
                        messages.warning(request, f"File Extension is not Supported")
                        message.delete()
                        return redirect(url)

            chat.updated_at = datetime.now()
            chat.save()
        return redirect(url)

    context = {"chat": chat, "msgs": msgs, "CheckUserStatus": CheckUserStatus}
    return render(request, "conversation/chat.html", context)


@login_required
def delete_chat(request, pk):
    Message.objects.get(id=pk).delete()
    return redirect(request.META.get("HTTP_REFERER"))


@login_required
def block(request):
    user_block_status = UserStatus.objects.filter(
        status="Block", user=request.user, conversation__participants=request.user
    )

    blocked_conversations = (
        Conversation.objects.prefetch_related(
            Prefetch(
                "conversation_status",
                queryset=user_block_status,
                to_attr="user_block_status",
            ),
        )
        .filter(
            conversation_status__user=request.user,
            conversation_status__status="Block",
            participants=request.user,
        )
        .order_by("-messages__timestamp")
        .distinct()
    )

    if request.method == "POST":
        convid = request.POST.get("convid")

        if convid:
            UserStatus.objects.get(user=request.user, conversation__id=convid).delete()
            return redirect(request.META.get("HTTP_REFERER"))

    context = {
        "Convs": blocked_conversations,
        "user_status": user_block_status,
    }
    return render(request, "conversation/block.html", context)
