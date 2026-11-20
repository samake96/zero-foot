# MATCHSCOPE Community — contrat fonctionnel V1

## Objectif
Permettre des échanges authentiques autour de chaque match, pour augmenter le retour des visiteurs sans transformer MATCHSCOPE en plateforme de paris.

## Parcours
- Onglet « Discussions » dans chaque fiche de match, avec nombre de messages et activité récente.
- Lecture publique, écriture réservée aux comptes connectés et vérifiés.
- Messages (maximum 1000 caractères), réponses à un message (un niveau initialement), tri « récents » ou « populaires ».
- Sondage 1/N/2 avant et pendant la rencontre, un vote par compte et par match. Les résultats des supporters doivent être explicitement distingués des probabilités du modèle.
- Un lien de partage renvoie vers une URL stable de match.

## Données et architecture
Une vraie discussion partagée exige un service serveur et une base de données. Ne jamais simuler des commentaires ou des votes comme s'ils provenaient d'autres utilisateurs. Ne pas stocker les messages publics uniquement dans localStorage.

Tables recommandées (PostgreSQL) :
- users(id UUID PK, display_name, created_at, status)
- matches(id TEXT PK, kickoff_at, home_name, away_name, league)
- posts(id UUID PK, match_id FK, user_id FK, parent_id FK nullable, body, created_at, edited_at, status)
- votes(match_id FK, user_id FK, choice CHECK IN ('home','draw','away'), created_at, PRIMARY KEY(match_id,user_id))
- reports(id UUID PK, post_id FK, reporter_id FK, reason, created_at, status)
- moderation_actions(id UUID PK, moderator_id FK, post_id FK, action, reason, created_at)

## API
GET /api/matches/:id/posts?cursor=&sort=new|popular (pagination)
POST /api/matches/:id/posts (auth obligatoire, contrôle serveur)
POST /api/posts/:id/report (auth)
GET /api/matches/:id/poll (comptes agrégés)
PUT /api/matches/:id/poll/vote (auth, upsert)
DELETE /api/posts/:id (auteur/modérateur, suppression logique)

## Sécurité et conformité
- Authentification serveur, contrôle des droits par utilisateur et match; aucune clé privée dans le navigateur.
- Anti-spam: limites de débit par compte/IP, CAPTCHA adaptatif, validation des tailles, sanitation, requêtes paramétrées.
- Signaler/bloquer, modération, suppression logique, journal d'audit, règles communautaires, protection des mineurs et des données personnelles.
- Ne pas afficher de faux compteurs ou de faux utilisateurs.
- Conserver les contenus conformément à une politique de confidentialité et de rétention explicite.
- Aucun chat temps réel revendiqué sans infrastructure de publication/abonnement et mesures de charge.

## Déploiement progressif
1. Base PostgreSQL managée, authentification, API sécurisée, tests d'autorisation.
2. Lecture/écriture et signalement sur fiches de match.
3. Sondages, classement des discussions, notifications opt-in.
4. Temps réel via SSE/WebSocket seulement si la charge et l'intérêt le justifient.

## Critères d'acceptation
- Deux comptes différents voient les mêmes messages après rafraîchissement.
- Impossible de publier en anonyme, de supprimer le message d'autrui ou de voter deux fois.
- Un message signalé peut être masqué et restauré par un modérateur.
- Les archives de matchs restent consultables avec leur discussion après le coup de sifflet final.
- Les temps de chargement des scores ne dépendent pas de la disponibilité du service Community.
- Tests d'intégration, charge et modération validés avant ouverture publique.

## Indicateurs
Visiteurs récurrents 7/30 jours, taux de consultation des discussions, messages utiles par match, signalements par 1000 messages, rétention et temps de réponse API.