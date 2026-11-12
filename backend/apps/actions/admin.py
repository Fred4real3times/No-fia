from django.contrib import admin

from .models import ActionComment, ActionEvidence, ActionItem


class ActionCommentInline(admin.TabularInline):
    model = ActionComment
    extra = 0
    readonly_fields = ("author", "created_at")


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ("title", "workspace", "entity", "priority", "status", "assigned_to", "due_at")
    list_filter = ("priority", "status")
    search_fields = ("title", "description", "workspace__name", "entity__name")
    inlines = (ActionCommentInline,)


@admin.register(ActionEvidence)
class ActionEvidenceAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "action", "uploaded_by", "created_at")
    search_fields = ("original_filename", "sha256", "action__title")
    readonly_fields = ("sha256", "uploaded_by", "created_at")
