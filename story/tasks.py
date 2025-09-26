from celery import shared_task
from story.models import Story


@shared_task
def expired_story():
    stories = Story.objects.all()
    for story in stories:
        if story.is_expired():
            story.delete()
    return None
