from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid


class Post(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    caption = models.CharField(null=True, blank=True, max_length=2000)
    body = models.TextField(null=True, blank=True)
    tag = models.ManyToManyField("Tag", blank=True)
    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"

    @property
    def likes(self):
        return Like.objects.filter(content_type=ContentType.objects.get_for_model(self))

    class Meta:
        ordering = ("-created_at",)


class Comment(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    comment = models.CharField(max_length=1000)
    like_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s comment on {self.comment}"

    @property
    def likes(self):
        return Like.objects.filter(content_type=ContentType.objects.get_for_model(self))

    @property
    def is_reply(self):
        return self.parent is not None

    class Meta:
        ordering = ("-created_at",)


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} likes {self.content_type}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "content_type", "object_id"], name="unique_like"
            )
        ]
        indexes = [models.Index(fields=["content_type", "object_id"])]
        ordering = ("-created_at",)


class PostMedia(models.Model):
    CONTENT_TYPE = (
        ("video", "video"),
        ("image", "image"),
    )

    post = models.ForeignKey(Post, related_name="media", on_delete=models.CASCADE)
    file = models.FileField(upload_to="PostMedia", max_length=100)
    content_type = models.CharField(choices=CONTENT_TYPE, max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.post.id)


class Event(models.Model):
    user = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="events"
    )
    title = models.CharField(max_length=100)
    cover = models.ImageField(upload_to="Eventcover")
    date = models.DateTimeField()
    place = models.CharField(max_length=50)
    city = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
