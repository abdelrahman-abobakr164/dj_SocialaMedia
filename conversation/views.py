from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Prefetch, Count, Max
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime

from django.contrib.auth import get_user_model
from conversation.forms import CreateForm
from accounts.models import Follow
from conversation.models import *

# Create your views here.


@login_required
def group(request):
    User = get_user_model()
    form = CreateForm()

    if request.method == "POST":
        create_form = CreateForm(request.POST)
        if create_form.is_valid():
            group_name = create_form.cleaned_data.get("group_name")
            group_image = request.FILES.get("group_image")
            participants = request.POST.getlist("participants")

            conversation = Conversation.objects.create(
                is_group=True, group_name=group_name
            )

            if group_image:
                image_extensions = group_image.name.split(".")[-1]
                if image_extensions in ["jpg", "png", "JPG", "PNG"]:
                    conversation.group_image = group_image
                    conversation.save()
                else:
                    messages.warning(request, "Invalid image format")
                    return redirect("group")

            conversation.participants.set(participants)
            conversation.participants.add(request.user)
            conversation.save()

            messages.success(request, "Group created successfully!")
            return redirect("group")
        else:
            messages.error(request, "Invalid form data")
            return redirect("group")

    else:
        following = Follow.objects.filter(
            Q(follower=request.user.id) | Q(following=request.user.id)
        )

        user_ids = set()
        for f in following:
            if f.follower_id != request.user.id:
                user_ids.add(f.follower_id)
            if f.following_id != request.user.id:
                user_ids.add(f.following_id)
        users = User.objects.filter(id__in=user_ids)

    return render(
        request, "conversation/create_group.html", {"users": users, "form": form}
    )


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
            conversation = Conversation.objects.get(id=convid)
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

    follow = Follow.objects.filter(
        Q(following=request.user) | Q(following=chat.other_participants(request.user)),
        Q(follower=chat.other_participants(request.user)) | Q(follower=request.user),
        status="accepted",
    ).exists()

    convstatus = UserStatus.objects.filter(conversation=chat, status="Block").exists()

    if convstatus:
        CheckUserStatus = True
        msgs = messages.warning(request, "This User In Block List")

    elif not follow:
        CheckUserStatus = True
        msgs = messages.warning(
            request, "This User Is No Longer Your Friend You Can't Chat With Him"
        )

    else:
        CheckUserStatus = False

    msgs = Message.objects.filter(conversation=chat).order_by("timestamp")
    Message.objects.filter(
        ~Q(sender=request.user),
        conversation=chat,
        read=False,
    ).update(read=True)

    if request.method == "POST":
        if not convstatus and follow:
            files = request.FILES.getlist("attachment")
            content = request.POST.get("content")

            if files or content:
                message = Message.objects.create(
                    conversation=chat,
                    content=content,
                    sender=request.user,
                )
                for file in files:
                    extensions = [
                        "mp4",
                        "mp3",
                        "jpg",
                        "JPG",
                        "png",
                        "PNG",
                        "GIF",
                        "pdf",
                    ]
                    file_read = file.read()
                    if file.name.split(".")[-1] in extensions:
                        if len(file_read) <= 1024 * 1024 * 10:
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
                        messages.warning(
                            request, f"The File Extension is not Supported"
                        )
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
