from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.utils import generate_follow_suggestions
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.db.models import Q, Prefetch
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from notifications.models import Notification
from accounts.models import Follow
from conversation.models import *
from accounts.forms import *
from core.models import *

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

User = get_user_model()


@csrf_exempt
def create_checkout_session(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": "Get Verified",
                            },
                            "unit_amount": 250,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=request.build_absolute_uri("/")
                + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=request.build_absolute_uri("/"),
                metadata={"user_id": user.id},
            )
            return JsonResponse({"id": session.id})
        except Exception as e:
            return HttpResponseBadRequest(str(e))
    return HttpResponseBadRequest("Invalid request")


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    webhook_secret = "whsec_71ciZDknZ6mBfYoAo1okqFWFt4Em17Ls"

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        user = User.objects.get(id=user_id)
        user.verified = True
        user.save()

    return HttpResponse(status=200)


@login_required
def videos(request, slug):
    user = get_object_or_404(User, slug=slug)
    if request.user == user or user.is_private == False:
        posts = (
            Post.objects.prefetch_related(
                Prefetch(
                    "media", queryset=PostMedia.objects.all(), to_attr="postattach"
                ),
                Prefetch(
                    "comments",
                    queryset=Comment.objects.filter(parent=None),
                    to_attr="none_parent_comment",
                ),
            )
            .order_by("-like_count", "-created_at")
            .filter(media__content_type="video")
            .filter(user=user)
        )

    else:
        posts = []
    return render(request, "accounts/videos.html", {"profile": user, "posts": posts})


@login_required
def profile(request, slug):
    user = get_object_or_404(User, slug=slug)
    conversation = (
        Conversation.objects.filter(Q(participants=user))
        .filter(Q(participants=request.user))
        .first()
    )

    if request.user != user and request.user.is_admin == False:
        user.viewers.add(request.user)

    if user.is_private == True or request.user == user:

        posts = (
            Post.objects.prefetch_related(
                Prefetch(
                    "comments",
                    queryset=Comment.objects.filter(parent=None),
                    to_attr="none_parent_comment",
                )
            )
            .filter(user=user)
            .order_by("-created_at")
        )

    else:
        posts = []

    is_following = Follow.objects.filter(
        follower=request.user, following=user, status=Follow.Status.ACCEPTED
    ).exists()

    is_follower = Follow.objects.filter(
        follower=user, following=request.user, status=Follow.Status.ACCEPTED
    ).exists()

    is_pending = Follow.objects.filter(
        follower=request.user, following=user, status=Follow.Status.PENDING
    ).exists()

    FollowingCount = Follow.objects.filter(
        follower=user, status=Follow.Status.ACCEPTED
    ).count()
    FollowersCount = Follow.objects.filter(
        following=user, status=Follow.Status.ACCEPTED
    ).count()

    context = {
        "profile": user,
        "posts": posts,
        "conversation": conversation,
        "is_following": is_following,
        "is_follower": is_follower,
        "is_pending": is_pending,
        "FollowingCount": FollowingCount,
        "FollowersCount": FollowersCount,
        "stripe_public_key": "pk_test_51Q3xnYH4IAM7G10vw0mAzfEqkajCpWH5PuIrYJziEdvBURYUnHzQXitK8ntYVdqoGknPH0fw9p8cHoErROxU1eGu00xRPC5XiA",
    }
    return render(request, "accounts/profile.html", context)


@login_required
def settings(request):
    user = get_object_or_404(User, username=request.user.username)
    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your Information Has Been Updated")
            return redirect("settings")
    else:
        form = UserForm(instance=user)
    return render(request, "accounts/settings.html", {"profile": user, "form": form})


@login_required
def follow_suggestions(request):
    users = generate_follow_suggestions(request.user)
    return render(request, "accounts/suggestions.html", {"users": users})


