from celery import shared_task
from story.models import Story
from datetime import datetime, timedelta


@shared_task
def expired_story():
    print("Celery Is Running")
    stories = Story.objects.all()
    for story in stories:
        if story.is_expired():
            story.delete()
    return None
