# Roadmap produit et technique

La roadmap conserve la séquence de 12 semaines du PRD, mais les semaines ne constituent pas une promesse de livraison. Le travail dépend de la disponibilité de dirigeants pilotes et d’exemples de fichiers autorisés.

| Phase | Objectif | Livrable | Gate de sortie |
| --- | --- | --- | --- |
| S1–S2 | Découverte | 15–20 entretiens, choix d’un sous-segment, rapports types, dictionnaire KPI. | 5 dirigeants acceptent de tester sur leurs propres rapports. |
| S3–S4 | Fondations | Multi-tenant, auth, rôles, audit, design system, tests d’isolation, migrations versionnées. | Onboarding et tests d’accès passés. |
| S5–S6 | Import & qualité | CSV/XLSX, PDF textuel assisté, mapping, validation, REVIEW, historique et provenance. | Imports reproductibles sur rapports de pilote et cas d’erreur expliqués. |
| S7–S8 | Pilotage | Vue portefeuille/entité, KPI simples, fraîcheur, alertes par règles et centre d’actions. | Chaque valeur possède sa source et les dirigeants comprennent les alertes. |
| S9–S10 | IA & mobile | Executive Brief, Q&A structuré, brouillons vocaux, cache lecture seule, notifications. | Réponses évaluées, aucune action sensible autonome et coûts suivis. |
| S11–S12 | Hardening & pilote | Sécurité, performance, restauration, onboarding et mesure de la valeur. | Décision Go / Pivot / No-Go basée sur usage et volonté de payer. |

## Prochain sprint technique recommandé

1. Générer et committer les migrations Django initiales ; retirer le bootstrap de schéma non versionné.
2. Ajouter les tests d’isolation pour chaque endpoint, les scénarios d’import, la validation et la confirmation.
3. Tester un corpus CSV/XLSX réel anonymisé avec l’expert-comptable pilote.
4. Compléter l’export complet, les commentaires/preuves d’action et les permissions membres.
5. Déployer un environnement de staging, PostgreSQL, stockage privé, secrets, monitoring et exercices de restauration.

## Décisions produit non négociables

- Pas de virement, paiement, banque temps réel ni agrégateur Mobile Money au MVP.
- Pas d’ERP, comptabilité officielle, paie, POS ou OCR massif.
- Pas de métrique agrégée entre devises différentes sans taux, date, source et règle documentés.
- Le P1 IA attend la validation des imports, du dictionnaire KPI et de la provenance.
