# Activation des scores MATCHSCOPE

Le site conserve le fichier de scores périodiques lorsque le flux Cloudflare est indisponible. Le collecteur est un Worker sans adresse publique. La fonction Pages /api/live-scores lit l'instantané dans KV. Le navigateur le consulte chaque minute lorsque l'onglet est visible. Il affiche « En direct » pour les rencontres en cours du flux à deux minutes si leur collecte date de quatre minutes au plus.

## Activation gratuite

1. Créer un espace Workers KV nommé matchscope-live-scores dans le compte Cloudflare qui héberge zero-foot. Reporter son ID dans workers/live-scores/wrangler.toml sur la copie de déploiement.
2. Depuis workers/live-scores, enregistrer la clé existante avec `npx wrangler secret put API_FOOTBALL_KEY`, puis déployer avec `npx wrangler deploy`. Saisir la clé dans l'invite de Wrangler.
3. Dans Workers & Pages → zero-foot → Settings → Bindings, ajouter une liaison KV de production nommée LIVE_SCORES vers le même espace. Redéployer le projet Pages.
4. Vérifier /api/live-scores après le prochain collecteur. L'intervalle attendu est 1800 secondes. Le site indique « Scores différés ». Ce mode ajoute 48 requêtes API par jour et partage le quota avec les workflows GitHub existants lorsque la même clé est utilisée.

## Activation du mode à deux minutes

Vérifier que le forfait API autorise au moins 720 requêtes par jour pour ce collecteur en plus des autres tâches. Dans workers/live-scores/wrangler.toml, remplacer le cron par `*/2 * * * *` puis redéployer le Worker. L'intervalle attendu dans /api/live-scores est 120 secondes. Le cache KV peut ajouter un délai de propagation. Le collecteur couvre la journée UTC courante.

Sur une rencontre en cours, relever l'heure de deux changements de score ou de statut comparés à la source et vérifier leur apparition dans le tableau puis dans la fiche ouverte. Vérifier que l'arrêt du collecteur fait repasser le site en mode différé. Exécuter les tests du collecteur avec `node --test workers/live-scores/index.test.mjs`.
