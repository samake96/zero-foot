#!/usr/bin/env bash
set -eu
umask 077
test "$(id -u)" = 0
config=$(mktemp /etc/matchscope-scores.env.XXXXXX)
trap 'rm -f -- "$config"' EXIT
read -rsp 'Cle API-Football puis Entree : ' football
printf '\n'
read -rsp 'Jeton Cloudflare puis Entree : ' token
printf '\n'
if [[ ! $football =~ ^[a-zA-Z0-9]+$ || ! $token =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo 'Cle ou jeton vide ou mal saisi.'
  exit 1
fi
printf '%s\n' \
  'CLOUDFLARE_ACCOUNT_ID=34cd3f1ad7970055b54bd7ecc92906b9' \
  'CLOUDFLARE_KV_NAMESPACE_ID=4bf871d36e734697aaefb19aec9df9aa' \
  "API_FOOTBALL_KEY=$football" "CLOUDFLARE_API_TOKEN=$token" > "$config"
node --env-file="$config" --dns-result-order=ipv4first /opt/matchscope/workers/live-scores/vps/collect.mjs --check
mv -f -- "$config" /etc/matchscope-scores.env
echo 'Configuration enregistree.'
