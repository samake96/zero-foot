#!/usr/bin/env bash
set -eu
umask 077
config=/etc/matchscope-scores.env
candidate=$(mktemp /etc/matchscope-scores.env.XXXXXX)
trap 'rm -f -- "$candidate"' EXIT
read -rsp 'Jeton Cloudflare puis Entree : ' token
printf '\n'
if [[ ! $token =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo 'Jeton vide ou mal saisi.'
  exit 1
fi
sed '/^CLOUDFLARE_API_TOKEN=/d' "$config" > "$candidate"
printf '\nCLOUDFLARE_API_TOKEN=%s\n' "$token" >> "$candidate"
unset token CLOUDFLARE_API_TOKEN
node --env-file="$candidate" --dns-result-order=ipv4first --input-type=module <<'JS'
import {randomUUID} from 'node:crypto';
import {cloudflareKV} from '/opt/matchscope/workers/live-scores/vps/collect.mjs';

const {CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_KV_NAMESPACE_ID, CLOUDFLARE_API_TOKEN} = process.env;
try {
  const kv = cloudflareKV(CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_KV_NAMESPACE_ID, CLOUDFLARE_API_TOKEN);
  await kv.put('vps-test-' + randomUUID(), 'ok', {expirationTtl: 120});
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
JS
mv -f -- "$candidate" "$config"
echo 'Test KV reussi. Jeton enregistre.'
