# Collecte FootChrono depuis une IPv4 dédiée

Provisionner un VPS Linux avec une IPv4 publique attribuée au serveur et Node.js 22. Le VPS interroge API-Football et écrit dans le stockage Cloudflare KV existant. Aucun serveur HTTP public n'est requis.

1. Rendre ce dépôt disponible à /opt/matchscope, accessible en lecture au service.
2. Créer /etc/matchscope-scores.env appartenant à root, mode 0600. Renseigner API_FOOTBALL_KEY, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_KV_NAMESPACE_ID et CLOUDFLARE_API_TOKEN, une variable NAME=value par ligne. L'espace KV est matchscope-live-scores. Utiliser un jeton Cloudflare avec permission Workers KV Storage Write sur le compte concerné.
3. Installer les unités depuis ce répertoire avec `sudo install -m 644 matchscope-scores.{service,timer} /etc/systemd/system/`, puis `sudo systemctl daemon-reload`.
4. Vérifier l'appel fournisseur seul avec `sudo systemd-run --wait --pipe -p EnvironmentFile=/etc/matchscope-scores.env /usr/bin/node --dns-result-order=ipv4first /opt/matchscope/workers/live-scores/vps/collect.mjs --check`. Répéter sur plusieurs créneaux pour détecter les refus intermittents.
5. Désactiver le déclencheur Cron du Worker Cloudflare avant d'activer le nouveau producteur. Lancer `sudo systemctl start matchscope-scores.service`. Vérifier la collecte dans `sudo journalctl -u matchscope-scores.service -n 20` et sur https://footchrono.com/api/live-scores.
6. Activer la minuterie via `sudo systemctl enable --now matchscope-scores.timer`. Observer plusieurs renouvellements consécutifs de updated_at. Le service utilise le même format de données que le Worker historique.
7. En cas d'échec, arrêter la minuterie VPS avant de réactiver le Cron Cloudflare afin de garder un seul producteur.