@login_required
def pending_requests(request):
    PendingList = Follow.objects.filter(
        following=request.user, status=Follow.Status.PENDING
    )

    FollowersCount = 0

    for i in PendingList:
        FollowersCount = Follow.objects.filter(
            following=i.follower, status=Follow.Status.ACCEPTED
        ).count()

    context = {"FollowersCount": FollowersCount, "PendingList": PendingList}
    return render(request, "accounts/pending-requests.html", context)


@login_required
def user_following(request, slug):
    user = get_object_or_404(User, slug=slug)
    if user.show_following == True or request.user == user:
        following = Follow.objects.filter(follower=user, status=Follow.Status.ACCEPTED)

        following_list = []
        for i in following:

            is_following = Follow.objects.filter(
                follower=request.user,
                following=i.following,
                status=Follow.Status.ACCEPTED,
            ).exists()

            is_follower = Follow.objects.filter(
                following=request.user,
                follower=i.following,
                status=Follow.Status.ACCEPTED,
            ).exists()

            followers_count = Follow.objects.filter(
                following=i.following, status=Follow.Status.ACCEPTED
            )

            following_count = Follow.objects.filter(
                follower=i.following, status=Follow.Status.ACCEPTED
            )

            following_list.append(
                {
                    "user": i.following,
                    "is_following": is_following,
                    "followers_count": followers_count,
                    "following_count": following_count,
                    "is_follower": is_follower,
                }
            )

        context = {
            "following_list": following_list,
            "user": user,
        }
        return render(request, "accounts/following.html", context)
    else:
        return redirect(f"/accounts/{slug}/")


@login_required
def user_followers(request, slug):
    user = get_object_or_404(User, slug=slug)
    if user.show_followers == True or request.user == user:
        followers = Follow.objects.filter(following=user, status=Follow.Status.ACCEPTED)

        followers_list = []

        for i in followers:
            is_following = Follow.objects.filter(
                follower=request.user,
                following=i.follower,
                status=Follow.Status.ACCEPTED,
            ).exists()

            is_follower = Follow.objects.filter(
                following=request.user,
                follower=i.follower,
                status=Follow.Status.ACCEPTED,
            ).exists()

            followers_count = Follow.objects.filter(
                following=i.follower, status=Follow.Status.ACCEPTED
            ).count()

            following_count = Follow.objects.filter(
                follower=i.follower, status=Follow.Status.ACCEPTED
            ).count()

            followers_list.append(
                {
                    "followers_count": followers_count,
                    "following_count": following_count,
                    "user": i.follower,
                    "is_follower": is_follower,
                    "is_following": is_following,
                }
            )

        context = {
            "user": user,
            "followers_list": followers_list,
        }
        return render(request, "accounts/followers.html", context)
    else:
        return redirect(f"/accounts/{slug}/")


@login_required
def send_follow(request, id):
    url = request.META.get("HTTP_REFERER")
    user = get_object_or_404(User, id=id)

    if request.user == user:
        messages.warning(request, "You cannot send follow request to yourself")
        return redirect(url)

    existing_request = Follow.objects.filter(
        follower=request.user, following=user
    ).first()

    if existing_request:
        if existing_request.status == Follow.Status.ACCEPTED:
            messages.warning(request, "You are already following this user")

        elif existing_request.status == Follow.Status.PENDING:
            messages.warning(request, "Request already pending")

    elif user.check_followers == False or request.user.is_admin:
        Follow.objects.create(
            follower=request.user, following=user, status=Follow.Status.ACCEPTED
        )

        follower = User.objects.get(id=request.user.id)
        following = User.objects.get(id=user.id)

        conversation = (
            Conversation.objects.filter(Q(participants=user)).filter(
                Q(participants=request.user)
            )
        ).exists()

        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(follower, following)

        messages.success(request, f"You are now following {user.username}")
        return redirect(url)

    else:
        Follow.objects.create(
            follower=request.user, following=user, status=Follow.Status.PENDING
        )

        messages.success(request, "Follow request sent successfully")
        return redirect(url)


