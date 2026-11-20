# ZERO FOOT — Classements automatiques

1. Déposez `index.html` à la racine du dépôt GitHub (remplacer le fichier existant).
2. Ajoutez `scripts/update_standings.py`, `.github/workflows/standings.yml` et `data/standings.json` aux chemins exacts.
3. Le workflow attend le secret GitHub `API_FOOTBALL_KEY`. Si votre secret existant porte un autre nom, adaptez la référence dans `standings.yml` (ne collez jamais la clé dans le code).
4. Dans GitHub → Actions → Update football standings → Run workflow, lancez la collecte.
5. Vérifiez que `data/standings.json` contient des équipes, puis attendez le déploiement Cloudflare Pages.

Le workflow tourne chaque jour à 06:25 UTC. Il effectue cinq requêtes par exécution (hors éventuels appels externes au site). La saison est actuellement fixée à 2026 : adaptez `FOOTBALL_SEASON` lors du passage à la saison suivante. L'API peut limiter certains championnats ou saisons selon votre abonnement. En cas d'échec d'une ligue, le script conserve sa dernière version valide, si disponible.

**Attention :** l'interface ne garantit pas du temps réel. Ne communiquez jamais votre clé API dans une capture ou un message.
