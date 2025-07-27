from django.contrib import admin
from conversation.models import *

# Register your models here.


class MessageAdmin(admin.ModelAdmin):
    list_display = ["conversation", "sender", "content", "read"]
    list_editable = ("read",)
    list_per_page = 20


class UserStatusAdmin(admin.ModelAdmin):
    list_display = ["user", "conversation", "status"]
    list_editable = ["status"]
    list_per_page = 20


admin.site.register(UserStatus, UserStatusAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(MessageAttachment)
admin.site.register(Conversation)
