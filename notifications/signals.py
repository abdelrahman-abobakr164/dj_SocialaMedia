from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from notifications.models import Notification
from .utils import send_notification_to_user
from django.dispatch import receiver
from django.db import transaction
from functools import partial

from accounts.models import Follow
from conversation.models import *
from core.models import *


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):

    if created:
        requires_approval = instance.following.check_followers
        ntype = "Follow Request" if requires_approval else "New Follower"
        actor, recipient = instance.follower, instance.following

    elif instance.status == Follow.Status.ACCEPTED:
        actor, recipient = instance.following, instance.follower
        ntype = "Follow Accepted"

    else:
        return

    notification = Notification.objects.create(
        actor=actor,
        recipient=recipient,
        content_type=ContentType.objects.get_for_model(Follow),
        object_id=str(instance.id),
        ntype=ntype,
    )

    transaction.on_commit(lambda: send_notification_to_user(notification))


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
        transaction.on_commit(lambda: send_notification_to_user(notification))


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
            transaction.on_commit(lambda: send_notification_to_user(notification))


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if not created:
        return
    for recipient in instance.conversation.recipients_for(instance.sender):
        notification = Notification.objects.create(
            actor=instance.sender,
            recipient=recipient,
            content_object=instance,
            ntype="Message",
        )
        transaction.on_commit(partial(send_notification_to_user, notification))
