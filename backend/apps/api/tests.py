from datetime import date
from decimal import Decimal
import pytest
from rest_framework.test import APIClient
from apps.identity.models import User
from apps.tenancy.models import Workspace, WorkspaceMembership, LegalEntity
from apps.sources.models import ImportBatch, MetricFact

@pytest.mark.django_db
def test_workspace_creation_assigns_owner_and_scopes_entity_access():
    user = User.objects.create_user(username="owner", email="owner@example.test", password="a-secure-test-password-123")
    other = User.objects.create_user(username="other", email="other@example.test", password="another-secure-password-123")
    client = APIClient(); client.force_authenticate(user=user)
    response = client.post("/api/v1/workspaces/", {"name":"Groupe pilote", "default_currency":"XAF"}, format="json")
    assert response.status_code == 201
    workspace_id = response.data["id"]
    assert WorkspaceMembership.objects.get(workspace_id=workspace_id, user=user).role == "OWNER"
    own = client.post("/api/v1/entities/?workspace_id=" + workspace_id, {"name":"Distribution SARL", "code":"DIST", "functional_currency":"XAF"}, format="json")
    assert own.status_code == 201
    client.force_authenticate(user=other)
    denied = client.get("/api/v1/entities/?workspace_id=" + workspace_id)
    assert denied.status_code == 403

@pytest.mark.django_db
def test_cockpit_only_returns_validated_facts_and_keeps_currencies_separate():
    user = User.objects.create_user(username="u", email="u@example.test", password="a-secure-test-password-123")
    workspace = Workspace.objects.create(name="Test", owner=user)
    WorkspaceMembership.objects.create(workspace=workspace, user=user, role="OWNER")
    entity = LegalEntity.objects.create(workspace=workspace, name="Entity", code="ENT", functional_currency="XAF")
    batch = ImportBatch.objects.create(workspace=workspace, entity=entity, original_filename="sales.csv", sha256="a"*64, size_bytes=10, detected_mime="text/csv", period_start=date(2026,1,1), period_end=date(2026,1,31), currency="XAF", uploaded_by=user)
    # No file payload is needed for fact aggregation; use a placeholder FileField name.
    batch.file.name = "quarantine/test.csv"; batch.save(update_fields=["file"])
    from django.utils import timezone
    MetricFact.objects.create(workspace=workspace, entity=entity, import_batch=batch, metric_key="reported_revenue", value=Decimal("1000.00"), currency="XAF", period_start=date(2026,1,1), period_end=date(2026,1,31), collected_at=timezone.now(), transformation_rule="sales-v1", status="VALIDATED")
    MetricFact.objects.create(workspace=workspace, entity=entity, import_batch=batch, metric_key="reported_revenue", value=Decimal("250.00"), currency="XAF", period_start=date(2026,1,1), period_end=date(2026,1,31), collected_at=timezone.now(), transformation_rule="sales-v1", status="REVIEW")
    second_entity = LegalEntity.objects.create(workspace=workspace, name="Entity 2", code="ENT2", functional_currency="XAF")
    second_batch = ImportBatch.objects.create(workspace=workspace, entity=second_entity, original_filename="sales-2.csv", sha256="b"*64, size_bytes=10, detected_mime="text/csv", period_start=date(2026,1,1), period_end=date(2026,1,31), currency="XAF", uploaded_by=user)
    second_batch.file.name = "quarantine/test-2.csv"; second_batch.save(update_fields=["file"])
    MetricFact.objects.create(workspace=workspace, entity=second_entity, import_batch=second_batch, metric_key="reported_revenue", value=Decimal("200.00"), currency="XAF", period_start=date(2026,1,1), period_end=date(2026,1,31), collected_at=timezone.now(), transformation_rule="sales-v1", status="VALIDATED")
    client = APIClient(); client.force_authenticate(user=user)
    response = client.get(f"/api/v1/cockpit/?workspace_id={workspace.id}")
    assert response.status_code == 200
    assert len(response.data["metrics"]) == 1
    assert response.data["metrics"][0]["value"] == "1200.000000"
    assert response.data["metrics"][0]["entity_count"] == 2
    assert set(response.data["metrics"][0]["entity_names"]) == {"Entity", "Entity 2"}
    assert len(response.data["metrics"][0]["sources"]) == 2
    scoped = client.get(f"/api/v1/cockpit/?workspace_id={workspace.id}&entity_id={entity.id}")
    assert scoped.status_code == 200
    assert scoped.data["metrics"][0]["value"] == "1000.000000"
    assert scoped.data["metrics"][0]["entity_count"] == 1

