from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch
from django.views.generic import View
from django.contrib import messages
from django.db import transaction

from core.decorators import owner_ship_required
from core.validations import file_validation
from accounts.models import Follow
from story.models import *
from core.models import *
from core.forms import *

User = get_user_model()


@login_required
def events(request):
    url = request.META.get("HTTP_REFERER")
    events = Event.objects.filter(
        Q(city=request.user.city) | Q(user=request.user)
    ).prefetch_related("user")

    if s := request.GET.get("s"):
        events = Event.objects.filter(Q(title__icontains=s)).prefetch_related("user")

    if request.method == "POST":
        profile_id = request.POST.get("profile_id")
        event_id = request.POST.get("event_id")
        if profile_id and event_id:
            event = get_object_or_404(Event, pk=event_id)
            user = get_object_or_404(User, pk=profile_id)

            if user in event.user.all():
                event.user.remove(user)
            else:
                event.user.add(user)
            event.save()
            return redirect(url)

    return render(request, "core/events.html", {"events": events})


@login_required
def profile_event(request, slug):
    user = get_object_or_404(User, slug=slug)
    can_view = user.show_events or request.user == user

    events = (
        Event.objects.filter(user=user).prefetch_related("user") if can_view else None
    )

    if s := request.GET.get("q"):
        events = events.filter(Q(title__icontains=s) | Q(place__icontains=s))

    return render(
        request, "core/profile_event.html", {"events": events, "profile": user}
    )


@login_required
def search(request):
    if username := request.GET.get("username"):
        users = User.objects.filter(username__icontains=username).exclude(
            username=request.user.username
        )

        for user in users:
            if users.exists():
                follow_status = Follow.objects.filter(
                    follower=request.user,
                    following=user,
                ).first()

                if follow_status:
                    btn = (
                        "UnFollow" if follow_status.status == "accepted" else "Pending"
                    )
                else:
                    btn = "Follow"

    context = {
        "usernames": users,
        "name": username,
        "btn": btn,
    }
    return render(request, "core/search.html", context)


@login_required
def home(request):
    events = Event.objects.filter(user=request.user)
    followers_post = Follow.objects.filter(
        follower=request.user, status=Follow.Status.ACCEPTED
    ).values_list("following", flat=True)

    posts = (
        Post.objects.select_related("user")
        .prefetch_related(
            "media",
            Prefetch(
                "comments",
                queryset=Comment.objects.filter(parent=None).select_related(
                    "user", "parent"
                ),
                to_attr="none_parent_comment",
            ),
        )
        .filter(
            Q(user__in=followers_post) | Q(user__verified=True) | Q(user=request.user)
        )
        .order_by("-like_count", "-created_at")
    )

    context = {
        "posts": posts,
        "events": events,
        "form": PostForm(),
        "commentform": CommentForm(),
    }
    return render(request, "core/index.html", context)


class PostDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        post = (
            Post.objects.select_related("user").prefetch_related("comments").get(id=pk)
        )
        comments = (
            Comment.objects.filter(post=post, parent=None)
            .select_related("user", "parent")
            .order_by("-like_count", "-created_at")
        )
        form = CommentForm()
        return render(
            request,
            "core/post-detail.html",
            {"post": post, "form": form, "comments": comments},
        )


@login_required
@owner_ship_required(Post, pk_kwarg="pk", user="user")
def post_update(request, pk):
    post_obj = (
        Post.objects.select_related("user")
        .prefetch_related("media", "comments")
        .get(pk=pk, user=request.user)
    )
    comments = (
        Comment.objects.filter(
            post=post_obj,
            parent=None,
        )
        .select_related("user", "parent")
        .order_by("-like_count", "-created_at")
    )

    if request.method == "POST":
        return upload(request, post_obj.id)

    context = {
        "post": post_obj,
        "form": CommentForm(),
        "comments": comments,
    }
    return render(request, "core/post-update.html", context)


@login_required
@require_POST
def upload(request, pk=None):
    url = request.META.get("HTTP_REFERER")

    files = request.FILES.getlist("files")
    tag = request.POST.get("tags")

    with transaction.atomic():
        post_obj, _ = Post.objects.get_or_create(pk=pk, defaults={"user": request.user})

        if files:

            if pk:
                post_obj.media.all().delete()

            for file in files:
                if file_validation(file):
                    PostMedia.objects.create(
                        post=post_obj,
                        file=file,
                        content_type=file.content_type.split("/")[0],
                    )

            post_obj.caption = request.POST.get("caption")

        else:
            post_obj.body = request.POST["body"]

        if tag:
            tag, _ = Tag.objects.get_or_create(name=tag)
            post_obj.tag.add(tag)

        post_obj.save()

    return redirect(url)


@login_required
@owner_ship_required(Post, pk_kwarg="id", user="user")
def post_delete(request, id):
    post = get_object_or_404(Post, id=id)
    post.delete()
    return redirect("/")


@login_required
@require_POST
def create_comment(request):
    url = request.META.get("HTTP_REFERER")
    form = CommentForm(request.POST)
    post_id = request.POST.get("post_id")
    parent = request.POST.get("parent")
    comment = request.POST.get("comment")

    if not form.is_valid():
        messages.error(request, "this field is required")

    comment = Comment.objects.create(
        user=request.user,
        post=Post.objects.get(id=post_id),
        comment=comment,
    )

    if parent:
        parent_comment = Comment.objects.get(id=parent)
        comment.parent = parent_comment
        comment.save()

        return redirect(url)


@login_required
@owner_ship_required(Comment, pk_kwarg="id", user="user")
def comment_update(request, id):
    comment = get_object_or_404(Comment, id=id)
    if request.method == "POST":
        message = request.POST.get("comment")
        if not message:
            messages.error(request, "Comment Field Required")

        comment.comment = message
        comment.save()
        return redirect("comment-update", id)

    return render(request, "core/comment-update.html", {"comment": comment})


@login_required
@owner_ship_required(Comment, pk_kwarg="id", user="user")
def delete_comment(request, id):
    comment = get_object_or_404(Comment, id=id)
    comment.delete()
    return redirect("post-detail", pk=comment.post.id)


@login_required
def like(request, content_type_id, object_id):
    url = request.META.get("HTTP_REFERER")
    content_type = get_object_or_404(ContentType, id=content_type_id)
    model_class = content_type.model_class()

    if model_class not in (Post, Comment):
        messages.error(request, "Invalid Content Type")
        return redirect(url)

    like, created = Like.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=object_id,
    )
    if not created:
        like.delete()

    return redirect(url)


def handler_404(request, exception):
    return render(request, "404.html", status=404)


def handler_500(request):
    return render(request, "500.html", status=500)
