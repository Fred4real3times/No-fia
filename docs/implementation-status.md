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
| CI | Validée sur GitHub Actions | Sur `main` : migrations générées puis appliquées sur PostgreSQL 17, `manage.py check`, Ruff et 6 tests backend passés sous Python 3.12 et 3.13 ; type-check TypeScript et build Vite passés sous Node 22. Les migrations générées ne sont pas encore versionnées. |
| Déploiement | Dev | Docker Compose PostgreSQL/Redis/API/Frontend préparé. Pas d’environnement de production, de sauvegardes testées ou de SLA. |

## Validation locale observée pendant la génération

**Contrôles exécutés et passés :**
- Compilation syntaxique Python : `py_compile` sur les modules backend.
- Smoke tests des parseurs : CSV, conversion Decimal, dates, rejet des cellules XLSX contenant des formules et autorisation contrôlée des soldes bancaires négatifs.
- Syntaxe JavaScript du mockup : `node --check` sur les scripts extraits.
- Analyse syntaxique TypeScript/TSX : `typescript.transpileModule` sans diagnostic syntaxique pour `App.tsx`, `api.ts`, `main.tsx` et `vite.config.ts` (ce contrôle ne remplace pas un type-check).
- Rendu Chromium du mockup : six écrans détectés et captures PNG générées. Il s’agit du mockup HTML, pas d’une session de l’application React connectée.
- `git diff --check` : passé ; dépôt local propre après commit.

**Contrôles non exécutés localement / restant à faire :**
- Installation des dépendances Python, Django/DRF et npm sur cet environnement local : registres inaccessibles par DNS. Les installations correspondantes ont en revanche réussi dans la CI GitHub.
- Recette navigateur de l’application React réellement connectée à l’API, avec parcours multi-utilisateur et fichiers métier représentatifs.
- Durcissement des migrations : les migrations initiales sont générées à la volée dans le job CI pour valider le scaffold ; elles doivent être relues, commitées et contrôlées sur une base vierge.
- Revue indépendante de sécurité, tests approfondis d’isolation multi-tenant/RBAC, sauvegarde/restauration et exécution Docker complète.

La CI verte valide le build frontend et le socle de tests actuel ; elle ne constitue ni une recette fonctionnelle exhaustive ni une autorisation de pilote client. Aucun déploiement non éphémère ni chargement de données financières réelles n’est recommandé à ce stade.
