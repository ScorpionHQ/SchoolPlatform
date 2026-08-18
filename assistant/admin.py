from django.contrib import admin

from .models import Attachment, Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = False


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ("name", "kind", "size", "created_at")
    can_delete = True


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "created_at", "updated_at")
    list_select_related = ("user",)
    search_fields = ("user__username", "user__first_name")
    inlines = (MessageInline, AttachmentInline)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("pk", "conversation", "role", "created_at")
    list_select_related = ("conversation",)
    list_filter = ("role",)
    search_fields = ("content",)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "kind", "size", "user", "created_at")
    list_select_related = ("user",)
    list_filter = ("kind",)
    search_fields = ("name", "user__username")
