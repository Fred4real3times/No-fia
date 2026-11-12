# YFEN — AI BUSINESS CONTROL TOWER

## Product Requirements Document, architecture technique et roadmap MVP
Le cockpit de pilotage multi-activités pour les dirigeants de PME et groupes en Afrique francophone.

### DÉCISION PRODUIT CENTRALE

Construire une couche de pilotage exécutif qui agrège les données existantes, signale les écarts et organise les actions. Ne pas commencer par un ERP, un logiciel comptable ou un agent IA autonome.

Version : 1.0  |  Date : 11 novembre 2026  |  Marché initial : Cameroun  |  Langue de lancement : français
Statut : proposition de cadrage à valider avec des dirigeants pilotes, un expert-comptable et un conseil juridique local.

## 0. Synthèse exécutive

YFEN (AI Business Control Tower) est une plateforme SaaS B2B qui donne à un dirigeant une vue consolidée de plusieurs entreprises, établissements ou activités, puis transforme les informations importantes en décisions et actions suivies.
Le produit ne doit pas chercher à remplacer immédiatement Excel, Sage, Odoo, les logiciels comptables locaux, les systèmes de caisse ou les outils métiers. Il doit d’abord les rendre lisibles ensemble, sans migration brutale et sans réécriture des systèmes de référence.
| Arbitrage utilisateur | Challenge | Décision produit recommandée |
| --- | --- | --- |
| Tous les dirigeants progressivement | Trop large pour le premier lancement : besoins, données et cycles de vente sont différents. | Garder une vision multi-secteurs, mais démarrer avec des dirigeants de PME qui supervisent 2 à 5 entreprises, sites ou unités, d’abord dans le commerce, la distribution et les services. |
| Cockpit centralisé | Un tableau de bord seul devient vite un écran de plus si les données sont manuelles ou périmées. | Cockpit + qualité/provenance des données + alertes + centre d’actions. La confiance dans les chiffres est la fonctionnalité principale. |
| Mobile prioritaire | Le mobile est idéal pour consulter et agir vite, mais pénible pour configurer des imports et analyser de gros tableaux. | PWA mobile-first installable, avec interface web adaptée au bureau. Ne pas financer deux applications natives au démarrage. |

### NORTH STAR METRIC

Nombre de décisions ou d’actions importantes suivies et clôturées à temps par dirigeant chaque semaine, avec données vérifiables. Ne pas optimiser seulement les ouvertures d’application.

## 1. Thèse produit et positionnement

Positionnement : « Le cockpit qui permet au dirigeant de savoir, en quelques minutes, ce qui va bien, ce qui dérape, ce qui exige son arbitrage et qui doit agir. »

### 1.1 Ce que nous construisons

• Une vue consolidée par portefeuille, entreprise, établissement et période.
• Une couche d’import et de normalisation de fichiers de gestion existants.
• Un résumé exécutif lisible, daté et relié à ses sources.
• Un centre d’actions avec responsable, échéance, statut et preuve de clôture.
• Une IA d’assistance qui explique les données autorisées et prépare des actions, sans inventer de chiffres ni exécuter seule des opérations sensibles.

### 1.2 Ce que nous ne sommes pas au MVP

• Pas un ERP complet, un logiciel de caisse, un outil de paie ou un système comptable officiel.
• Pas un service de tenue comptable, de production de DSF ou de certification SYSCOHADA.
• Pas une application de banque ou de Mobile Money et pas un agrégateur bancaire temps réel au lancement.
• Pas un agent autonome autorisé à payer, virer, valider une dépense ou modifier une écriture comptable.
• Pas un outil de prévision financière qui présente des estimations comme des certitudes.

### 1.3 Pression concurrentielle et différenciation

Le marché local compte déjà des solutions de gestion qui combinent comptabilité OHADA, paie, ventes, stocks, trésorerie, tableaux de bord, application Android et mode hors ligne. Omamori affiche publiquement des offres à 15 000 FCFA/mois et 25 000 FCFA/mois. Notre proposition ne peut donc pas être une copie plus jolie de ces fonctions. Elle doit agréger des systèmes qui restent en place, comparer plusieurs entités/outils, montrer la qualité et la fraîcheur de chaque source, puis organiser les arbitrages et les actions du dirigeant. La différenciation devra être prouvée par les usages, pas déclarée dans le marketing.

