export async function onRequestGet({params}) {
  const match = /^([1-9][0-9]{0,8})\.png$/.exec(params.id);
  if (!match) return new Response(null, {status:404});

  try {
    const image = await fetch('https://media.api-sports.io/football/teams/' + match[1] + '.png',
      {signal:AbortSignal.timeout(5000), redirect:'error'});
    const type = image.headers.get('content-type') ?? '';
    if (image.ok && type.startsWith('image/png')) {
      return new Response(image.body, {headers:{
        'content-type':'image/png', 'cache-control':'public, max-age=86400',
      }});
    }
    if (image.status === 404) return new Response(null,{status:404});
  } catch {
    // A temporary source failure must not be cached as a missing badge.
  }
  return new Response(null,{status:502,headers:{'cache-control':'no-store'}});
}
