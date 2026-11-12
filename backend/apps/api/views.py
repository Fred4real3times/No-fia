from __future__ import annotations

import csv
import hashlib
import io
import tempfile
from datetime import date
from decimal import InvalidOperation
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from apps.actions.models import ActionItem
from apps.alerts.models import Alert
from apps.audit.models import AuditEvent
from apps.sources.models import ImportBatch, MetricFact, ValidationIssue
from apps.tenancy.models import BusinessUnit, LegalEntity, Workspace, WorkspaceMembership
from .data_services import METRIC_BY_REPORT, METRIC_LABELS, parse_decimal, parse_source_date, read_tabular_file
from .metrics import build_cockpit, evaluate_workspace_alerts
from .permissions import WorkspaceScopeMixin
from .serializers import (
    ActionCommentSerializer,
    ActionSerializer,
    BusinessUnitSerializer,
    CreateWorkspaceSerializer,
    EntitySerializer,
    ImportBatchSerializer,
    WorkspaceSerializer,
)

User = get_user_model()
MAX_IMPORT_BYTES = 10 * 1024 * 1024


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspaceListCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = WorkspaceMembership.objects.filter(
            user=request.user, is_active=True, workspace__status=Workspace.Status.ACTIVE
        ).select_related("workspace")
        data = []
        for membership in memberships:
            item = dict(WorkspaceSerializer(membership.workspace).data)
            item["role"] = membership.role
            data.append(item)
        return Response(data)

    def post(self, request):
        serializer = CreateWorkspaceSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            workspace = serializer.save()
            AuditEvent.objects.create(
                workspace=workspace, actor=request.user, action="WORKSPACE_CREATED",
                target_type="Workspace", target_id=str(workspace.id),
            )
        data = dict(WorkspaceSerializer(workspace).data)
        data["role"] = WorkspaceMembership.Role.OWNER
        return Response(data, status=status.HTTP_201_CREATED)


class EntityListCreateView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = self.get_membership()
        qs = LegalEntity.objects.filter(workspace=membership.workspace).select_related("parent")
        return Response(EntitySerializer(qs, many=True).data)

    def post(self, request):
        membership = self.get_membership(write=True)
        serializer = EntitySerializer(data=request.data, context={"workspace": membership.workspace})
        serializer.is_valid(raise_exception=True)
        entity = serializer.save(workspace=membership.workspace)
        AuditEvent.objects.create(
            workspace=membership.workspace, actor=request.user, action="ENTITY_CREATED",
            target_type="LegalEntity", target_id=str(entity.id),
        )
        return Response(EntitySerializer(entity).data, status=status.HTTP_201_CREATED)


class BusinessUnitListCreateView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = self.get_membership()
        qs = BusinessUnit.objects.filter(entity__workspace=membership.workspace).select_related("entity", "manager")
        entity_id = request.query_params.get("entity_id")
        if entity_id:
            qs = qs.filter(entity_id=entity_id)
        return Response(BusinessUnitSerializer(qs, many=True).data)

    def post(self, request):
        membership = self.get_membership(write=True)
        serializer = BusinessUnitSerializer(data=request.data, context={"workspace": membership.workspace})
        serializer.is_valid(raise_exception=True)
        unit = serializer.save()
        AuditEvent.objects.create(
            workspace=membership.workspace, actor=request.user, action="BUSINESS_UNIT_CREATED",
            target_type="BusinessUnit", target_id=str(unit.id),
        )
        return Response(BusinessUnitSerializer(unit).data, status=status.HTTP_201_CREATED)


class WorkspaceMembersView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = self.get_membership()
        qs = WorkspaceMembership.objects.filter(workspace=membership.workspace, is_active=True).select_related("user")
        return Response([
            {"id": m.id, "user_id": m.user_id, "email": m.user.email,
             "full_name": m.user.display_name or m.user.get_full_name(), "role": m.role}
            for m in qs
        ])

    def post(self, request):
        membership = self.get_membership(admin=True, write=True)
        email = str(request.data.get("email", "")).strip().lower()
        role = str(request.data.get("role", WorkspaceMembership.Role.VIEWER)).upper()
        allowed = {WorkspaceMembership.Role.ADMIN, WorkspaceMembership.Role.ACCOUNTANT,
                   WorkspaceMembership.Role.MANAGER, WorkspaceMembership.Role.VIEWER}
        if not email:
            raise ValidationError({"email": "Adresse e-mail obligatoire."})
        if role not in allowed:
            raise ValidationError({"role": "Rôle non autorisé pour une invitation."})
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            raise ValidationError({"email": "Ce compte YFEN n’existe pas encore. L’invitation e-mail sera ajoutée dans une prochaine étape."})
        obj, created = WorkspaceMembership.objects.get_or_create(
            workspace=membership.workspace, user=user, defaults={"role": role, "is_active": True}
        )
        if not created and obj.is_active:
            raise ValidationError({"email": "Cette personne est déjà membre du workspace."})
        obj.role = role
        obj.is_active = True
        obj.save(update_fields=["role", "is_active"])
        AuditEvent.objects.create(
            workspace=membership.workspace, actor=request.user, action="MEMBER_ADDED",
            target_type="WorkspaceMembership", target_id=str(obj.id), metadata={"email": email, "role": role},
        )
        return Response({"id": obj.id, "email": user.email, "role": obj.role}, status=status.HTTP_201_CREATED)


