import {pathToFileURL} from 'node:url';
import {collectScores} from '../index.mjs';

export function cloudflareKV(account, namespace, token, request = fetch) {
  if (!/^[a-f0-9]{32}$/i.test(account || '') || !/^[a-f0-9]{32}$/i.test(namespace || '') || !token) {
    throw new Error('Cloudflare KV configuration is incomplete');
  }
  return {
    async put(key, value, {expirationTtl}) {
      const url = new URL('https://api.cloudflare.com/client/v4/accounts/' + account +
        '/storage/kv/namespaces/' + namespace + '/values/' + encodeURIComponent(key));
      url.searchParams.set('expiration_ttl', String(expirationTtl));
      const response = await request(url, {
        method: 'PUT',
        headers: {authorization: 'Bearer ' + token, 'content-type': 'application/octet-stream'},
        body: value,
        signal: AbortSignal.timeout(15000),
      });
      const result = await response.json().catch(() => null);
      if (!response.ok || result?.success !== true) {
        throw new Error('Cloudflare KV publication failed (HTTP ' + response.status + ')');
      }
    },
  };
}

async function main() {
  const checkOnly = process.argv.includes('--check');
  const env = process.env;
  const store = checkOnly ? {async put(_key, value) {
    console.log(JSON.parse(value).matches.length + ' fixtures validated; no publication');
  }} : cloudflareKV(env.CLOUDFLARE_ACCOUNT_ID, env.CLOUDFLARE_KV_NAMESPACE_ID, env.CLOUDFLARE_API_TOKEN);
  await collectScores({cron: '*/2 * * * *', scheduledTime: Date.now()}, {
    API_FOOTBALL_KEY: env.API_FOOTBALL_KEY,
    LIVE_SCORES: store,
  });
  if (!checkOnly) console.log('Live scores snapshot published');
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  main().catch(error => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
