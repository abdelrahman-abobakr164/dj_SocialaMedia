import uuid
from django.db import models
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator

User = get_user_model()


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name="conversations")
    admin = models.ManyToManyField(User, related_name="conversation_admin", blank=True)
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=100, null=True, blank=True, unique=True)
    group_image = models.ImageField(upload_to="group_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        if self.is_group:
            return self.group_name or f"Group {self.id}"
        participants = self.participants.all()
        return f"{participants[0]} => {participants[1]}"

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("conversation", kwargs={"pk": self.id})

    def other_participants(self, user):
        return self.participants.exclude(id=user.id).first()

    def recipients_for(self, user):
        return self.participants.exclude(id=user.id)

    def mark_as_read_by(self, user):
        unread = Message.objects.filter(conversation=self).exclude(sender=user)

        if not self.is_group:
            unread.filter(read=False).update(read=True)
            return

        message_ids = list(unread.exclude(read_by=user).values_list("id", flat=True))

        if not message_ids:
            return

        user.read_messages.add(*message_ids)

        needed = self.participants.count() - 1

        fully_read_ids = list(
            Message.objects.filter(id__in=message_ids)
            .annotate(readers=Count("read_by"))
            .filter(readers__gte=needed)
            .values_list("id", flat=True)
        )
        Message.objects.filter(id__in=fully_read_ids).update(read=True)


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        User, related_name="message_sender", on_delete=models.CASCADE
    )
    content = models.TextField(
        validators=[MaxLengthValidator(2000)], null=True, blank=True
    )
    read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, related_name="read_messages", blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]


class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message, related_name="attachments", on_delete=models.CASCADE
    )
    file_name = models.CharField(max_length=50, null=True, blank=True)
    file = models.FileField(upload_to="message_attachments/")
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for message {self.message.id}"


class UserStatus(models.Model):
    STATUS_CHOICES = (("Block", "Block"),)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="conversation_status"
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, null=True, blank=True
    )

    def __str__(self):
        return f"{self.user.username}'s status for conversation {self.conversation.id}"