class ActionListCreateView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = self.get_membership()
        qs = ActionItem.objects.filter(workspace=membership.workspace).select_related(
            "entity", "created_by", "assigned_to"
        ).prefetch_related("comments")
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if request.query_params.get("assigned_to_me") == "true":
            qs = qs.filter(assigned_to=request.user)
        return Response(ActionSerializer(qs[:200], many=True, context={"workspace": membership.workspace}).data)

    def post(self, request):
        membership = self.get_membership(write=True)
        serializer = ActionSerializer(data=request.data, context={"workspace": membership.workspace})
        serializer.is_valid(raise_exception=True)
        action = serializer.save(workspace=membership.workspace, created_by=request.user)
        AuditEvent.objects.create(
            workspace=membership.workspace, actor=request.user, action="ACTION_CREATED",
            target_type="ActionItem", target_id=str(action.id), metadata={"priority": action.priority},
        )
        return Response(ActionSerializer(action, context={"workspace": membership.workspace}).data,
                        status=status.HTTP_201_CREATED)


class ActionDetailView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, membership, action_id):
        try:
            return ActionItem.objects.select_related("entity", "created_by", "assigned_to").prefetch_related(
                "comments"
            ).get(id=action_id, workspace=membership.workspace)
        except ActionItem.DoesNotExist as exc:
            raise NotFound("Action introuvable dans ce workspace.") from exc

    def patch(self, request, action_id):
        membership = self.get_membership(write=True)
        action = self.get_object(membership, action_id)
        serializer = ActionSerializer(action, data=request.data, partial=True,
                                      context={"workspace": membership.workspace})
        serializer.is_valid(raise_exception=True)
        old_status = action.status
        updated = serializer.save()
        if updated.status == ActionItem.Status.DONE and old_status != ActionItem.Status.DONE:
            updated.completed_at = timezone.now()
            updated.save(update_fields=["completed_at", "updated_at"])
        elif updated.status != ActionItem.Status.DONE and old_status == ActionItem.Status.DONE:
            updated.completed_at = None
            updated.save(update_fields=["completed_at", "updated_at"])
        AuditEvent.objects.create(
            workspace=membership.workspace, actor=request.user, action="ACTION_UPDATED",
            target_type="ActionItem", target_id=str(updated.id),
            metadata={"from_status": old_status, "to_status": updated.status},
        )
        return Response(ActionSerializer(updated, context={"workspace": membership.workspace}).data)


