from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "workspace", "entity", "severity", "status", "triggered_at")
    list_filter = ("severity", "status")
    search_fields = ("title", "rule_key", "workspace__name", "explanation")
    readonly_fields = ("triggered_at",)
