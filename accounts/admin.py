from django.contrib import admin
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "first_name",
        "last_name",
        "username",
        "is_active",
        "is_superuser",
        "is_staff",
        "is_admin",
    ]
    list_filter = ["is_active", "is_superuser", "is_staff", "is_admin"]
    search_fields = ("email",)
    list_per_page = 20


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'status']
    list_per_page = 20

admin.site.register(Contact)