## 2. Cible, marché initial et utilisateurs

### 2.1 Vision de marché vs segment d’entrée

« Tous les dirigeants progressivement » reste une ambition de plateforme, pas une définition de client MVP. Le lancement doit viser un groupe ayant un problème commun, un accès aux données et une capacité de payer.
| Élément | Définition proposée |
| --- | --- |
| ICP initial | Propriétaire-dirigeant ou directeur général d’une PME camerounaise qui supervise 2 à 5 entreprises, points de vente, agences ou unités opérationnelles. |
| Secteurs de départ | Commerce/distribution et services B2B ; sélectionner ensuite un sous-segment selon les entretiens et les fichiers réellement disponibles. |
| Complexité cible | Environ 5 à 100 collaborateurs ou plusieurs responsables d’activité (hypothèse à valider, pas une statistique de marché). |
| Acheteur économique | Fondateur, DG, directeur administratif et financier ou responsable de groupe. |
| Utilisateurs secondaires | Comptable, contrôleur, responsable d’agence, chef d’activité, assistant de direction. |
| Déclencheur d’achat | Trop de temps à consolider les rapports ; retard de visibilité ; dépendance à un collaborateur ; absence de suivi fiable entre plusieurs activités. |

### 2.2 Personas et jobs-to-be-done

| Persona | Besoin prioritaire | Succès observable |
| --- | --- | --- |
| Dirigeant / owner | Comprendre l’état des activités sans appeler cinq personnes. | Vue de portefeuille à jour et trois priorités maximum. |
| Contrôleur / DAF | Consolider les chiffres, détecter les anomalies, documenter les écarts. | Imports traçables, rapprochement des totaux et explication des écarts. |
| Responsable d’activité | Faire remonter les informations utiles et clôturer les actions. | Saisie courte, responsabilités claires, moins de reporting répétitif. |

### 2.3 Hypothèses à tester avant le développement complet

• Le dirigeant accepte-t-il d’importer ses fichiers chaque semaine ou chaque mois ?
• Quels rapports existent réellement : ventes, caisse, banque, dépenses, créances, stocks, projets, tâches ?
• Qui est propriétaire des fichiers et qui peut autoriser leur partage ?
• Le principal coût est-il la consolidation, la détection tardive, le suivi des responsables ou la qualité des données ?
• Quel montant le client paierait-il pour une réduction mesurable du temps de pilotage ?

## 3. PRD — périmètre et exigences fonctionnelles

### 3.1 Parcours principal

1. Créer un espace de travail et ajouter une ou plusieurs entreprises/activités.
2. Importer un fichier Excel/CSV ou joindre un rapport PDF textuel.
3. Choisir le type de rapport, la période, la devise et l’entreprise concernée.
4. Prévisualiser les colonnes, faire correspondre les champs et corriger les anomalies.
5. Confirmer l’import ; seules les données validées alimentent les indicateurs.
6. Consulter le cockpit, voir la date de fraîcheur et ouvrir la source d’un indicateur.
7. Créer ou assigner une action depuis une alerte ; suivre son échéance jusqu’à clôture.
8. Recevoir un résumé exécutif et poser des questions sur les données autorisées.

### 3.2 Modules du MVP

