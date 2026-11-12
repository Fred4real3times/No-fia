# Contribuer à YFEN

## Principes de développement

- Lire le PRD et l'architecture avant de modifier un flux métier.
- Conserver le monolithe modulaire ; pas de microservices sans ADR et besoin mesuré.
- Toute lecture ou écriture métier doit être bornée au workspace côté serveur.
- Les KPI sont calculés côté backend avec des types décimaux ; pas d'agrégation financière dans le navigateur ni dans le LLM.
- Les fichiers importés sont non fiables et ne doivent jamais exécuter macros, formules, liens ou scripts.
- Toute métrique publiée doit garder une provenance, période, devise/unité, date et version de transformation.
- Une action sensible exige une confirmation humaine habilitée.

## Avant une pull request

Backend :

```bash
cd backend
ruff check .
python manage.py check
pytest -q
```

Frontend :

```bash
cd frontend
npm install
npm run build
```

## Migrations Django

Les apps du scaffold ne contiennent pas encore de migrations initiales commitées. L'entrypoint local génère temporairement le schéma pour faciliter le premier démarrage. Avant d'ajouter une fonctionnalité ou de préparer un environnement durable :

```bash
cd backend
python manage.py makemigrations identity tenancy sources actions alerts audit
python manage.py migrate
```

Vérifier et committer les migrations générées avec le changement de modèles. Ne jamais générer des migrations à la volée en production. Une étape de hardening doit supprimer `makemigrations` de l'entrypoint et appliquer uniquement les migrations versionnées.

## Données de test

N'utiliser que des données synthétiques ou anonymisées autorisées. Ne jamais committer `.env`, des fichiers bancaires réels, des médias ou des sauvegardes.
