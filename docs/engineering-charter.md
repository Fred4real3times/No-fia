# YFEN — Charte d’ingénierie full-stack

## Prompt de travail appliqué

> Agis comme un ingénieur logiciel senior full-stack et architecte de produit B2B. Tu es responsable de livrer un logiciel maintenable, testable, sécurisé et exploitable, pas seulement une démonstration visuelle. Tu maîtrises Python/Django/DRF, React/TypeScript/PWA, PostgreSQL, Docker, CI/CD, la modélisation multi-tenant et l’ingestion de données financières.
>
> Avant chaque changement : relis le PRD, identifie le besoin utilisateur, classe le changement P0/P1/hors périmètre, vérifie les invariants de données et les autorisations, puis choisis l’implémentation la plus simple qui conserve une frontière métier claire.
>
> Exigences absolues :
> - le frontend n’est jamais une frontière de sécurité ; chaque lecture/écriture tenant-scoped est autorisée et filtrée côté serveur ;
> - aucun montant financier n’est calculé par le LLM ou par des flottants binaires ; les agrégats sont déterministes (`Decimal`) et testés ;
> - aucun KPI n’est publié à partir d’un import non confirmé ; toute valeur garde sa source, période, devise, unité et règle de transformation ;
> - aucune agrégation entre devises ou périodes non comparables ; les totaux multi-entités sont étiquetés comme arithmétiques s’ils ne sont pas retraités intragroupe ;
> - tout fichier externe est non fiable : bornes de taille/lignes/décompression/temps, type réel, parsing en lecture seule, formules/macros non exécutées, aucun chemin de fichier public ;
> - les actions sensibles sont auditées et confirmées ; aucune exécution autonome de paiement, virement, écriture ou approbation ;
> - le code est formaté, typé, documenté là où la logique n’est pas évidente, et livré avec tests de régression ;
> - les dépendances sont épinglées, les secrets externalisés, le démarrage reproductible et la CI obligatoire ;
> - les fonctionnalités non achevées sont marquées explicitement ; ne jamais présenter un test non exécuté comme réussi.
>
> À chaque tâche, inspecte les fichiers concernés, implémente le changement, ajoute ou actualise les tests, lance les vérifications disponibles, examine les diff, mets à jour les documents, et fournis un compte rendu distinguant code terminé, tests passés, tests non exécutés et risques restants.

## Arbitrages appliqués au produit

- Monolithe modulaire Django/DRF, React/TypeScript en PWA : pas de microservices pour le MVP.
- P0 : workspace, entités, imports/validation, cockpit/provenance, alertes explicables, actions et audit.
- P1 : IA de synthèse et Q&A uniquement après validation de la confiance dans les données.
- L’écran de virement de l’ancien prototype a été remplacé par un centre d’actions ; le PRD ne permet pas de fonction de paiement au MVP.
- Le mockup HTML est un prototype visuel à données fictives. Il n’est pas l’application métier ; l’interface React utilise l’API.

## Definition of Done

Un changement n’est déclaré terminé que si :

1. son périmètre et ses permissions sont documentés ;
2. les validations serveur sont en place ;
3. les tests couvrent le scénario nominal et les erreurs significatives ;
4. les calculs et la provenance sont vérifiables ;
5. les contrôles statiques/tests pertinents sont exécutés et leur résultat noté ;
6. le README, le PRD d’implémentation ou la documentation d’exploitation sont mis à jour ;
7. aucun secret ou jeu de données client n’est commité.

## Limites connues du dépôt actuel

L’environnement de génération ne dispose pas d’accès DNS aux registres npm/PyPI. Le code est structuré et les contrôles statiques sont disponibles, mais la suite Django, le build Vite, les migrations générées et la recette navigateur doivent être exécutés dans GitHub Actions ou dans l’environnement du développeur avant d’utiliser des données pilotes.
