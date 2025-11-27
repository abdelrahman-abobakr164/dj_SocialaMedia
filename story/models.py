from django.db import models
from django.conf import settings
from datetime import datetime, timedelta
import uuid


class Story(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stories"
    )
    file = models.FileField(upload_to="stories/", null=True, blank=True)
    caption = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user}'s story"

    def is_expired(self):
        return datetime.now().date() > self.expires_at.date()

    class Meta:
        verbose_name = "Story"
        verbose_name_plural = "Stories"
        ordering = ["-created_at"]


class StoryView(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="views")
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="viewed_stories",
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("story", "viewer")
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.viewer.username} viewed {self.story.user.username}'s story"
