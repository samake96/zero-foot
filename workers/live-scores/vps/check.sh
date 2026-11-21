#!/usr/bin/env bash
set -eu
printf 'Saisis ta cle API-Football puis appuie sur Entree : '
IFS= read -rs API_FOOTBALL_KEY
printf '\n'
if [[ -z "$API_FOOTBALL_KEY" ]]; then
  printf 'Cle manquante.\n' >&2
  exit 1
fi
export API_FOOTBALL_KEY
exec node --dns-result-order=ipv4first /opt/matchscope/workers/live-scores/vps/collect.mjs --check