@pytest.mark.django_db

def test_csv_import_requires_human_confirmation_before_cockpit_publication(tmp_path, settings):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from apps.alerts.models import Alert

    settings.MEDIA_ROOT = tmp_path
    user = User.objects.create_user(
        username="pilot-owner", email="pilot-owner@example.test", password="secure-test-password-123"
    )
    workspace = Workspace.objects.create(name="Pilote Douala", owner=user)
    WorkspaceMembership.objects.create(workspace=workspace, user=user, role="OWNER")
    entity = LegalEntity.objects.create(
        workspace=workspace, name="Distribution pilote", code="DIST", functional_currency="XAF"
    )
    client = APIClient()
    client.force_authenticate(user=user)

    # A newly created active entity must produce a visible, explainable missing-report alert.
    alerts_url = f"/api/v1/alerts/?workspace_id={workspace.id}&evaluate=true"
    first_alerts = client.get(alerts_url)
    assert first_alerts.status_code == 200
    assert any(a["rule_key"] == f"MISSING_FIRST_REPORT:{entity.id}" for a in first_alerts.data)
    client.get(alerts_url)
    assert Alert.objects.filter(workspace=workspace, rule_key=f"MISSING_FIRST_REPORT:{entity.id}").count() == 1

    csv_payload = (
        "Date;Montant\n"
        "2026-11-01;150000\n"
        "2026-11-02;250000\n"
        "2026-11-03;montant-invalide\n"
    ).encode("utf-8")
    upload = SimpleUploadedFile("ventes.csv", csv_payload, content_type="text/csv")
    create = client.post(
        f"/api/v1/imports/?workspace_id={workspace.id}",
        {
            "file": upload,
            "entity": str(entity.id),
            "report_type": "SALES",
            "period_start": "2026-11-01",
            "period_end": "2026-11-30",
            "currency": "XAF",
        },
        format="multipart",
    )
    assert create.status_code == 201, create.data
    batch_id = create.data["id"]

    preview = client.post(f"/api/v1/imports/{batch_id}/preview/?workspace_id={workspace.id}", {}, format="json")
    assert preview.status_code == 200, preview.data
    assert preview.data["row_count"] == 3
    assert preview.data["suggested_mapping"]["amount"] == "Montant"

    stage = client.post(
        f"/api/v1/imports/{batch_id}/stage/?workspace_id={workspace.id}",
        {"mapping": {"amount": "Montant", "date": "Date"}},
        format="json",
    )
    assert stage.status_code == 200, stage.data
    assert stage.data["rows_staged"] == 2
    assert stage.data["rows_rejected"] == 1

    cockpit_before = client.get(f"/api/v1/cockpit/?workspace_id={workspace.id}")
    assert cockpit_before.status_code == 200
    assert cockpit_before.data["metrics"] == []

    confirm = client.post(f"/api/v1/imports/{batch_id}/confirm/?workspace_id={workspace.id}", {}, format="json")
    assert confirm.status_code == 200, confirm.data
    assert confirm.data["facts_published"] == 2

    cockpit_after = client.get(f"/api/v1/cockpit/?workspace_id={workspace.id}")
    assert cockpit_after.status_code == 200
    assert len(cockpit_after.data["metrics"]) == 1
    assert cockpit_after.data["metrics"][0]["value"] == "400000.000000"
    assert cockpit_after.data["metrics"][0]["coverage"] == "partial"

    refreshed_alerts = client.get(alerts_url)
    assert refreshed_alerts.status_code == 200
    missing = Alert.objects.get(workspace=workspace, rule_key=f"MISSING_FIRST_REPORT:{entity.id}")
    assert missing.status == Alert.Status.RESOLVED


