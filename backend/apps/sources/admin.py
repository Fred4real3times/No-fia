from django.contrib import admin

from .models import ImportBatch, MetricFact, ValidationIssue


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "workspace", "entity", "report_type", "status", "created_at")
    list_filter = ("status", "report_type", "currency")
    search_fields = ("original_filename", "sha256", "workspace__name", "entity__name")
    readonly_fields = ("sha256", "size_bytes", "detected_mime", "uploaded_by", "created_at", "validated_at")


@admin.register(MetricFact)
class MetricFactAdmin(admin.ModelAdmin):
    list_display = ("metric_key", "value", "currency", "entity", "period_start", "period_end", "status")
    list_filter = ("status", "metric_key", "currency")
    search_fields = ("entity__name", "import_batch__original_filename", "source_value")
    readonly_fields = ("created_at", "collected_at")


@admin.register(ValidationIssue)
class ValidationIssueAdmin(admin.ModelAdmin):
    list_display = ("import_batch", "row_number", "field_name", "message", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("import_batch__original_filename", "message", "raw_value")
