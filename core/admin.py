from django.contrib import admin
from .models import *


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["user", "post", "comment", "created_at", "updated_at"]
    list_per_page = 20
    search_fields = ["user", "post"]


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at"]
    list_per_page = 20
    search_fields = ["user", "post"]


admin.site.register(Tag)
admin.site.register(Post)
admin.site.register(PostMedia)
admin.site.register(Event)
