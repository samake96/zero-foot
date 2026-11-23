export function onRequestGet({params}) {
  const match = /^([1-9][0-9]{0,8})\.png$/.exec(params.id);
  if (!match) return new Response(null, {status:404});
  const [filename, id] = match;
  const host = ['45', '55', '539', '797'].includes(id)
    ? 'https://footchrono.com/images/clubs/'
    : 'https://media.api-sports.io/football/teams/';
  return new Response(null, {status:302, headers:{location: host + filename}});
}
