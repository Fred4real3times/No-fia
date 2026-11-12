from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.tenancy.models import WorkspaceMembership

WRITE_ROLES = {WorkspaceMembership.Role.OWNER, WorkspaceMembership.Role.ADMIN, WorkspaceMembership.Role.ACCOUNTANT, WorkspaceMembership.Role.MANAGER}
ADMIN_ROLES = {WorkspaceMembership.Role.OWNER, WorkspaceMembership.Role.ADMIN}

class WorkspaceScopeMixin:
    """Resolve and verify workspace membership on every tenant-scoped request."""
    def get_membership(self, *, write: bool = False, admin: bool = False):
        workspace_id = self.request.query_params.get("workspace_id") or self.request.data.get("workspace_id")
        if not workspace_id:
            raise ValidationError({"workspace_id": "Ce paramètre est obligatoire."})
        membership = WorkspaceMembership.objects.select_related("workspace").filter(
            workspace_id=workspace_id, user=self.request.user, is_active=True,
            workspace__status="ACTIVE",
        ).first()
        if not membership:
            raise PermissionDenied("Aucun accès à ce workspace.")
        if admin and membership.role not in ADMIN_ROLES:
            raise PermissionDenied("Rôle ADMIN ou OWNER requis.")
        if write and membership.role not in WRITE_ROLES:
            raise PermissionDenied("Votre rôle ne permet pas cette opération.")
        return membership
