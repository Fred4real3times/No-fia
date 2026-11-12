import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

class Workspace(models.Model):
    class Status(models.TextChoices): ACTIVE = "ACTIVE", "Active"; SUSPENDED = "SUSPENDED", "Suspended"; CLOSED = "CLOSED", "Closed"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_workspaces")
    default_currency = models.CharField(max_length=3, default="XAF")
    timezone = models.CharField(max_length=64, default="Africa/Douala")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ["name"]
    def __str__(self): return self.name

class WorkspaceMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"; ADMIN = "ADMIN", "Admin"; ACCOUNTANT = "ACCOUNTANT", "Accountant"; MANAGER = "MANAGER", "Manager"; VIEWER = "VIEWER", "Viewer"
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="workspace_memberships")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.VIEWER)
    is_active = models.BooleanField(default=True)
    invited_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace", "user"], name="uq_workspace_membership_user")]
        indexes = [models.Index(fields=["user", "is_active"]), models.Index(fields=["workspace", "role"])]

class LegalEntity(models.Model):
    class Status(models.TextChoices): ACTIVE = "ACTIVE", "Active"; ARCHIVED = "ARCHIVED", "Archived"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="entities")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="subsidiaries")
    name = models.CharField(max_length=180)
    code = models.CharField(max_length=40)
    country_code = models.CharField(max_length=2, default="CM")
    functional_currency = models.CharField(max_length=3, default="XAF")
    sector = models.CharField(max_length=80, blank=True)
    timezone = models.CharField(max_length=64, default="Africa/Douala")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace", "code"], name="uq_entity_workspace_code")]
        ordering = ["name"]
    def clean(self):
        if self.parent_id and self.parent.workspace_id != self.workspace_id:
            raise ValidationError({"parent": "La société mère doit appartenir au même workspace."})
    def __str__(self): return self.name

class BusinessUnit(models.Model):
    class UnitType(models.TextChoices): LOCATION = "LOCATION", "Location"; ACTIVITY = "ACTIVITY", "Activity"; DEPARTMENT = "DEPARTMENT", "Department"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity = models.ForeignKey(LegalEntity, on_delete=models.CASCADE, related_name="business_units")
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=40)
    unit_type = models.CharField(max_length=16, choices=UnitType.choices, default=UnitType.LOCATION)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="managed_business_units")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["entity", "code"], name="uq_unit_entity_code")]
        ordering = ["name"]
    def clean(self):
        if self.manager_id and not WorkspaceMembership.objects.filter(workspace=self.entity.workspace, user=self.manager, is_active=True).exists():
            raise ValidationError({"manager": "Le responsable doit être membre actif du workspace."})
