from django.contrib import admin
from .models import Notification

# Register your models here.


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["ntype", "actor", "recipient", "read"]
    list_filter = ["read", "ntype"]
    list_per_page = 20