class ActionCommentListCreateView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, action_id):
        membership = self.get_membership()
        action = ActionItem.objects.filter(workspace=membership.workspace, id=action_id).first()
        if not action:
            raise NotFound("Action introuvable.")
        return Response(ActionCommentSerializer(action.comments.select_related("author"), many=True).data)

    def post(self, request, action_id):
        membership = self.get_membership(write=True)
        action = ActionItem.objects.filter(workspace=membership.workspace, id=action_id).first()
        if not action:
            raise NotFound("Action introuvable.")
        serializer = ActionCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(action=action, author=request.user)
        AuditEvent.objects.create(
            workspace=membership.workspace, actor=request.user, action="ACTION_COMMENTED",
            target_type="ActionItem", target_id=str(action.id),
        )
        return Response(ActionCommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class ImportBatchListCreateView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = self.get_membership()
        qs = ImportBatch.objects.filter(workspace=membership.workspace).select_related("entity", "uploaded_by")
        return Response(ImportBatchSerializer(qs[:100], many=True).data)

    def post(self, request):
        membership = self.get_membership(write=True)
        uploaded = request.FILES.get("file")
        if not uploaded:
            raise ValidationError({"file": "Fichier obligatoire."})
        if uploaded.size <= 0 or uploaded.size > MAX_IMPORT_BYTES:
            raise ValidationError({"file": "Le fichier doit peser entre 1 octet et 10 Mo."})
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in {".csv", ".xlsx", ".pdf"}:
            raise ValidationError({"file": "Formats acceptés : CSV, XLSX et PDF textuel."})
        first = uploaded.read(8)
        uploaded.seek(0)
        signatures = {".xlsx": b"PK", ".pdf": b"%PDF-"}
        if suffix in signatures and not first.startswith(signatures[suffix]):
            raise ValidationError({"file": "La signature du fichier ne correspond pas à son extension."})
        if suffix == ".csv":
            sample = uploaded.read(min(uploaded.size, 4096))
            uploaded.seek(0)
            if b"\x00" in sample:
                raise ValidationError({"file": "Le CSV contient des octets nuls."})
            try:
                sample.decode("utf-8-sig")
            except UnicodeDecodeError:
                try:
                    sample.decode("cp1252")
                except UnicodeDecodeError as exc:
                    raise ValidationError({"file": "Encodage CSV non reconnu."}) from exc
        entity_id = request.data.get("entity")
        entity = LegalEntity.objects.filter(id=entity_id, workspace=membership.workspace, status="ACTIVE").first()
        if not entity:
            raise ValidationError({"entity": "Entité inconnue dans le workspace actif."})
        try:
            period_start = date.fromisoformat(request.data.get("period_start", ""))
            period_end = date.fromisoformat(request.data.get("period_end", ""))
        except (TypeError, ValueError) as exc:
            raise ValidationError({"period": "Les dates doivent être au format AAAA-MM-JJ."}) from exc
        if period_end < period_start:
            raise ValidationError({"period_end": "La date de fin précède la date de début."})
        digest = hashlib.sha256()
        for chunk in uploaded.chunks():
            digest.update(chunk)
        sha = digest.hexdigest()
        if ImportBatch.objects.filter(workspace=membership.workspace, sha256=sha).exists():
            raise ValidationError({"file": "Ce fichier a déjà été importé dans ce workspace."})
        report_type = request.data.get("report_type", ImportBatch.ReportType.OTHER)
        if report_type not in ImportBatch.ReportType.values:
            raise ValidationError({"report_type": "Type de rapport non reconnu."})
        currency = str(request.data.get("currency", entity.functional_currency)).upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValidationError({"currency": "Code devise à 3 lettres requis."})
        mime = {".csv": "text/csv", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".pdf": "application/pdf"}[suffix]
        try:
            with transaction.atomic():
                batch = ImportBatch.objects.create(
                    workspace=membership.workspace, entity=entity, file=uploaded,
                    original_filename=Path(uploaded.name).name[:255], sha256=sha,
                    size_bytes=uploaded.size, detected_mime=mime, report_type=report_type,
                    period_start=period_start, period_end=period_end, currency=currency,
                    status=ImportBatch.Status.QUARANTINED, uploaded_by=request.user,
                )
                AuditEvent.objects.create(
                    workspace=membership.workspace, actor=request.user, action="IMPORT_QUARANTINED",
                    target_type="ImportBatch", target_id=str(batch.id),
                    metadata={"sha256": sha, "size_bytes": batch.size_bytes},
                )
        except IntegrityError as exc:
            raise ValidationError({"file": "Ce fichier existe déjà dans le workspace."}) from exc
        return Response(ImportBatchSerializer(batch).data, status=status.HTTP_201_CREATED)


class ImportBatchPreviewView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        membership = self.get_membership()
        batch = ImportBatch.objects.filter(id=batch_id, workspace=membership.workspace).first()
        if not batch:
            raise NotFound("Lot d’import introuvable.")
        if batch.status not in {ImportBatch.Status.QUARANTINED, ImportBatch.Status.REVIEW}:
            raise ValidationError({"status": "Ce lot ne peut plus être prévisualisé."})
        suffix = Path(batch.original_filename).suffix.lower()
        if suffix == ".pdf":
            try:
                import pdfplumber
                with batch.file.open("rb") as file_obj:
                    with pdfplumber.open(file_obj) as pdf:
                        text_pages = [(page.extract_text() or "") for page in pdf.pages[:10]]
                text_preview = "\n\n".join(text_pages)[:6000]
            except Exception as exc:
                raise ValidationError({"file": "Impossible d’extraire le texte du PDF."}) from exc
            return Response({"batch_id": str(batch.id), "format": "pdf-text", "assisted": True,
                             "text_preview": text_preview,
                             "message": "Extraction textuelle uniquement. Vérifie et structure les données dans un CSV/XLSX avant validation.",
                             "can_stage": False})
        try:
            with batch.file.open("rb") as file_obj:
                content = file_obj.read(MAX_IMPORT_BYTES + 1)
            with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
                tmp.write(content)
                tmp.flush()
                headers, rows = read_tabular_file(tmp.name, batch.original_filename)
        except (ValueError, OSError) as exc:
            raise ValidationError({"file": str(exc)}) from exc
        aliases = {"amount": ["amount", "montant", "valeur", "total", "debit", "credit", "solde", "balance",
                               "closing balance", "closing_balance", "solde de clôture", "solde_cloture", "solde_final"],
                   "date": ["date", "transaction_date", "date_operation", "date opération"]}
        suggested = {}
        for field, choices in aliases.items():
            match = next((h for h in headers if h.strip().lower() in choices), None)
            if match:
                suggested[field] = match
        batch.rows_seen = len(rows)
        batch.save(update_fields=["rows_seen"])
        is_bank_balance = batch.report_type == ImportBatch.ReportType.BANK
        return Response({"batch_id": str(batch.id), "format": suffix[1:], "columns": headers,
                         "row_count": len(rows), "sample": rows[:10], "suggested_mapping": suggested,
                         "metric_key": METRIC_BY_REPORT.get(batch.report_type), "can_stage": True,
                         "mapping_note": ("Pour un relevé bancaire, sélectionne la colonne de solde de clôture (pas le montant des mouvements). "
                                          "YFEN conservera le solde de la dernière date présente dans le fichier." if is_bank_balance else "")})


class ImportBatchStageView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        membership = self.get_membership(write=True)
        batch = ImportBatch.objects.filter(id=batch_id, workspace=membership.workspace).first()
        if not batch:
            raise NotFound("Lot d’import introuvable.")
        if batch.status not in {ImportBatch.Status.QUARANTINED, ImportBatch.Status.REVIEW}:
            raise ValidationError({"status": "Ce lot ne peut plus être préparé."})
        mapping = request.data.get("mapping") or {}
        amount_column = str(mapping.get("amount", ""))
        date_column = str(mapping.get("date", ""))
        metric_key = METRIC_BY_REPORT.get(batch.report_type)
        if not amount_column or not metric_key:
            raise ValidationError({"mapping": "La colonne du montant est obligatoire."})
        if batch.report_type == ImportBatch.ReportType.BANK:
            normalized_balance_column = amount_column.strip().lower().replace("_", " ")
            allowed_balance_names = {"solde", "balance", "closing balance", "solde de clôture", "solde cloture", "solde final"}
            if normalized_balance_column not in allowed_balance_names:
                raise ValidationError({"mapping": "Pour un relevé bancaire, la colonne doit explicitement représenter le solde de clôture (ex. Solde, Balance ou Closing balance). Le montant des mouvements ne peut pas être utilisé comme solde."})
            if not date_column:
                raise ValidationError({"mapping": "La date est obligatoire pour identifier le dernier solde de clôture."})
        if MetricFact.objects.filter(import_batch=batch).exists():
            raise ValidationError({"status": "Des faits ont déjà été préparés pour ce lot."})
        try:
            with batch.file.open("rb") as file_obj:
                content = file_obj.read(MAX_IMPORT_BYTES + 1)
            suffix = Path(batch.original_filename).suffix.lower()
            with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
                tmp.write(content)
                tmp.flush()
                headers, rows = read_tabular_file(tmp.name, batch.original_filename)
        except (ValueError, OSError) as exc:
            raise ValidationError({"file": str(exc)}) from exc
        if amount_column not in headers or (date_column and date_column not in headers):
            raise ValidationError({"mapping": "La correspondance choisie n’existe pas dans le fichier."})
        period_start = batch.period_start
        period_end = batch.period_end
        facts = []
        issues = []
        for row_number, row in enumerate(rows, start=2):
            raw = row.get(amount_column, "")
            try:
                amount = parse_decimal(raw, allow_negative=batch.report_type == ImportBatch.ReportType.BANK)
                if date_column:
                    source_date = parse_source_date(row.get(date_column, ""))
                    if source_date < period_start or source_date > period_end:
                        raise ValueError("date hors de la période déclarée")
                fact_start = source_date if batch.report_type == ImportBatch.ReportType.BANK else period_start
                fact_end = source_date if batch.report_type == ImportBatch.ReportType.BANK else period_end
                rule = (f"latest-closing-balance:{amount_column}:v1" if batch.report_type == ImportBatch.ReportType.BANK
                        else f"sum-column:{amount_column}:v1")
                facts.append(MetricFact(
                    workspace=membership.workspace, entity=batch.entity, import_batch=batch,
                    metric_key=metric_key, value=amount, currency=batch.currency, unit="AMOUNT",
                    period_start=fact_start, period_end=fact_end, collected_at=timezone.now(),
                    source_row=row_number, source_column=amount_column, source_value=raw[:500],
                    transformation_rule=rule, status=MetricFact.Status.REVIEW,
                ))
            except (InvalidOperation, ValueError) as exc:
                is_amount_error = isinstance(exc, InvalidOperation)
                issue_value = raw if is_amount_error else row.get(date_column, "")
                issues.append(ValidationIssue(
                    workspace=membership.workspace, import_batch=batch, row_number=row_number,
                    field_name=amount_column if is_amount_error else date_column,
                    raw_value=issue_value[:500],
                    message=("Montant invalide ou négatif." if is_amount_error else str(exc))[:500],
                ))
        if batch.report_type == ImportBatch.ReportType.BANK and facts:
            facts = [max(facts, key=lambda fact: (fact.period_end, fact.source_row or 0))]
        with transaction.atomic():
            if facts:
                MetricFact.objects.bulk_create(facts, batch_size=500)
            if issues:
                ValidationIssue.objects.bulk_create(issues, batch_size=500)
            batch.mapping = {"amount": amount_column, "date": date_column, "metric_key": metric_key}
            batch.rows_seen = len(rows)
            batch.rows_staged = len(facts)
            batch.rows_rejected = len(issues)
            batch.status = ImportBatch.Status.REVIEW
            batch.parser_version = "yfen-tabular-v1"
            batch.save(update_fields=["mapping", "rows_seen", "rows_staged", "rows_rejected", "status", "parser_version"])
            AuditEvent.objects.create(
                workspace=membership.workspace, actor=request.user, action="IMPORT_STAGED",
                target_type="ImportBatch", target_id=str(batch.id),
                metadata={"rows_seen": len(rows), "rows_staged": len(facts), "rows_rejected": len(issues), "mapping": batch.mapping},
            )
        return Response({"batch": ImportBatchSerializer(batch).data, "metric_label": METRIC_LABELS[metric_key],
                         "rows_staged": len(facts), "rows_rejected": len(issues),
                         "issues": [{"row_number": i.row_number, "field_name": i.field_name, "raw_value": i.raw_value, "message": i.message} for i in issues[:100]],
                         "requires_confirmation": True}, status=status.HTTP_200_OK)


class ImportBatchConfirmView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        membership = self.get_membership(write=True)
        batch = ImportBatch.objects.filter(id=batch_id, workspace=membership.workspace).first()
        if not batch:
            raise NotFound("Lot d’import introuvable.")
        if batch.status != ImportBatch.Status.REVIEW:
            raise ValidationError({"status": "Le lot doit être en revue avant confirmation."})
        facts = MetricFact.objects.filter(import_batch=batch, workspace=membership.workspace,
                                          status=MetricFact.Status.REVIEW)
        if not facts.exists():
            raise ValidationError({"facts": "Aucun fait valide à publier. Corrige le fichier puis réimporte-le."})
        with transaction.atomic():
            count = facts.update(status=MetricFact.Status.VALIDATED)
            batch.status = ImportBatch.Status.VALIDATED
            batch.validated_at = timezone.now()
            batch.save(update_fields=["status", "validated_at"])
            AuditEvent.objects.create(
                workspace=membership.workspace, actor=request.user, action="IMPORT_VALIDATED",
                target_type="ImportBatch", target_id=str(batch.id), metadata={"facts_published": count},
            )
        return Response({"batch": ImportBatchSerializer(batch).data, "facts_published": count,
                         "rejected_rows": batch.rows_rejected})


class ImportBatchCancelView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        membership = self.get_membership(write=True)
        batch = ImportBatch.objects.filter(id=batch_id, workspace=membership.workspace).first()
        if not batch:
            raise NotFound("Lot d’import introuvable.")
        if batch.status == ImportBatch.Status.VALIDATED:
            raise ValidationError({"status": "Un lot validé ne peut pas être supprimé ici. Utilise une annulation auditée dédiée."})
        batch.status = ImportBatch.Status.CANCELLED
        batch.save(update_fields=["status"])
        MetricFact.objects.filter(import_batch=batch, status=MetricFact.Status.REVIEW).update(status=MetricFact.Status.REJECTED)
        AuditEvent.objects.create(workspace=membership.workspace, actor=request.user, action="IMPORT_CANCELLED",
                                  target_type="ImportBatch", target_id=str(batch.id))
        return Response({"status": batch.status})


class CockpitView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = self.get_membership()
        entity_id = request.query_params.get("entity_id")
        if entity_id and not LegalEntity.objects.filter(id=entity_id, workspace=membership.workspace).exists():
            raise ValidationError({"entity_id": "Entité hors du workspace actif."})
        return Response(build_cockpit(membership.workspace, entity_id=entity_id))


class AlertListView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = self.get_membership()
        if request.query_params.get("evaluate") == "true":
            evaluate_workspace_alerts(membership.workspace)
        qs = Alert.objects.filter(workspace=membership.workspace).select_related("entity", "acknowledged_by")
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        return Response([{
            "id": str(a.id), "entity_id": str(a.entity_id) if a.entity_id else None,
            "entity_name": a.entity.name if a.entity else None, "rule_key": a.rule_key,
            "title": a.title, "explanation": a.explanation, "severity": a.severity,
            "status": a.status, "evidence": a.evidence, "triggered_at": a.triggered_at,
        } for a in qs[:100]])


class AlertAcknowledgeView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, alert_id):
        membership = self.get_membership(write=True)
        alert = Alert.objects.filter(id=alert_id, workspace=membership.workspace).first()
        if not alert:
            raise NotFound("Alerte introuvable.")
        alert.status = Alert.Status.ACKNOWLEDGED
        alert.acknowledged_by = request.user
        alert.save(update_fields=["status", "acknowledged_by"])
        AuditEvent.objects.create(workspace=membership.workspace, actor=request.user,
                                  action="ALERT_ACKNOWLEDGED", target_type="Alert", target_id=str(alert.id))
        return Response({"id": str(alert.id), "status": alert.status})


