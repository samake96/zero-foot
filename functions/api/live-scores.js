export async function onRequestGet({env}) {
  const fallback = (reason) => Response.json({available: false, reason}, {
    headers: {'cache-control': 'no-store'},
  });
  if (!env.LIVE_SCORES) return fallback('not_configured');
  try {
    const snapshot = await env.LIVE_SCORES.get('latest', {type: 'json', cacheTtl: 30});
    if (!snapshot) return fallback('awaiting_collection');
    return Response.json(snapshot, {headers: {'cache-control': 'no-store'}});
  } catch {
    return fallback('temporarily_unavailable');
  }
}
