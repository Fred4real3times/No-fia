# État d’implémentation — YFEN v0.1.0

Mise à jour : 12 novembre 2026.

| Domaine | État | Détail |
| --- | --- | --- |
| Auth | Partiel implémenté | Inscription, connexion par email/mot de passe, token API, `/me`, logout. MFA et cycle de vie avancé du token absents. |
| Workspace & memberships | Partiel implémenté | Création workspace + OWNER, liste des espaces, ajout d’un compte existant à un workspace. Invitations email et gestion complète des rôles à finir. |
| Entités / unités | Implémenté en base API | Création/liste entité et unité ; archivage, édition et périmètre fin par unité à finir. |
| Import CSV/XLSX | Parcours MVP implémenté | Upload quarantaine, SHA-256, preview, mapping montant/date, faits REVIEW, anomalies et confirmation explicite. Les relevés bancaires exigent un solde de clôture daté (valeur la plus récente, sans somme des mouvements). À tester sur des fichiers métiers réels. |
| PDF textuel | Partiel | Extraction de texte pour lecture assistée ; pas de structuration automatique, pas d’OCR. |
| KPI | Socle implémenté | Agrégation Decimal de faits validés, séparée par entité, période et devise, avec provenance. Dictionnaire métier et règles d’exhaustivité à valider. |
| Alertes | Partiel | Règles pour actions en retard et imports anciens. Alertes reporting manquant/variation seuil à étendre et tester. |
| Centre d’actions | Socle implémenté | Création, assignation à un membre, priorité, échéance, statuts et commentaires API. Preuves et historique détaillé à finir. |
| Audit | Partiel | Journal de lecture append-only au niveau modèle, événements de base. Protection externe et couverture de toutes les mutations à compléter. |
| Frontend | MVP de travail | React responsive, login/register, workspace, entreprises, imports, cockpit, actions, analyse, paramètres et audit. |
| PWA faible réseau | Partiel | Manifest et cache du shell seulement. Aucun cache de données financières ; brouillons offline/synchronisation et conflit pas encore implémentés. |
| Assistant IA | Non activé | Module P1 verrouillé ; aucune donnée n’est envoyée à un LLM. |
| CI | Configurée | Backend tests et frontend build prévus sous GitHub Actions. Exécution à confirmer après publication du dépôt. |
| Déploiement | Dev | Docker Compose PostgreSQL/Redis/API/Frontend préparé. Pas d’environnement de production, de sauvegardes testées ou de SLA. |

## Validation locale observée pendant la génération

**Contrôles exécutés et passés :**
- Compilation syntaxique Python : `py_compile` sur les modules backend.
- Smoke tests des parseurs : CSV, conversion Decimal, dates, rejet des cellules XLSX contenant des formules et autorisation contrôlée des soldes bancaires négatifs.
- Syntaxe JavaScript du mockup : `node --check` sur les scripts extraits.
- Analyse syntaxique TypeScript/TSX : `typescript.transpileModule` sans diagnostic syntaxique pour `App.tsx`, `api.ts`, `main.tsx` et `vite.config.ts` (ce contrôle ne remplace pas un type-check).
- Rendu Chromium du mockup : six écrans détectés et captures PNG générées. Il s’agit du mockup HTML, pas d’une session de l’application React connectée.
- `git diff --check` : passé ; dépôt local propre après commit.

**Contrôles non exécutés :**
- Installation des dépendances Python et Django/DRF : PyPI inaccessible dans cet environnement (échec DNS).
- Installation npm, type-check complet et build Vite : npm registry inaccessible.
- Suite de tests Django/API, migrations et tests PostgreSQL : non exécutés, Django/DRF et pytest-django ne sont pas installés.
- Recette navigateur de l’application React connectée à l’API et exécution Docker : non exécutées.

Ces contrôles non exécutés ne doivent pas être interprétés comme des réussites. La CI doit tourner après publication GitHub, puis les migrations doivent être générées, relues et commitées avant un déploiement non éphémère.
