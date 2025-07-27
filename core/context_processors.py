from core.models import Post, Comment
from django.contrib.contenttypes.models import ContentType


def content_types(request):
    return {
        "post_content_type_id": ContentType.objects.get_for_model(Post).id,
        "comment_content_type_id": ContentType.objects.get_for_model(Comment).id,
    }
