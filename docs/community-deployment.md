# Activation de FootChrono Community sur Cloudflare Pages

Le code de lecture et de publication est présent, mais les échanges restent désactivés tant que l'infrastructure n'est pas configurée.

1. Créer une base Cloudflare D1 nommée `matchscope-community` dans le compte Cloudflare qui héberge Pages.
2. Ajouter la liaison D1 `COMMUNITY_DB` au projet Pages, pour la production et les environnements de prévisualisation appropriés.
3. Appliquer `migrations/0001_community.sql` à cette base via la console D1 ou Wrangler. Ne pas exécuter la migration contre une autre base.
4. Configurer une application Cloudflare Access pour protéger la publication de messages. Définir `ACCESS_TEAM_DOMAIN` (par exemple `myteam.cloudflareaccess.com`) et `ACCESS_AUD` dans les variables d'environnement Pages. Le serveur vérifie la signature du JWT Access et son audience avant d'accepter les publications.
5. Attention : protéger uniquement les requêtes POST avec une politique Access appropriée. La lecture GET doit rester publique. La politique et l'authentification doivent être testées dans un navigateur réel, car les configurations Access diffèrent.
6. Redéployer et vérifier : GET /api/matches/123/posts (200), POST sans jeton (401), POST avec jeton Access valide (201), limite de publication (429), réponses non autorisées (400).

## Important
- Les identités Cloudflare Access ne sont pas des comptes supporters classiques. Cette intégration est un premier backend sécurisé, à remplacer ou compléter par une authentification grand public avant ouverture à grande échelle.
- Aucune clé API ou secret ne doit être commité dans GitHub.
- Le front n'affiche pas encore de formulaire de publication. Il ne faut pas annoncer le forum comme ouvert.
- La protection contre le spam actuelle est une première barrière et non une solution de modération complète. Un panneau de modération, les signalements, les contrôles des liens et les tests de charge restent nécessaires.
