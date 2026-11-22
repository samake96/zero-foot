# FootChrono — feuille de route de livraison

Mise à jour : 2026-11-21

## Vision
Une plateforme footballistique rapide, accessible sur mobile, avec scores et calendrier, statistiques fiables, archives, prévisions expliquées et discussions modérées.

## Règles de livraison
- Un commit n'est pas une livraison vérifiée.
- Chaque fonctionnalité doit avoir des tests, un état de disponibilité explicite et un contrôle sur le site publié.
- Ne jamais afficher une statistique inventée, ni qualifier de « direct » un score actualisé toutes les trois heures.
- Ne pas engager de dépenses ni activer un service payant sans accord.
- Ne pas exposer les clés API côté navigateur.
- Mesurer les performances mobiles et l'accessibilité avant de déclarer une version terminée.

## Priorité 0 — fiabilité des données
- [x] Archivage automatique des résultats définitifs (premier fichier observé : 42 résultats au 21/11/2026)
- [ ] Tests automatisés de validation des archives et des rencontres
- [ ] Surveillance de la fraîcheur des données et messages explicites sur le site
- [ ] Contrôle de déploiement Cloudflare en conditions réelles

## Priorité 1 — expérience produit
- [x] Nouvelle identité visuelle FootChrono V6 (code)
- [x] Fiches historiques interactives (code)
- [ ] Tests navigateur sur mobile et ordinateur
- [ ] Navigation par match, équipe et championnat avec URL partageables
- [ ] Affichage des états vides, erreurs et chargements cohérent

## Priorité 2 — architecture et couverture
- [ ] Interface d'accès aux données indépendante des fournisseurs
- [ ] Base de données et cache avec stratégie de rétention
- [ ] Sélection et comparaison des API selon couverture, latence, coût et droits d'usage
- [ ] Matchs en cours : rafraîchissement adapté au budget et à la licence
- [ ] Statistiques détaillées et événements seulement si fournis par la source

## Priorité 3 — analyses et communauté
- [ ] Évaluation continue de la calibration des probabilités et publication des limites
- [ ] Gestion des identités équipes entre fournisseurs
- [ ] Forum : authentification, modération, anti-spam, signalements et tests E2E
- [ ] Observabilité, sauvegardes et plan de reprise

## Définition de terminé
Code relu, tests automatisés réussis, déploiement de production confirmé, parcours utilisateur vérifié sur navigateur et limitations documentées.