@login_required
def user_unfollow(request, id):
    url = request.META.get("HTTP_REFERER")
    user = get_object_or_404(User, id=id)
    UserUnfollow = Follow.objects.filter(follower=request.user, following=user)

    if request.user == user:
        return redirect("profile", slug=user.slug)

    elif UserUnfollow.exists():
        UserUnfollow.delete()
        messages.success(request, f"You have unfollowed {user.username}")
    else:
        messages.warning(request, f"You were not following {user.username}")

    return redirect(url)


@login_required
def remove(request, id):
    url = request.META.get("HTTP_REFERER")
    user = get_object_or_404(User, id=id)
    follow = get_object_or_404(
        Follow,
        follower=user,
        following=request.user,
    )
    follow.delete()
    messages.success(request, f"Successfully Removed {follow.follower.username}")
    return redirect(url)


@login_required
def respond_to_follow(request, id, action):
    url = request.META.get("HTTP_REFERER")
    follow_request = get_object_or_404(Follow, id=id)

    if action == "accept":
        follow_request.status = "accepted"
        follow_request.save()

        follower = User.objects.get(id=follow_request.follower.id)
        following = User.objects.get(id=follow_request.following.id)

        conversation = (
            Conversation.objects.filter(Q(participants=follower)).filter(
                Q(participants=follower)
            )
        ).exists()

        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(follower, following)

        messages.success(request, "Follow request accepted")

    elif action == "cancel":
        follow_request.delete()

    return redirect(url)


@login_required
def cancel_request(request, id):
    url = request.META.get("HTTP_REFERER")
    target_user = get_object_or_404(User, id=id)
    notification = Notification.objects.filter(
        actor=request.user, recipient=target_user
    )
    follow_request = get_object_or_404(
        Follow,
        follower=request.user,
        following=target_user,
        status=Follow.Status.PENDING,
    )
    if notification.exists():
        notification.delete()
    follow_request.delete()
    messages.success(request, "Follow request cancelled")
    return redirect(url)


@login_required
def viewers_list(request, slug):
    if request.user.slug != slug:
        return redirect(f"/accounts/{slug}")

    if request.user.verified or request.user.is_admin:
        profile = get_object_or_404(User, slug=slug)
        visitors = profile.viewers.all()

        following_ids = Follow.objects.filter(
            follower=profile, status=Follow.Status.ACCEPTED
        ).values_list("following_id", flat=True)

        follower_ids = Follow.objects.filter(
            following=profile, status=Follow.Status.ACCEPTED
        ).values_list("follower_id", flat=True)

        visitor_list = []
        for i in visitors:
            is_following = i.id in following_ids
            is_follower = i.id in follower_ids

            visitor_list.append(
                {
                    "viewer": i,
                    "is_follower": is_follower,
                    "is_following": is_following,
                }
            )
        context = {"visitor_list": visitor_list, "profile": profile}
        return render(request, "accounts/viewers-list.html", context)

    else:
        messages.warning(
            request, "You Should Get Verify Your Account To Get This Feature"
        )
        return redirect(f"/accounts/{slug}/")


@login_required
def contact_us(request):
    form = ContactForm(request.POST)
    if request.method == "POST":
        contanct_form = ContactForm(request.POST)
        if form.is_valid():
            contanct_form.save()
            send_mail(
                subject="Sociala Media Contact-us",
                from_email=form.cleaned_data.get("email"),
                message=form.cleaned_data.get("message"),
                recipient_list=[settings.EMAIL_HOST_USER],
            )

            return JsonResponse(
                {"success": True, "message": "Thanks i'll get back to you soon."}
            )
        else:
            return JsonResponse({"success": False, "message": "Don't Mess"}, status=400)

    return render(request, "accounts/contact_us.html", {"form": form})
