from story.models import Story
from core.models import Event
from celery import shared_task
from django.utils import timezone


@shared_task
def delete_expired_stories():
    deleted_count, _ = Story.objects.filter(expires_at__lt=timezone.now()).delete()
    return deleted_count


@shared_task
def delete_expired_events():
    deleted_count, _ = Event.objects.filter(date__lt=timezone.now()).delete()
    return deleted_count
