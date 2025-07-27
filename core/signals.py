from django.db.models.signals import post_save, post_delete
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from core.models import *


@receiver([post_save, post_delete], sender=Like)
def increase_likes(sender, instance, **kwargs):

    model_class = instance.content_object.__class__
    content_type = ContentType.objects.get_for_model(model_class)

    if model_class == Post:
        Post.objects.filter(id=instance.object_id).update(
            like_count=Like.objects.filter(
                content_type=content_type, object_id=instance.object_id
            ).count()
        )

    if model_class == Comment:
        Comment.objects.filter(id=instance.object_id).update(
            like_count=Like.objects.filter(
                content_type=content_type, object_id=instance.object_id
            ).count()
        )