Le noyau P0 doit déjà apporter de la valeur sans IA générative. Le résumé IA et le Q&A sont P1 : ils ne sont activés qu’après validation des imports, des KPI et de la traçabilité.
| Module | Priorité / exigences | Critères d’acceptation |
| --- | --- | --- |
| Workspace & portefeuille | P0 — Création d’espace, entreprises, activités/sites, devise et période de reporting. | Un utilisateur autorisé peut passer d’une entité à une autre ; aucune donnée d’une autre entité n’apparaît sans droit. |
| Import & data quality | P0 — CSV/XLSX ; PDF textuel en extraction assistée ; prévisualisation, mapping, validation, doublons et historique de lots. | Aucune donnée n’est publiée sans confirmation ; chaque import possède un ID, une source, un horodatage et un statut. |
| Cockpit exécutif | P0 — Vue portefeuille et vue entité : chiffre d’affaires importé, encaissements/solde de trésorerie déclaré, dépenses, créances et échéances disponibles. | Chaque KPI indique période, devise, date de dernière mise à jour, couverture et lien vers le lot source. |
| Alertes & exceptions | P0 — Règles explicites : données manquantes, retard de reporting, variation dépassant un seuil défini, échéance proche. | Chaque alerte expose la règle et les données qui l’ont déclenchée ; pas de diagnostic opaque. |
| Centre d’actions | P0 — Créer, assigner, commenter, fixer une échéance, changer le statut et joindre une preuve. | Toute action possède un responsable, un statut et un historique ; les rappels peuvent être désactivés. |
| AI Executive Brief | P1 — Résumé quotidien/hebdomadaire des faits importants et des actions en retard, après validation du noyau de données. | Chaque fait est relié à une donnée source et daté ; si les données sont insuffisantes, le système le dit. |
| Assistant Q&A limité | P1 — Questions en langage naturel sur les métriques et actions présentes dans le périmètre utilisateur. | Réponses fondées sur des requêtes structurées validées ; refus explicite si la donnée n’existe pas. |
| Administration & audit | P0 — Invitations, rôles simples, journal d’activité, export des données et fermeture de compte. | Les actions sensibles sont journalisées ; un export complet de l’espace peut être demandé. |

### 3.3 Fonctions à décaler

| Après MVP | Pourquoi |
| --- | --- |
| Connecteurs bancaires et Mobile Money en direct | Dépendances contractuelles, sécurité, autorisations et formats variables ; commencer par import de relevés. |
| Prévisions avancées et détection de fraude ML | Nécessitent des historiques propres et suffisants ainsi que des métriques validées. |
| Comptabilité, facturation, paie, stock et POS | Risque de devenir un ERP et de concurrencer frontalement des suites déjà implantées. |
| Automatisation autonome de paiements ou d’approbations | Risque opérationnel et réglementaire trop élevé pour le premier produit. |
| OCR de masse sur PDF scannés | Variabilité documentaire importante ; commencer par PDF textuels et contrôle humain. |
| Déploiement multi-pays et fiscalité multi-juridiction | Concentrer la conformité et la localisation sur le Cameroun au départ. |

## 4. Expérience utilisateur et design system

### 4.1 Navigation principale

| Écran | Question à laquelle il répond | Priorité |
| --- | --- | --- |
| Accueil / Mon portefeuille | Qu’est-ce qui mérite mon attention aujourd’hui ? | P0 |
| Entreprises | Quelle entité ou activité dois-je consulter ? | P0 |
| Données / Imports | D’où viennent les chiffres et sont-ils fiables ? | P0 |
| Actions | Qui doit faire quoi et pour quand ? | P0 |
| Assistant | Puis-je poser une question sans chercher dans cinq fichiers ? | P1, après les données fiables |
| Paramètres / Accès | Qui voit quoi et comment gérer mon espace ? | P0 |

### 4.2 Principes UX non négociables

• Vue d’ensemble courte : trois à cinq indicateurs prioritaires, puis accès au détail.
• Un vocabulaire compréhensible par un dirigeant non-comptable ; définitions disponibles pour chaque KPI.
• Une action principale par écran ; saisie vocale possible mais toujours confirmée.
• Afficher les montants dans leur devise d’origine ; ne jamais additionner XAF, USD ou EUR sans taux, date et méthode explicites.
• Afficher « dernière mise à jour » et « données partielles » au même niveau visuel que la valeur.
• Fonctionner correctement sur Android, écran étroit et connexion lente ; éviter les graphiques lourds.
• Prévoir le français en premier, architecture prête pour anglais et autres langues ultérieurement.

### 4.3 Mobile prioritaire, pas mobile exclusif

Recommandation : commencer par une PWA responsive installable sur Android. Le mobile sert à consulter, recevoir les alertes, dicter une note et traiter une action. Le navigateur desktop sert aux imports volumineux, au mapping de colonnes, à l’administration et aux rapports. Une application Android native ne sera justifiée qu’après validation des usages hors ligne, notifications, caméra ou intégrations appareil.

### MODE RÉSEAU FAIBLE

Au MVP : afficher le dernier cockpit synchronisé en lecture seule et autoriser la rédaction locale d’une note ou d’une action en brouillon. Ne pas permettre de modifier hors ligne des soldes, écritures ou KPI consolidés ; synchroniser ensuite avec contrôle des conflits.

## 5. Données, métriques et fiabilité

