from celery import Celery
import os
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_media.settings")

app = Celery("social_media")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "delete-expired-stories-every-hour": {
        "task": "story.tasks.expired_story",
        "schedule": crontab(minute=0, hour="*"),
    }
}
