from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Story, StoryView


@login_required
def create_story(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        caption = request.POST.get("caption")

        if file:
            story = Story(user=request.user, caption=caption)
            story.file = file
            story.save()

        else:
            return redirect("story:story_list")

        return redirect("story:story_list")

    return render(request, "story/create_story.html")


@login_required
def story_list(request):
    return render(request, "story/story_list.html")


@login_required
def view_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)

    if story.is_expired():
        messages.warning(request, "The Story is Expired")
        return redirect("story:story_list")

    if story.user != request.user:
        StoryView.objects.get_or_create(story=story, viewer=request.user)

    user_stories = (
        Story.objects.filter(user=story.user, expires_at__gt=timezone.now())
        .select_related("user")
        .order_by("-created_at")
    )

    current_index = list(user_stories).index(story)

    prev_story = user_stories[current_index - 1] if current_index > 0 else None
    next_story = (
        user_stories[current_index + 1]
        if current_index < len(user_stories) - 1
        else None
    )

    context = {
        "story": story,
        "prev_story": prev_story,
        "next_story": next_story,
        "view_count": StoryView.objects.filter(story=story).count(),
    }

    return render(request, "story/view_story.html", context)


@login_required
def delete_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)

    if story.user != request.user:
        return redirect("story:story_list")

    story.delete()
    return redirect("story:story_list")


@login_required
def story_viewers(request, story_id):
    story = get_object_or_404(Story, id=story_id)

    if story.user != request.user:
        return redirect("story:story_list")

    viewers = (
        StoryView.objects.filter(story=story)
        .select_related("viewer")
        .exclude(viewer=story.user)
        .order_by("-viewed_at")
    )

    context = {
        "story": story,
        "viewers": viewers,
    }

    return render(request, "story/story_viewers.html", context)