### 5.1 Modèle de données logique

| Objet | Champs / relations clés |
| --- | --- |
| Workspace | ID, nom, propriétaire, paramètres, plan, statut. |
| LegalEntity / BusinessUnit | Workspace ID, nom, pays, devise fonctionnelle, secteur, fuseau, entité mère éventuelle. |
| Location / Activity | Entité, type, nom, code interne, responsable. |
| User / Membership | Identité, rôle, workspace, périmètre entités autorisées, statut. |
| SourceFile / ImportBatch | Nom, type, empreinte, version, origine, auteur, date, période, statut, parser version. |
| Mapping / ValidationIssue | Correspondance colonnes, règle, ligne, valeur d’origine, correction, décision utilisateur. |
| MetricFact | Entité, métrique, valeur, devise/unité, période, date de collecte, source batch, statut de validation. |
| Alert / Action | Règle, faits déclencheurs, priorité, responsable, échéance, statut, commentaires, historique. |
| AuditEvent | Acteur, action, objet, avant/après lorsque pertinent, horodatage, adresse/session selon politique. |

### 5.2 Dictionnaire de métriques du MVP

Ne pas commencer par vingt ratios. Démarrer avec des métriques simples dont la source peut être vérifiée.
| Métrique | Définition MVP | Précaution |
| --- | --- | --- |
| Chiffre d’affaires rapporté | Somme des lignes de vente validées pour la période. | Nommer « rapporté » si les ventes ne sont pas rapprochées de la comptabilité. |
| Encaissements rapportés | Somme des encaissements présents dans le fichier importé. | Ne pas l’assimiler au chiffre d’affaires ni au solde bancaire. |
| Dépenses rapportées | Somme des dépenses catégorisées et validées. | Exclure les lignes ambiguës des agrégats ou les afficher séparément. |
| Créances clients | Montants clients restant dus selon l’état importé. | Préciser date d’arrêté et absence éventuelle de rapprochement. |
| Dettes fournisseurs | Montants fournisseurs restant dus selon l’état importé. | Même exigence de date d’arrêté et source. |
| Variation période sur période | (Valeur période courante - précédente) / valeur précédente. | Afficher N/A si base précédente nulle ou périodes non comparables. |
| Fraîcheur des données | Temps depuis le dernier import validé par famille de données. | Ne pas qualifier de temps réel une donnée importée manuellement. |

### 5.3 Règles de fiabilité des données

• Chaque chiffre affiché doit être traçable à un import, un champ source et une règle de transformation.
• Les calculs financiers sont déterministes et testés ; le modèle de langage ne calcule pas les totaux.
• Les données rejetées, ambiguës ou incomplètes restent visibles dans une file de revue, pas dans les KPI certifiés.
• Un import dupliqué ne doit pas doubler les agrégats : empreinte de fichier, période, source et détection de répétition.
• Les corrections produisent une nouvelle version et conservent l’historique ; pas de réécriture silencieuse.
• Les entités multi-devises sont affichées séparément jusqu’à ce qu’un taux documenté et une règle de consolidation soient définis.

## 6. Architecture technique recommandée

### CHOIX D’ARCHITECTURE

Monolithe modulaire + traitements asynchrones. Éviter les microservices pour le MVP : ils augmentent le coût d’exploitation avant que le modèle produit soit validé.

### 6.1 Vue logique

### UTILISATEURS

Android / navigateur mobile       Navigateur desktop
\                  /
PWA React / TypeScript
Cache local (IndexedDB) + file de brouillons
| HTTPS / API REST
Backend Django + DRF
---------------------------------------------------------
Auth & RBAC | Portefeuille | KPI | Actions | Audit | AI
Import / validation | Connecteurs futurs | Notifications
---------------------------------------------------------
|                 |                    |
PostgreSQL        Worker Celery         Stockage objet
données métier    parsing / IA / jobs    fichiers originaux
|                 |                    |
+----------- Redis / Queue -----------+
|
Fournisseur LLM abstrait
contexte structuré minimal, jamais accès SQL libre

OBSERVABILITÉ : logs structurés, métriques, alertes, suivi erreurs
EXPLOITATION : Docker, sauvegardes, CI/CD, environnements séparés

### 6.2 Stack recommandée

