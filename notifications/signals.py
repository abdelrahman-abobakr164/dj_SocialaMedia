from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from notifications.models import Notification
from django.dispatch import receiver
from accounts.models import Follow
from conversation.models import *
from core.models import *
from .utils import send_notification


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        if instance.following.check_followers == False or instance.follower.is_admin:
            send_notification(
                actor=instance.follower,
                recipient=instance.following,
                ntype="New Follower",
                content_object=instance,
                extra_data={
                    "follower_profile": instance.follower.get_absolute_url(),
                    "action_url": f"/profile/{instance.follower.slug}/"
                }
            )
        else:
            send_notification(
                actor=instance.follower,
                recipient=instance.following,
                ntype="Follow Request",
                content_object=instance,
                extra_data={
                    "follower_profile": instance.follower.get_absolute_url(),
                    "action_url": f"/profile/{instance.follower.slug}/"
                }
            )

    elif instance.status == "accepted":
        send_notification(
            actor=instance.following,
            recipient=instance.follower,
            ntype="Follow Accepted",
            content_object=instance,
            extra_data={
                "profile_url": instance.following.get_absolute_url(),
                "action_url": f"/profile/{instance.following.slug}/"
            }
        )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created and instance.user != instance.post.user:
        send_notification(
            actor=instance.user,
            recipient=instance.post.user,
            ntype="Comment",
            content_object=instance.post,
            extra_data={
                "comment_content": instance.content[:100] + "..." if len(instance.content) > 100 else instance.content,
                "post_url": instance.post.get_absolute_url(),
                "action_url": instance.post.get_absolute_url()
            }
        )


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if created:
        content_object = instance.content_object
        content_owner = content_object.user

        if instance.user != content_owner:
            send_notification(
                actor=instance.user,
                recipient=content_owner,
                ntype="Like",
                content_object=content_object,
                extra_data={
                    "content_type": content_object.__class__.__name__.lower(),
                    "content_url": content_object.get_absolute_url() if hasattr(content_object, 'get_absolute_url') else "#",
                    "action_url": content_object.get_absolute_url() if hasattr(content_object, 'get_absolute_url') else "#"
                }
            )


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        other_participant = instance.conversation.other_participants(instance.sender)
        if other_participant:
            send_notification(
                actor=instance.sender,
                recipient=other_participant,
                ntype="Message",
                content_object=instance,
                extra_data={
                    "message_preview": instance.content[:50] + "..." if instance.content and len(instance.content) > 50 else instance.content or "Attachment",
                    "conversation_url": instance.conversation.get_absolute_url(),
                    "action_url": instance.conversation.get_absolute_url()
                }
            )
