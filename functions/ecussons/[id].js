const localBadges = new Set(['45', '55', '539', '797']);

export async function onRequestGet({params, request, env}) {
  const match = /^([1-9][0-9]{0,8})\.png$/.exec(params.id);
  if (!match) return new Response(null, {status:404});
  const [filename, id] = match;
  try {
    const image = localBadges.has(id)
      ? await env.ASSETS.fetch(new URL('/images/clubs/' + filename, request.url))
      : await fetch('https://media.api-sports.io/football/teams/' + filename, {
        cf:{cacheEverything:true,cacheTtlByStatus:{'200-299':86400,'400-599':0}},
      });
    if (image.ok && image.headers.get('content-type')?.startsWith('image/')) {
      return new Response(image.body,{headers:{
        'Content-Type':image.headers.get('content-type'),
        'Cache-Control':'public, max-age=86400',
      }});
    }
  } catch {
    return new Response(null,{status:502});
  }
  return new Response(null,{status:404});
}