| Couche | Choix pragmatique | Pourquoi / limites |
| --- | --- | --- |
| Front-end | React + TypeScript + Vite, PWA responsive. | Rapide à livrer, UI mobile et desktop dans un projet ; PWA d’abord, native plus tard si nécessaire. |
| Back-end | Python + Django + Django REST Framework. | Auth, permissions, ORM, administration et écosystème d’import/data solide. |
| Base principale | PostgreSQL. | Transactions, intégrité relationnelle, rapports et isolation renforcée par politiques d’accès. |
| Jobs asynchrones | Celery + Redis. | Parsing fichiers, génération de brief, notifications et tâches longues hors requête HTTP. |
| Fichiers | Stockage objet compatible S3, chiffré, liens temporaires. | Séparer fichiers sources de la base métier ; politiques de conservation. |
| Import | Pandas/openpyxl ou parsers dédiés ; extraction PDF textuelle avec contrôle. | Ne jamais exécuter macros, scripts ou formules importées. |
| IA | Couche d’abstraction fournisseur + modèles de prompts versionnés + sortie JSON validée. | Changer de fournisseur sans réécrire la logique ; minimiser les données envoyées. |
| Observabilité | Sentry ou équivalent, logs structurés, métriques et alertes. | Mesurer erreurs d’import, latence, coût IA, incidents et synchronisation. |
| Déploiement | Docker, CI/CD, environnements dev/staging/prod, services managés si budget. | Éviter de maintenir soi-même DB/Redis/stockage au début. |

### 6.3 Architecture d’import

• Upload sécurisé et contrôle de type réel du fichier, taille et extension.
• Quarantaine/scan antivirus et stockage du fichier original immuable.
• Parsing dans un worker isolé avec limites mémoire/temps ; macros désactivées et non exécutées.
• Prévisualisation et mapping explicite vers le schéma interne.
• Validation des types, dates, devises, doublons, valeurs manquantes et totaux de contrôle.
• Confirmation par un utilisateur habilité.
• Création d’un lot de données normalisées ; provenance conservée jusqu’au KPI.
• Possibilité d’annuler logiquement un lot et recalculer les agrégats sans perdre l’audit.

### 6.4 Architecture IA sûre

Le modèle IA ne reçoit pas un accès direct à la base de données, aux fichiers bruts ou aux opérations d’écriture. Il reçoit un contexte structuré minimal, généré par des fonctions métier autorisées.
| Cas d’usage | Approche |
| --- | --- |
| Question « Quel site a le plus baissé ? » | Le système détecte l’intention, appelle un service KPI autorisé, vérifie période/devise/couverture puis formule la réponse. |
| Résumé exécutif | Le moteur de règles sélectionne les faits ; le LLM les hiérarchise et rédige un texte court avec références. |
| Créer une tâche depuis la voix | Transcription + extraction de champs + aperçu ; création seulement après confirmation. |
| Donnée manquante | L’assistant répond que le rapport n’a pas été fourni ou que la période n’est pas comparable. |
| Action financière sensible | Non autorisée au MVP ; l’IA peut préparer une suggestion, jamais exécuter. |

## 7. Sécurité, confidentialité et réglementation

La plateforme peut traiter des données financières d’entreprise ainsi que des données personnelles de dirigeants, salariés, clients et fournisseurs. La conformité et la sécurité doivent être intégrées dès la conception, pas ajoutées à la fin.

### 7.1 Exigences de sécurité P0

• Isolation stricte des workspaces et entités ; RBAC vérifié côté serveur sur chaque endpoint.
• MFA obligatoire pour administrateurs et propriétaires ; politique de session et révocation des appareils.
• TLS en transit, chiffrement des volumes et stockage, gestion des secrets hors du code.
• Journal d’audit non modifiable par les utilisateurs ordinaires.
• Sauvegardes chiffrées, test régulier de restauration et procédure d’incident.
• Rate limiting, validation des entrées, protection CSRF/XSS/SSRF, contrôle des uploads et dépendances.
• Pas de données client utilisées pour entraîner un modèle public sans base juridique, information et accord appropriés.
• Contrôle des accès du support technique et traçabilité de toute consultation de données clients.
• Export et suppression selon les règles contractuelles et légales ; rétention définie par type de données.

### 7.2 IA et fichiers non fiables

