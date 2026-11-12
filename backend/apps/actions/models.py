import uuid
from django.conf import settings
from django.db import models
from apps.tenancy.models import LegalEntity, Workspace

class ActionItem(models.Model):
    class Status(models.TextChoices): OPEN = "OPEN", "Open"; IN_PROGRESS = "IN_PROGRESS", "In progress"; BLOCKED = "BLOCKED", "Blocked"; DONE = "DONE", "Done"; CANCELLED = "CANCELLED", "Cancelled"
    class Priority(models.TextChoices): LOW = "LOW", "Low"; MEDIUM = "MEDIUM", "Medium"; HIGH = "HIGH", "High"; CRITICAL = "CRITICAL", "Critical"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="actions")
    entity = models.ForeignKey(LegalEntity, null=True, blank=True, on_delete=models.PROTECT, related_name="actions")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_yfen_actions")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="assigned_yfen_actions")
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [models.Index(fields=["workspace", "status", "due_at"]), models.Index(fields=["workspace", "assigned_to", "status"])]
        ordering = ["status", "due_at", "-created_at"]
    def clean(self):
        from apps.tenancy.models import WorkspaceMembership
        if self.entity_id and self.entity.workspace_id != self.workspace_id:
            raise ValueError("Action entity must belong to the action workspace.")
        for person in [self.created_by, self.assigned_to]:
            if person and not WorkspaceMembership.objects.filter(workspace=self.workspace, user=person, is_active=True).exists():
                raise ValueError("Action creator and assignee must be active workspace members.")

class ActionComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.ForeignKey(ActionItem, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["created_at"]

class ActionEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.ForeignKey(ActionItem, on_delete=models.CASCADE, related_name="evidence")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    file = models.FileField(upload_to="action-evidence/%Y/%m/", max_length=500)
    original_filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
