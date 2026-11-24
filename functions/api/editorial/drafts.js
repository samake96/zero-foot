import {submitDraft} from '../../_lib/editorial-draft.js';

const reply = (status) => new Response(null, {status, headers:{'Cache-Control':'no-store'}});
const encoder = new TextEncoder();

export async function onRequestPost({request, env}) {
  const secret = env.EDITORIAL_DRAFT_TOKEN;
  if (!secret || secret.length < 32 || !env.COMMUNITY_DB) return reply(503);
  const token = request.headers.get('Authorization') || '';
  const sign = value => crypto.subtle.digest('SHA-256', encoder.encode(value));
  const [actual, expected] = await Promise.all([sign(token), sign('Bearer ' + secret)]);
  if (!crypto.subtle.timingSafeEqual(actual, expected)) return reply(403);
  const key = request.headers.get('Idempotency-Key') || '';
  if (!/^[A-Za-z0-9_-]{8,80}$/.test(key) ||
      !request.headers.get('Content-Type')?.startsWith('application/x-www-form-urlencoded')) return reply(400);

  const reader = request.body?.getReader();
  if (!reader) return reply(400);
  const decoder = new TextDecoder();
  let body = '';
  let bytes = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > 64000) {
        await reader.cancel();
        return reply(413);
      }
      body += decoder.decode(value, {stream:true});
    }
    const fields = new URLSearchParams(body + decoder.decode());
    const result = await submitDraft(env.COMMUNITY_DB, key => (fields.get(key) || '').trim(), 'veille-footchrono', 'veille-' + key);
    return reply(result.status);
  } catch {
    return reply(503);
  }
}