• Traiter chaque fichier importé et texte extrait comme une entrée non fiable ; un document ne peut pas donner d’instructions au modèle.
• Ne jamais ouvrir ou exécuter les macros Excel, scripts, pièces jointes ou formules comme du code.
• Limiter taille, nombre de lignes, types de fichiers et temps CPU des parseurs.
• Utiliser une sortie de modèle schématisée et validée ; échapper le texte avant affichage.
• Afficher la date et les sources ; faire dire « je ne sais pas » lorsque la donnée manque.
• Prévoir des tests contre prompt injection, fuite entre tenants, hallucination numérique et action non autorisée.

### 7.3 Cadre juridique à examiner

La loi camerounaise n°2024/017 du 23 décembre 2024 relative à la protection des données à caractère personnel doit être intégrée au cadrage juridique. Avant le pilote, un conseil local doit confirmer les rôles de responsable de traitement/sous-traitant, les bases de traitement, les mentions d’information, l’exercice des droits, les durées de conservation, les transferts internationaux et les exigences de sécurité applicables au cas concret.
Pour les données comptables, l’AUDCIF et le SYSCOHADA révisé sont des référentiels importants dans l’espace OHADA. Le produit doit importer et présenter des données issues de ces systèmes avec des correspondances explicites, sans se déclarer logiciel comptable conforme ni produire des états réglementaires au MVP.
Si une évolution future touche à l’initiation de paiements, à la fourniture de services de paiement ou à des données bancaires réglementées, analyser séparément le périmètre CEMAC/BEAC/COBAC et conclure des partenariats autorisés avant toute mise en production.

## 8. Exigences non fonctionnelles et critères d’acceptation

| Domaine | Cible MVP proposée | Test / preuve |
| --- | --- | --- |
| Performance | Cockpit principal p95 ≤ 3 s sur jeu de données pilote et connexion mobile raisonnable. | Tests de charge + mesures réelles sur téléphones Android ciblés. |
| Compatibilité | Android récent via PWA ; Chrome mobile ; navigateur desktop moderne. | Matrice de tests appareils/résolutions. |
| Faible réseau | Pages essentielles légères ; dernier snapshot en lecture seule ; brouillons en file locale. | Tests de déconnexion/reconnexion et conflits. |
| Calculs | 100 % de concordance avec les jeux de test de référence pour les métriques supportées. | Tests unitaires et tests de non-régression. |
| Provenance | 100 % des KPI publiés ont source, période, devise, date et règle. | Tests API + revue UX. |
| Sécurité | Aucun accès croisé entre tenants dans les tests ; aucun secret dans le dépôt. | Tests d’autorisation, revue ASVS, scan dépendances. |
| Sauvegarde | Sauvegarde automatisée et restauration de test documentée avant pilote payant. | Exercice de restauration, journal de résultat. |
| IA | Aucune action sensible exécutée sans confirmation ; réponses chiffrées reliées à un fait source. | Jeux de tests adversariaux, revue humaine d’échantillons. |
| Disponibilité | Objectif pilote : 99,5 % mensuel, hors maintenance annoncée. | Monitoring et rapport d’incidents. |

## 9. Roadmap MVP — 12 semaines

La roadmap ci-dessous est une séquence de réalisation, pas une promesse calendaire. Elle suppose une équipe dédiée et un accès rapide à des dirigeants pilotes ainsi qu’à des fichiers anonymisés ou autorisés.
| Période | Focus | Livrables | Gate de sortie |
| --- | --- | --- | --- |
| S1–S2 | Découverte et validation | 15–20 entretiens ; collecte d’exemples de rapports ; prototype mobile ; dictionnaire KPI ; segment d’entrée confirmé. | Au moins 5 dirigeants acceptent de tester avec leurs propres rapports et de discuter d’un pilote payant. |
| S3–S4 | Fondations produit et sécurité | UX testée ; modèle multi-tenant ; authentification ; rôles ; audit ; environnement dev/staging ; design system. | Tests d’isolation et parcours d’onboarding passés. |
| S5–S6 | Imports et qualité des données | CSV/XLSX ; PDF textuel assisté si ressources disponibles ; mapping ; détection doublons ; staging ; validation ; provenance. | Imports pilotes reproductibles sur fichiers réels et cas d’erreur gérés. |
| S7–S8 | Cockpit et actions | Vue portefeuille ; vue entreprise ; KPI prioritaires ; freshness ; alertes par règles ; centre d’actions. | Chaque chiffre affiché est traçable et les dirigeants comprennent les alertes sans formation longue. |
| S9–S10 | IA encadrée et mobile | Executive Brief ; Q&A structuré ; capture vocale en brouillon ; cache de lecture ; notifications. | Réponses fondées, aucune hallucination critique dans le jeu de tests, coût IA suivi. |
| S11–S12 | Pilote, hardening et commercialisation | Tests sécurité ; performance ; restauration ; onboarding ; formation ; mesure usage/valeur ; pricing pilote. | Go / Pivot / No-Go décidé à partir de données d’usage et de volonté de payer. |

