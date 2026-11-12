import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q
from apps.tenancy.models import LegalEntity, Workspace

class Alert(models.Model):
    class Severity(models.TextChoices): INFO = "INFO", "Info"; WARNING = "WARNING", "Warning"; CRITICAL = "CRITICAL", "Critical"
    class Status(models.TextChoices): OPEN = "OPEN", "Open"; ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"; RESOLVED = "RESOLVED", "Resolved"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="alerts")
    entity = models.ForeignKey(LegalEntity, null=True, blank=True, on_delete=models.PROTECT, related_name="alerts")
    rule_key = models.CharField(max_length=80)
    title = models.CharField(max_length=180)
    explanation = models.TextField()
    severity = models.CharField(max_length=12, choices=Severity.choices, default=Severity.INFO)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    evidence = models.JSONField(default=dict, blank=True)
    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    class Meta:
        indexes = [models.Index(fields=["workspace", "status", "severity"])]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "rule_key"],
                condition=Q(status__in=["OPEN", "ACKNOWLEDGED"]),
                name="uq_active_workspace_alert_rule",
            )
        ]
        ordering = ["-triggered_at"]
