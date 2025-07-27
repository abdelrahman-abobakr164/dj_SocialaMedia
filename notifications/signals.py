from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from notifications.models import Notification
from django.dispatch import receiver
from accounts.models import Follow
from conversation.models import *
from core.models import *


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    content_type = ContentType.objects.get_for_model(Follow)

    if created:
        if instance.following.check_followers == False or instance.follower.is_admin:
            Notification.objects.create(
                actor=instance.follower,
                recipient=instance.following,
                content_type=content_type,
                object_id=instance.id,
                ntype="New Follower",
            )

        else:
            Notification.objects.create(
                actor=instance.follower,
                recipient=instance.following,
                content_type=content_type,
                object_id=instance.id,
                ntype="Follow Request",
            )

    elif instance.status == "accepted":
        Notification.objects.create(
            actor=instance.following,
            recipient=instance.follower,
            content_type=content_type,
            object_id=instance.id,
            ntype="Follow Accepted",
        )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):

    if created and instance.user != instance.post.user:
        content_type = ContentType.objects.get_for_model(Comment)
        Notification.objects.create(
            actor=instance.user,
            recipient=instance.post.user,
            content_type=content_type,
            object_id=instance.post.id,
            ntype="Comment",
        )


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):

    if created:
        content_object = instance.content_object
        content_owner = content_object.user

        if instance.user != content_owner:
            model_class = content_object.__class__
            content_type = ContentType.objects.get_for_model(model_class)

            Notification.objects.create(
                actor=instance.user,
                recipient=content_owner,
                content_type=content_type,
                object_id=content_object.id,
                ntype="Like",
            )


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            actor=instance.sender,
            recipient=instance.conversation.other_participants(instance.sender),
            content_object=instance,
            ntype="Message",
        )