### 9.1 Organisation d’équipe minimale

| Rôle | Charge indicative | Responsabilité |
| --- | --- | --- |
| Product owner / fondateur | Temps plein | Entretiens, arbitrages, priorisation, pilote et vente. |
| UX/UI designer | Temps partiel au début | Parcours mobile, prototype, tests utilisateurs et design system. |
| Backend engineer | Temps plein | API, multi-tenant, modèle de données, import, audit et sécurité. |
| Frontend engineer | Temps plein | PWA, tableau de bord, imports, cache et accessibilité. |
| Data/AI engineer | Temps partiel puis ciblé | Pipeline documentaire, métriques, prompts, évaluations et coûts IA. |
| QA / security reviewer | Temps partiel régulier | Tests fonctionnels, données, autorisations, sécurité et non-régression. |
| Conseil comptable/juridique local | Interventions ciblées | Validation des métriques, des mappings comptables et du cadre contractuel/réglementaire. |

## 10. Mesure du succès et critères de décision

| Indicateur | Définition | Seuil de validation pilote proposé |
| --- | --- | --- |
| Time-to-first-value | Temps entre création de l’espace et première vue fiable alimentée. | ≤ 30 minutes sur un fichier standard avec assistance légère. |
| Import success rate | Part des lots importés sans erreur bloquante après mapping. | ≥ 80 % sur les formats convenus avec les pilotes ; analyser les autres cas. |
| Data trust rate | Part des KPI contrôlés par les pilotes et acceptés sans correction. | ≥ 95 % sur les métriques supportées ; investiguer chaque écart. |
| Weekly active leaders | Dirigeants qui consultent le cockpit et traitent au moins une action par semaine. | ≥ 70 % des pilotes actifs après 4 semaines. |
| Action closure | Part des actions échues clôturées ou explicitement replanifiées. | Mesurer une amélioration vs baseline ; ne pas imposer un chiffre avant mesure. |
| Time saved | Temps hebdomadaire passé à consolider, relancer et produire le reporting. | Objectif exploratoire : ≥ 3 h économisées/semaine ; mesurer par journal de temps. |
| Willingness to pay | Pilotes qui acceptent une offre payante au prix testé. | Au moins 3 clients payants ou engagements de paiement documentés avant extension. |

### GATE DE LANCEMENT COMMERCIAL

Ne pas passer à l’échelle si les utilisateurs ne font pas confiance aux chiffres, si les imports requièrent systématiquement l’intervention de l’équipe produit ou si les dirigeants ne reviennent pas chaque semaine.

## 11. Principaux risques et réponses

| Risque | Probabilité / impact | Réponse |
| --- | --- | --- |
| Cible trop large | Élevée / élevé | Choisir un seul beachhead et une famille de rapports au départ. |
| Données hétérogènes et sales | Élevée / élevé | Templates d’import, mapping, validation, file REVIEW et provenance. |
| Cockpit sans usage récurrent | Moyenne / élevé | Faire du centre d’actions et des alertes la boucle de rétention ; mesurer le temps économisé. |
| Concurrence ERP local | Élevée / élevé | Ne pas recopier comptabilité/stock/paie ; se différencier par consolidation multi-systèmes et pilotage dirigeant. |
| Hallucinations IA | Moyenne / élevé | Calculs déterministes, réponses structurées, citations internes, seuils de refus et tests. |
| Fuite inter-entreprises | Faible à moyenne / critique | Isolation tenant, RBAC serveur, tests automatisés et revue sécurité. |
| Coûts IA incontrôlés | Moyenne / moyen | Résumé événementiel, cache, quotas, modèles adaptés et suivi du coût par compte. |
| Faible connectivité | Élevée / moyen | PWA légère, cache lecture seule, synchronisation explicite et tests sur réseau dégradé. |
| Glissement vers ERP | Élevée / élevé | Roadmap stricte ; toute nouvelle saisie métier doit démontrer un avantage sur la consolidation. |

