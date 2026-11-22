export const competitions = [
  {id: 39, slug: 'premier-league', name: 'Premier League'},
  {id: 140, slug: 'la-liga', name: 'La Liga'},
  {id: 78, slug: 'bundesliga', name: 'Bundesliga'},
  {id: 135, slug: 'serie-a', name: 'Serie A'},
  {id: 61, slug: 'ligue-1', name: 'Ligue 1'},
];

export const escape = value => String(value ?? '').replace(/[&<>"']/g, char =>
  ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[char]);

export async function loadData(context, file) {
  const url = new URL('/data/' + file + '.json', context.request.url);
  const response = await context.env.ASSETS.fetch(url);
  if (!response.ok) throw new Error('Data unavailable');
  return response.json();
}

export function dateLabel(value, includeTime = false) {
  const date = new Date(value);
  if (!value || !Number.isFinite(date.getTime())) return 'Date indisponible';
  const options = includeTime ? {dateStyle: 'medium', timeStyle: 'short'} : {dateStyle: 'long'};
  return new Intl.DateTimeFormat('fr-FR', {...options, timeZone: 'UTC'}).format(date);
}

export function page({path, title, description, heading, content, status = 200, cache = 60}) {
  const url = 'https://footchrono.com' + path;
  const html = `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escape(title)} | FootChrono</title><meta name="description" content="${escape(description)}">
<link rel="canonical" href="${url}"><meta property="og:url" content="${url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="FootChrono">
<meta property="og:title" content="${escape(title)}"><meta property="og:description" content="${escape(description)}">
<meta property="og:locale" content="fr_FR"><meta name="twitter:card" content="summary">
<style>
*{box-sizing:border-box}body{margin:0;background:#0b1727;color:#e9f1fa;font:16px/1.55 system-ui,sans-serif}
main,header{max-width:960px;margin:auto;padding:24px}nav,.links{display:flex;gap:16px;flex-wrap:wrap}
a{color:#84edb6;text-underline-offset:3px}h1{font-size:clamp(2rem,6vw,3rem);line-height:1.12}
.table-wrap{overflow:auto;margin:16px 0}table{border-collapse:collapse;width:100%;min-width:420px}
th,td{padding:9px;text-align:start;border-bottom:1px solid #304159}tbody th{font-weight:600}
.muted{color:#b1c1d1}.score{white-space:nowrap;font-weight:700}
</style></head><body><header><nav aria-label="Navigation principale"><a href="/">FootChrono</a>
<a href="/scores">Scores</a><a href="/classements">Classements</a><a href="/actualites/">Actualités</a></nav>
</header><main><h1>${escape(heading)}</h1>${content}</main></body></html>`;
  return new Response(html, {
    status,
    headers: {'content-type': 'text/html; charset=utf-8', 'cache-control': status === 200 ? 'public, max-age=' + cache : 'no-store'},
  });
}

export function competitionLinks() {
  return '<div class="links">' + competitions.map(({slug, name}) =>
    `<a href="/classements/${slug}">Classement ${escape(name)}</a>`).join('') + '</div>';
}

export function standingsTable(teams) {
  return `<div class="table-wrap"><table><thead><tr><th scope="col">Pos.</th><th scope="col">Équipe</th>
<th scope="col">MJ</th><th scope="col">V</th><th scope="col">N</th><th scope="col">D</th>
<th scope="col">Diff.</th><th scope="col">Pts</th></tr></thead><tbody>${teams.map(team =>
  `<tr><td>${escape(team.rank)}</td><th scope="row">${escape(team.name)}</th>
<td>${escape(team.played)}</td><td>${escape(team.win)}</td><td>${escape(team.draw)}</td>
<td>${escape(team.lose)}</td><td>${escape(team.goal_diff)}</td><td>${escape(team.points)}</td></tr>`).join('')}</tbody></table></div>`;
}
