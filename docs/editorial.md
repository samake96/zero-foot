# Activer la rédaction FootChrono

1. Appliquer `migrations/0002_editorial.sql` à la base D1 liée au projet Pages sous `COMMUNITY_DB`.
2. Dans Cloudflare Access, protéger `/redaction` et ses sous-chemins. Configurer la vérification JWT côté Pages avec `ACCESS_TEAM_DOMAIN` et l’audience de l’application. Si la rédaction et la communauté utilisent des applications Access distinctes, configurer `EDITORIAL_ACCESS_AUD` pour la rédaction.
3. Dans les variables de production de Pages, renseigner `EDITORIAL_WRITERS` et `EDITORIAL_REVIEWERS` avec les adresses Access autorisées, séparées par des virgules. Utiliser deux comptes distincts pour une soumission et sa validation.
4. Après déploiement, ouvrir `/redaction/`. Le rédacteur saisit l’identifiant de la fiche et les sources. Le relecteur ouvre la fiche, contrôle l’identité des clubs, la compétition et les faits, puis publie ou refuse avec une note. La fiche publique peut conserver la version précédente en cache pendant 30 secondes.

Les mises à jour de matchs exécutent déjà `scripts/validate_data.py` avant publication. Un échec du script arrête la publication des données de ce traitement.
