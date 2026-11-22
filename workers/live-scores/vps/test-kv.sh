#!/usr/bin/env bash
set -eu
node --env-file=/etc/matchscope-scores.env --dns-result-order=ipv4first --input-type=module <<'JS'
import {randomUUID} from 'node:crypto';
import {cloudflareKV} from '/opt/matchscope/workers/live-scores/vps/collect.mjs';

const {CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_KV_NAMESPACE_ID, CLOUDFLARE_API_TOKEN} = process.env;
try {
  const kv = cloudflareKV(CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_KV_NAMESPACE_ID, CLOUDFLARE_API_TOKEN);
  await kv.put('vps-test-' + randomUUID(), 'ok', {expirationTtl: 120});
  console.log('Test KV reussi.');
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
JS