@pytest.mark.django_db
def test_bank_statement_publishes_latest_closing_balance_not_sum(tmp_path, settings):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from apps.sources.models import MetricFact

    settings.MEDIA_ROOT = tmp_path
    user = User.objects.create_user(
        username="bank-owner", email="bank-owner@example.test", password="secure-test-password-123"
    )
    workspace = Workspace.objects.create(name="Portefeuille banque", owner=user)
    WorkspaceMembership.objects.create(workspace=workspace, user=user, role="OWNER")
    entity = LegalEntity.objects.create(
        workspace=workspace, name="Entité bancaire", code="BANK", functional_currency="XAF"
    )
    client = APIClient()
    client.force_authenticate(user=user)
    file = SimpleUploadedFile(
        "solde-banque.csv",
        "Date;Solde de clôture\n2026-11-01;1200000\n2026-11-02;1450000\n2026-11-03;1325000\n".encode("utf-8"),
        content_type="text/csv",
    )
    created = client.post(
        f"/api/v1/imports/?workspace_id={workspace.id}",
        {
            "file": file,
            "entity": str(entity.id),
            "report_type": "BANK",
            "period_start": "2026-11-01",
            "period_end": "2026-11-03",
            "currency": "XAF",
        },
        format="multipart",
    )
    assert created.status_code == 201, created.data
    batch_id = created.data["id"]
    preview = client.post(
        f"/api/v1/imports/{batch_id}/preview/?workspace_id={workspace.id}", {}, format="json"
    )
    assert preview.status_code == 200, preview.data
    assert preview.data["suggested_mapping"]["amount"] == "Solde de clôture"
    assert "dernière date" in preview.data["mapping_note"]

    stage = client.post(
        f"/api/v1/imports/{batch_id}/stage/?workspace_id={workspace.id}",
        {"mapping": {"amount": "Solde de clôture", "date": "Date"}},
        format="json",
    )
    assert stage.status_code == 200, stage.data
    assert stage.data["rows_staged"] == 1
    staged = MetricFact.objects.get(import_batch_id=batch_id)
    assert staged.value == Decimal("1325000.000000")
    assert staged.period_start == date(2026, 11, 3)
    assert staged.transformation_rule.startswith("latest-closing-balance:")

    confirmed = client.post(
        f"/api/v1/imports/{batch_id}/confirm/?workspace_id={workspace.id}", {}, format="json"
    )
    assert confirmed.status_code == 200, confirmed.data
    cockpit = client.get(f"/api/v1/cockpit/?workspace_id={workspace.id}")
    assert cockpit.status_code == 200
    assert cockpit.data["metrics"][0]["metric_key"] == "reported_cash_balance"
    assert cockpit.data["metrics"][0]["value"] == "1325000.000000"


def test_xlsx_parser_rejects_formula_cells(tmp_path):
    from openpyxl import Workbook
    from apps.api.data_services import read_tabular_file

    path = tmp_path / "formula.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Date", "Montant"])
    sheet.append(["2026-11-01", "=1+1"])
    workbook.save(path)
    workbook.close()

    with pytest.raises(ValueError, match="formules"):
        read_tabular_file(str(path), path.name)


def test_negative_bank_closing_balance_is_supported_but_other_amounts_remain_nonnegative():
    from decimal import InvalidOperation
    from apps.api.data_services import parse_decimal

    assert parse_decimal("-125000", allow_negative=True) == Decimal("-125000.000000")
    with pytest.raises(InvalidOperation):
        parse_decimal("-125000")
