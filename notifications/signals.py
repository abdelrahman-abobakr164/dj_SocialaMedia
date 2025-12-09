from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from notifications.models import Notification
from .utils import send_notification_to_user
from django.dispatch import receiver
from accounts.models import Follow
from conversation.models import *
from core.models import *


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    content_type = ContentType.objects.get_for_model(Follow)

    if created:
        ntype = "Follow Request"
        if not instance.following.check_followers or instance.follower.is_admin:
            ntype = "New Follower"

        notification = Notification.objects.create(
            actor=instance.follower,
            recipient=instance.following,
            content_type=content_type,
            object_id=str(instance.id),
            ntype=ntype,
        )
        send_notification_to_user(notification)

    elif instance.status == "accepted":
        notification = Notification.objects.create(
            actor=instance.following,
            recipient=instance.follower,
            content_type=content_type,
            object_id=str(instance.id),
            ntype="Follow Accepted",
        )
        send_notification_to_user(notification)


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created and instance.user != instance.post.user:
        content_type = ContentType.objects.get_for_model(Comment)
        notification = Notification.objects.create(
            actor=instance.user,
            recipient=instance.post.user,
            content_type=content_type,
            object_id=str(instance.post.id),
            ntype="Comment",
        )
        send_notification_to_user(notification)


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):

    if created:
        content_object = instance.content_object
        content_owner = content_object.user

        if instance.user != content_owner:
            content_type = ContentType.objects.get_for_model(content_object.__class__)

            notification = Notification.objects.create(
                actor=instance.user,
                recipient=content_owner,
                content_type=content_type,
                object_id=str(content_object.id),
                ntype="Like",
            )
        send_notification_to_user(notification)


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        notification = Notification.objects.create(
            actor=instance.sender,
            recipient=instance.conversation.other_participants(instance.sender),
            content_object=instance,
            ntype="Message",
        )
        send_notification_to_user(notification)
