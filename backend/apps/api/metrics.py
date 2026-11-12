from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone

from apps.actions.models import ActionItem
from apps.alerts.models import Alert
from apps.sources.models import ImportBatch, MetricFact

METRIC_LABELS = {
    "reported_revenue": "Chiffre d’affaires rapporté",
    "reported_collections": "Encaissements rapportés",
    "reported_cash_balance": "Solde de trésorerie déclaré",
    "reported_expenses": "Dépenses rapportées",
    "reported_receivables": "Créances clients",
    "reported_payables": "Dettes fournisseurs",
    "reported_other_amount": "Autre montant rapporté",
}


def build_cockpit(workspace, entity_id=None):
    facts = MetricFact.objects.filter(
        workspace=workspace, status=MetricFact.Status.VALIDATED
    ).select_related("entity", "import_batch")
    if entity_id:
        facts = facts.filter(entity_id=entity_id)

    # Portfolio metrics aggregate only like-for-like facts: identical metric,
    # currency, unit and reporting period. They are arithmetic sums, not
    # consolidated financial statements: no intra-group elimination is done.
    grouped = defaultdict(lambda: {
        "value": Decimal("0"), "count": 0, "latest": None, "sources": {}, "entities": {}
    })
    for fact in facts.iterator(chunk_size=500):
        key = (fact.metric_key, fact.currency or "", fact.unit, fact.period_start, fact.period_end)
        target = grouped[key]
        target["value"] += fact.value
        target["count"] += 1
        target["latest"] = max(target["latest"], fact.collected_at) if target["latest"] else fact.collected_at
        target["entities"][str(fact.entity_id)] = fact.entity.name
        target["sources"][str(fact.import_batch_id)] = {
            "id": str(fact.import_batch_id),
            "file": fact.import_batch.original_filename,
            "created_at": fact.import_batch.created_at,
            "rows_rejected": fact.import_batch.rows_rejected,
        }

    metrics = []
    for (key, currency, unit, start, end), data in grouped.items():
        entity_ids = list(data["entities"].keys())
        entity_names = list(data["entities"].values())
        metrics.append({
            "metric_key": key,
            "label": METRIC_LABELS.get(key, key),
            "value": str(data["value"]),
            "currency": currency,
            "unit": unit,
            "period_start": start,
            "period_end": end,
            "entity_id": entity_ids[0] if len(entity_ids) == 1 else None,
            "entity_ids": entity_ids,
            "entity_names": entity_names,
            "entity_count": len(entity_ids),
            "fact_count": data["count"],
            "last_collected_at": data["latest"],
            "sources": list(data["sources"].values()),
            "coverage": "partial" if any(source.get("rows_rejected", 0) for source in data["sources"].values()) else "complete",
        })
    metrics.sort(key=lambda item: (item["metric_key"], item["currency"], item["period_start"], item["entity_count"]))
    validated = ImportBatch.objects.filter(workspace=workspace, status=ImportBatch.Status.VALIDATED).order_by("-validated_at")
    if entity_id:
        validated = validated.filter(entity_id=entity_id)
    latest = validated.values("id", "original_filename", "report_type", "validated_at")[:1]
    return {
        "workspace_id": str(workspace.id),
        "generated_at": timezone.now(),
        "metrics": metrics,
        "latest_validated_import": list(latest),
        "open_actions": ActionItem.objects.filter(workspace=workspace).exclude(status__in=[ActionItem.Status.DONE, ActionItem.Status.CANCELLED]).count(),
        "overdue_actions": ActionItem.objects.filter(workspace=workspace, due_at__lt=timezone.now()).exclude(status__in=[ActionItem.Status.DONE, ActionItem.Status.CANCELLED]).count(),
    }


def evaluate_workspace_alerts(workspace):
    """Evaluate explainable rules and avoid recreating acknowledged alerts."""
    now = timezone.now()
    created = []

    def create_once(*, rule_key, entity, title, explanation, severity, evidence):
        existing = Alert.objects.filter(workspace=workspace, rule_key=rule_key).exclude(
            status=Alert.Status.RESOLVED
        ).first()
        if existing:
            return
        alert = Alert.objects.create(
            workspace=workspace, entity=entity, rule_key=rule_key, title=title,
            explanation=explanation, severity=severity, evidence=evidence,
        )
        created.append(alert)

    overdue = ActionItem.objects.filter(workspace=workspace, due_at__lt=now).exclude(
        status__in=[ActionItem.Status.DONE, ActionItem.Status.CANCELLED]
    )
    active_overdue_keys = set()
    for action in overdue.select_related("entity")[:200]:
        rule_key = f"OVERDUE_ACTION:{action.id}"
        active_overdue_keys.add(rule_key)
        create_once(
            rule_key=rule_key,
            entity=action.entity,
            title=f"Action en retard : {action.title[:120]}",
            explanation=f"L’échéance de cette action était fixée au {action.due_at:%d/%m/%Y %H:%M}.",
            severity=Alert.Severity.WARNING if action.priority != ActionItem.Priority.CRITICAL else Alert.Severity.CRITICAL,
            evidence={"action_id": str(action.id), "due_at": action.due_at.isoformat(), "status": action.status},
        )
    # Close alerts whose action is no longer overdue or has been completed/cancelled.
    stale_action_alerts = Alert.objects.filter(workspace=workspace, rule_key__startswith="OVERDUE_ACTION:",
                                               status__in=[Alert.Status.OPEN, Alert.Status.ACKNOWLEDGED])
    for alert in stale_action_alerts:
        if alert.rule_key not in active_overdue_keys:
            alert.status = Alert.Status.RESOLVED
            alert.save(update_fields=["status"])

    stale_before = now - timedelta(days=30)
    for entity in workspace.entities.filter(status="ACTIVE"):
        latest = ImportBatch.objects.filter(
            workspace=workspace, entity=entity, status=ImportBatch.Status.VALIDATED
        ).order_by("-validated_at").first()
        if latest is None:
            create_once(
                rule_key=f"MISSING_FIRST_REPORT:{entity.id}", entity=entity,
                title=f"Aucun rapport validé — {entity.name}",
                explanation="Aucun lot de données n’a encore été confirmé pour cette entité.",
                severity=Alert.Severity.WARNING,
                evidence={"entity_id": str(entity.id), "required_action": "Importer un rapport et confirmer les lignes valides"},
            )
        elif latest.validated_at and latest.validated_at < stale_before:
            create_once(
                rule_key=f"STALE_REPORTING:{entity.id}", entity=entity,
                title=f"Données anciennes — {entity.name}",
                explanation="Aucun import validé n’a été reçu pour cette entité au cours des 30 derniers jours.",
                severity=Alert.Severity.WARNING,
                evidence={"last_validated_at": latest.validated_at.isoformat(), "days_threshold": 30},
            )
        else:
            Alert.objects.filter(workspace=workspace, entity=entity,
                                 rule_key__in=[f"MISSING_FIRST_REPORT:{entity.id}", f"STALE_REPORTING:{entity.id}"],
                                 status__in=[Alert.Status.OPEN, Alert.Status.ACKNOWLEDGED]).update(status=Alert.Status.RESOLVED)
    return created
