# Sécurité et gouvernance des données

## Modèle de menace simplifié

YFEN manipule des données financières d’entreprise et des informations potentiellement personnelles. Les principales menaces couvertes dans le socle sont : accès inter-workspace, import de fichier malformé, doublon d’un lot, injection de formule dans un export, publication de faits non confirmés et fuite d’un fichier source.

## Contrôles présents dans le code

- Token d’authentification requis sur les endpoints métier.
- Membership actif vérifié côté serveur pour chaque lecture/écriture tenant-scoped.
- Relations entité et responsable validées dans le périmètre du workspace.
- Taille upload limitée à 10 Mo, types admis CSV/XLSX/PDF et vérifications de signature XLSX/PDF.
- SHA-256 stocké ; un même fichier n’est pas réimportable dans un même workspace.
- Les fichiers originaux ne sont pas servis par une route publique ; `MEDIA_URL` n’est pas exposé.
- Les faits sont préparés en revue et ne deviennent visibles dans le cockpit qu’après confirmation explicite.
- L’audit est append-only au niveau du modèle ; les événements sensibles sont créés par l’API.
- Les données API ne sont jamais mises en cache par le service worker.
- Les cellules de formule XLSX sont détectées et refusées ; les macros ne sont jamais ouvertes ni exécutées. Le classeur est soumis à un plafond de décompression et de nombre d’entrées ZIP avant parsing.

## Garde-fous encore incomplets

Ce dépôt ne doit pas être présenté comme certifié ni prêt à accueillir des données client sensibles en production. À compléter avant pilote réel :

1. MFA obligatoire pour OWNER/ADMIN, expiration/rotation des tokens et révocation des appareils.
2. Scanner antivirus ou service de détection en quarantaine et parsing dans un conteneur/worker avec limites CPU, mémoire, temps, pages PDF, lignes et décompression ZIP.
3. Chiffrement au repos du stockage objet et des sauvegardes ; gestion KMS des clés et rotation des secrets.
4. Politique de sauvegarde, exercices de restauration, RPO/RTO et plan de réponse incident.
5. Tests de pénétration et revue OWASP ASVS, contrôle SSRF/XSS/CSRF/IDOR, scan de dépendances et CSP stricte.
6. Journal d’audit externalisé ou protégé contre l’altération par un opérateur système ; la protection Django ne résiste pas à un administrateur de base de données.
7. Contrats, mentions d’information, bases légales, gestion des droits, sous-traitants, transferts internationaux et durées de conservation.
8. Export complet et suppression/fermeture de compte conforme à la politique contractuelle et légale.

## Fichiers et IA

Les fichiers et les textes extraits sont des données non fiables. Ils ne peuvent pas fournir d’instructions au système. La version actuelle n’envoie aucun fichier à un LLM. Lors de l’activation P1, un adaptateur devra transmettre un contexte structuré minimal, calculé par les services métier autorisés. Le modèle ne recevra ni SQL libre, ni identifiants de stockage, ni capacité d’écriture. Toute création d’action issue de la voix devra être présentée à l’utilisateur puis confirmée.

## Références à valider

Le PRD fourni cite la loi camerounaise n°2024/017, l’AUDCIF/SYSCOHADA, l’OWASP ASVS 5.0 et le NIST AI RMF Generative AI Profile. Leurs applications exactes au produit, notamment le texte juridique et les transferts de données, doivent être confirmées par un conseil camerounais avant traitement de données de clients pilotes.
