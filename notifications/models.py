from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import models
from core.models import *

# Create your models here.


User = get_user_model()


NOTIFICATION_CHOICES = (
    ("Follow Accepted", "Follow Accepted"),
    ("Follow Request", "Follow Request"),
    ("New Follower", "New Follower"),
    ("Comment", "Comment"),
    ("Like", "Like"),
    ("Message", "Message"),
)


class Notification(models.Model):
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    ntype = models.CharField(max_length=17, choices=NOTIFICATION_CHOICES)
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="receiver"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    content_object = GenericForeignKey("content_type", "object_id")
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["read"]),
        ]

    def __str__(self):
        return f"({self.ntype}) {self.actor} => {self.recipient}"
