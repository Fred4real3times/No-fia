# Architecture technique YFEN

## Décision

**Monolithe modulaire Django + traitements différés**, exposé par API REST, avec un frontend React/TypeScript PWA. Pas de microservices au MVP. Les frontières métier sont matérialisées par des applications Django afin de conserver un faible coût d'exploitation et de pouvoir extraire un service plus tard si la charge le justifie.

## Vue de déploiement

```text
Android / Chrome mobile / navigateur desktop
                 |
        React + TypeScript + Vite
        PWA shell / IndexedDB futur
                 | HTTPS / JSON + multipart
                 v
       Django + Django REST Framework
  Auth | Workspace | Portfolio | Imports | KPI
      Actions | Alertes | Audit | Exports
          |             |             |
          v             v             v
      PostgreSQL      Redis       Stockage fichiers
      données métier  jobs futurs  quarantaine privée
          |             |
          +------ Celery (P1 / parsing lourd) ------+
                                      |
                            adaptateur LLM (P1)
                   contexte structuré, pas de SQL libre
```

## Modules Django

| Application | Responsabilité |
| --- | --- |
| `identity` | Identité, mot de passe, email unique et token d’accès. |
| `tenancy` | Workspaces, memberships, entités juridiques et unités opérationnelles. |
| `sources` | Lots de fichiers, faits métriques, provenance et anomalies de validation. |
| `actions` | Actions, responsable, priorité, statut, commentaires et preuves. |
| `alerts` | Alertes générées par des règles déterministes. |
| `audit` | Événements d’audit append-only au niveau modèle. |
| `api` | Auth, permissions tenant, sérialisation, endpoints, agrégats et exports. |

## Flux d’import P0 implémenté

1. L’utilisateur choisit le workspace, l’entité, la famille de rapport, la période et la devise.
2. L’API vérifie le rôle, la limite de taille (10 Mo), l’extension, la signature XLSX/PDF et les premiers octets du CSV.
3. Le fichier original est stocké dans le répertoire privé de quarantaine ; son SHA-256 est conservé et un doublon dans le workspace est rejeté.
4. L’aperçu CSV/XLSX présente les colonnes et dix lignes maximum. Pour un PDF, l’extraction textuelle est une aide de lecture ; elle ne crée pas de faits.
5. L’utilisateur choisit explicitement la colonne du montant et, en option, la colonne de date.
6. Les lignes sont analysées en `MetricFact.REVIEW`. Les lignes non conformes produisent des `ValidationIssue`.
7. Une confirmation explicite fait passer les faits de `REVIEW` à `VALIDATED` et le lot à `VALIDATED` dans une transaction. Seuls les faits validés sont exposés dans le cockpit.

### Familles de métriques agrégées

- `SALES` → `reported_revenue`
- `CASH` → `reported_collections`
- `BANK` → `reported_cash_balance`
- `EXPENSES` → `reported_expenses`
- `RECEIVABLES` → `reported_receivables`
- `PAYABLES` → `reported_payables`

La somme est effectuée par le backend avec `Decimal`. Dans la vue portefeuille, les faits ne sont agrégés qu’à métrique, période, devise et unité identiques ; les devises et périodes différentes restent séparées. Dans une vue entité, le filtre cible une seule entité. Le total portefeuille est un total arithmétique des données rapportées : aucune élimination des opérations intragroupe ni consolidation comptable n’est réalisée. Les taux de change ne sont pas appliqués automatiquement.

## Contrôle multi-tenant

Chaque endpoint métier reçoit un `workspace_id` puis résout un membership actif côté serveur. Les queryset sont filtrés par workspace ; les relations (entité, responsable) sont revalidées contre le même workspace dans les serializers. Un UUID difficile à deviner n'est jamais considéré comme une autorisation.

Rôles initiaux : `OWNER`, `ADMIN`, `ACCOUNTANT`, `MANAGER`, `VIEWER`. Le frontend masque certains contrôles selon le rôle, mais la permission décisive demeure dans l'API.

## Frontend

- React 19 + TypeScript, Vite 8.
- Navigation mobile et desktop dans un seul projet responsive.
- Le token d’accès est gardé dans `sessionStorage`, non dans `localStorage`.
- Le service worker ne met en cache que le shell statique et ne met jamais en cache `/api/` ou des réponses financières.
- Les montants affichés sont formatés dans le navigateur ; les sommes financières et agrégats restent calculés par le backend. Les agrégats portefeuille sont des totaux arithmétiques explicitement signalés comme non retraités intragroupe.
- Le menu Assistant IA est volontairement verrouillé P1.

## Dépendances structurantes

| Couche | Technologie | Usage |
| --- | --- | --- |
| API | Django 6.1.3 + DRF 3.18.3 | Auth, ORM, permissions, REST et admin. |
| Base | PostgreSQL 17 (Docker) | Données métier et transactions. SQLite est disponible en mode développement local. |
| Fichiers | Django Storage privé | Fichiers sources conservés hors des réponses publiques. |
| Tableurs | openpyxl | Lecture XLSX en mode lecture seule et `data_only`. |
| PDF | pdfplumber | Extraction textuelle assistée, sans OCR. |
| Jobs futurs | Celery + Redis | Parsing lourd, briefs et notifications asynchrones après le P0. |
| Frontend | React 19.3.0, TypeScript 5.9, Vite 8.3 | PWA responsive. |

## Limites d’architecture à traiter avant pilote payant

- Générer, relire et committer les migrations initiales ; le scaffold actuel permet un bootstrap de développement mais ne doit pas lancer `makemigrations` en production.
- Déplacer le parsing des fichiers vers un worker isolé avec quotas CPU/mémoire, et ajouter scan antivirus/quarantaine opérationnelle.
- Activer MFA, rotation/expiration des tokens et sessions révocables par appareil.
- Configurer un stockage objet S3 privé chiffré, des liens temporaires, la politique de rétention et la restauration.
- Ajouter observabilité, alertes d’exploitation et tests de charge p95.
