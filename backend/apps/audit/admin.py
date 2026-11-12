from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "workspace", "actor", "action", "target_type", "target_id")
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("workspace__name", "actor__email", "target_id")
    readonly_fields = ("id", "workspace", "actor", "action", "target_type", "target_id", "metadata", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
