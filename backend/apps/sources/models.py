from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.tenancy.models import LegalEntity, Workspace


def quarantine_path(instance, filename: str) -> str:
    safe_name = filename.replace("/", "_").replace("\\", "_")[:180]
    return f"quarantine/{instance.workspace_id}/{instance.id}/{safe_name}"


class ImportBatch(models.Model):
    class ReportType(models.TextChoices):
        SALES = "SALES", "Ventes"
        CASH = "CASH", "Trésorerie / encaissements"
        BANK = "BANK", "Relevé bancaire"
        EXPENSES = "EXPENSES", "Dépenses"
        RECEIVABLES = "RECEIVABLES", "Créances clients"
        PAYABLES = "PAYABLES", "Dettes fournisseurs"
        OTHER = "OTHER", "Autre"

    class Status(models.TextChoices):
        QUARANTINED = "QUARANTINED", "En quarantaine"
        REVIEW = "REVIEW", "À vérifier"
        VALIDATED = "VALIDATED", "Validé"
        FAILED = "FAILED", "Échec"
        CANCELLED = "CANCELLED", "Annulé"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="import_batches")
    entity = models.ForeignKey(LegalEntity, on_delete=models.PROTECT, related_name="import_batches")
    file = models.FileField(upload_to=quarantine_path, max_length=500)
    original_filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64)
    size_bytes = models.PositiveBigIntegerField()
    detected_mime = models.CharField(max_length=100)
    report_type = models.CharField(max_length=16, choices=ReportType.choices, default=ReportType.OTHER)
    period_start = models.DateField()
    period_end = models.DateField()
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUARANTINED)
    parser_version = models.CharField(max_length=40, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    mapping = models.JSONField(default=dict, blank=True)
    rows_seen = models.PositiveIntegerField(default=0)
    rows_staged = models.PositiveIntegerField(default=0)
    rows_rejected = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace", "sha256"], name="uq_import_workspace_sha256")]
        indexes = [models.Index(fields=["workspace", "created_at"]), models.Index(fields=["entity", "period_start", "period_end"])]
        ordering = ["-created_at"]

    def clean(self):
        if self.entity_id and self.workspace_id != self.entity.workspace_id:
            raise ValueError("Import batch and entity must belong to the same workspace.")
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start.")


class MetricFact(models.Model):
    class Status(models.TextChoices):
        REVIEW = "REVIEW", "À vérifier"
        VALIDATED = "VALIDATED", "Validé"
        REJECTED = "REJECTED", "Rejeté"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="metric_facts")
    entity = models.ForeignKey(LegalEntity, on_delete=models.PROTECT, related_name="metric_facts")
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.PROTECT, related_name="facts")
    metric_key = models.CharField(max_length=64)
    value = models.DecimalField(max_digits=24, decimal_places=6)
    currency = models.CharField(max_length=3, blank=True)
    unit = models.CharField(max_length=24, default="AMOUNT")
    period_start = models.DateField()
    period_end = models.DateField()
    collected_at = models.DateTimeField(default=timezone.now)
    source_row = models.PositiveIntegerField(null=True, blank=True)
    source_column = models.CharField(max_length=120, blank=True)
    source_value = models.CharField(max_length=500, blank=True)
    transformation_rule = models.CharField(max_length=100)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.REVIEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["workspace", "status", "metric_key"]), models.Index(fields=["entity", "period_start", "period_end"])]

    def clean(self):
        if self.entity_id and (self.entity.workspace_id != self.workspace_id or self.import_batch.workspace_id != self.workspace_id or self.import_batch.entity_id != self.entity_id):
            raise ValueError("MetricFact, entity and import batch must share the same workspace and entity.")
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start.")


class ValidationIssue(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "À examiner"
        RESOLVED = "RESOLVED", "Résolu"
        REJECTED = "REJECTED", "Rejeté"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="validation_issues")
    import_batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="issues")
    row_number = models.PositiveIntegerField()
    field_name = models.CharField(max_length=120, blank=True)
    raw_value = models.CharField(max_length=500, blank=True)
    message = models.CharField(max_length=500)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["row_number"]
        indexes = [models.Index(fields=["workspace", "status"])]