## 12. Hypothèse de monétisation

Tester une tarification par espace de travail et nombre d’entités/sites suivis, plutôt que par nombre de requêtes IA. Le client achète une visibilité et un système de suivi, pas des tokens.
| Offre test | Prix mensuel hypothétique | Limites commerciales à tester |
| --- | --- | --- |
| Pilot / Solo | 15 000–25 000 FCFA | 1 entreprise, 1–2 utilisateurs, imports mensuels limités, cockpit et actions. |
| Portfolio | 35 000–75 000 FCFA | Jusqu’à 5 entités/sites, plusieurs utilisateurs, alertes et brief IA. |
| Group | 100 000–200 000 FCFA+ | Plusieurs entités, rôles avancés, exports, onboarding et support renforcé. |
| Enterprise | Sur devis | Connecteurs, SSO, exigences contractuelles et déploiement spécifique. |

Ce sont des hypothèses de test, non des prix établis par une étude de disposition à payer. Prévoir frais d’onboarding ou de nettoyage de données lorsque l’historique est complexe. Ne pas inclure un usage IA illimité.

## 13. Décisions à prendre avant le premier sprint

• Valider le segment d’entrée précis (ex. distribution multi-sites ou services multi-entités) sur la base des 15–20 entretiens.
• Sélectionner 5 à 10 entreprises pilotes qui acceptent de partager des fichiers anonymisés/autorisé et de tester chaque semaine.
• Collecter au moins deux modèles de rapports réels par entreprise et choisir les trois familles de données supportées.
• Valider le dictionnaire des 5–7 KPI du MVP avec un expert-comptable camerounais.
• Faire examiner les flux de données et contrats par un conseil juridique local avant toute mise en production client.
• Choisir les fournisseurs d’hébergement et d’IA après analyse des conditions de traitement, localisation, rétention, coûts et réversibilité.

### DÉCISION RECOMMANDÉE

GO pour prototype et validation client. NO-GO pour un développement complet multi-secteurs avant d’avoir confirmé un segment, une source de données récurrente et une disposition à payer.

## Annexe A — Sources et hypothèses externes

Les liens ci-dessous servent de points de départ à la vérification du marché, des référentiels et des exigences de sécurité. Les affirmations juridiques doivent être confirmées par un conseil local avant contractualisation ou déploiement.
DataReportal — Digital 2026: Cameroon
https://datareportal.com/reports/digital-2026-cameroon
Repères d’accès Internet et connectivité publiés pour fin 2025 ; les chiffres de connexions mobiles ne sont pas équivalents au nombre d’utilisateurs Internet.
Omamori — Offres et tarifs
https://omamori.cm/offres
Concurrent local affichant notamment des offres à 15 000 et 25 000 FCFA/mois et des fonctions de gestion, mobile et hors ligne.
Omamori — Produit
https://omamori.cm/
Référence concurrentielle : comptabilité, ventes, stock, trésorerie, tableaux de bord et accompagnement local.
OHADA — Publication de l’AUDCIF et du SYSCOHADA révisé
https://www.ohada.org/publication-du-nouvel-acte-uniforme-relatif-au-droit-comptable-et-a-l-information-financiere-audcif/
Source institutionnelle sur l’AUDCIF et le SYSCOHADA révisé.
Présidence de la République du Cameroun — Loi n°2024/017
https://prc.cm/fr/actualites/actes/lois/7588-loi-n-2024-017-du-23-decembre-2024-autorisant-le-president-de-la-republique-a-ratifier-le-traite-de-beijing-sur-les-interpretations-et-executions-audiovisuelles-adopte-le-24-juin-2012-a-beijing-chine-9
Page officielle de publication du texte relatif à la protection des données personnelles.
OWASP — Application Security Verification Standard 5.0
https://asvs.owasp.org/
Référentiel de vérification de sécurité applicative ; version 5.0.0 publiée en mai 2025.
NIST — AI RMF Generative AI Profile
https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
Cadre de référence volontaire pour la gestion des risques des systèmes d’IA générative.