class AuditEventListView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = self.get_membership()
        if membership.role not in {WorkspaceMembership.Role.OWNER, WorkspaceMembership.Role.ADMIN,
                                   WorkspaceMembership.Role.ACCOUNTANT}:
            raise PermissionDenied("Accès réservé aux rôles OWNER, ADMIN et ACCOUNTANT.")
        qs = AuditEvent.objects.filter(workspace=membership.workspace).select_related("actor")[:200]
        return Response([{
            "id": str(e.id), "actor": e.actor.email, "action": e.action, "target_type": e.target_type,
            "target_id": e.target_id, "metadata": e.metadata, "created_at": e.created_at,
        } for e in qs])


class ExportFactsView(WorkspaceScopeMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        membership = self.get_membership()
        facts = MetricFact.objects.filter(workspace=membership.workspace,
                                          status=MetricFact.Status.VALIDATED).select_related("entity", "import_batch")
        entity_id = request.query_params.get("entity_id")
        if entity_id:
            facts = facts.filter(entity_id=entity_id)
        output = io.StringIO()
        writer = csv.writer(output)

        def safe_csv_text(value):
            text = "" if value is None else str(value)
            # Spreadsheet applications may interpret leading control characters
            # and formula markers as executable formulas when opening CSV files.
            probe = text.lstrip("\t\r\n ")
            return "'" + text if probe.startswith(("=", "+", "-", "@")) else text
        writer.writerow(["entity", "metric_key", "value", "currency", "unit", "period_start", "period_end",
                         "source_file", "source_row", "source_column", "transformation_rule", "collected_at"])
        for fact in facts.iterator(chunk_size=1000):
            writer.writerow([safe_csv_text(fact.entity.name), safe_csv_text(fact.metric_key), fact.value,
                             safe_csv_text(fact.currency), safe_csv_text(fact.unit), fact.period_start,
                             fact.period_end, safe_csv_text(fact.import_batch.original_filename), fact.source_row,
                             safe_csv_text(fact.source_column), safe_csv_text(fact.transformation_rule),
                             fact.collected_at.isoformat()])
        response = HttpResponse("\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="yfen-validated-facts.csv"'
        response["Cache-Control"] = "no-store"
        return response
