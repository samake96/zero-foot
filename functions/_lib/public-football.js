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

export function page({path, title, description, heading, content, status = 200, cache = 60, ads = true}) {
  const url = 'https://footchrono.com' + path;
  const html = `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escape(title)} | FootChrono</title><meta name="description" content="${escape(description)}">
<link rel="canonical" href="${url}"><meta property="og:url" content="${url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="FootChrono">
<meta property="og:title" content="${escape(title)}"><meta property="og:description" content="${escape(description)}">
<meta property="og:locale" content="fr_FR"><meta name="twitter:card" content="summary">
<link rel="stylesheet" href="/footchrono-public.css">${ads ? '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180571260643744" crossorigin="anonymous"></script><style>.fc-ad{width:calc(100% - 32px);max-width:728px;margin:16px auto}.fc-ad:has(ins[data-ad-status="unfilled"]){display:none}</style>' : ''}</head><body><header class="fc-header"><div class="fc-header-inner"><a class="fc-brand" href="/" aria-label="FootChrono, accueil"><span class="fc-mark" aria-hidden="true">F</span><span>Foot<b>Chrono</b></span></a><nav class="fc-nav" aria-label="Navigation principale"><a href="/">Accueil</a><a href="/scores"${path === '/scores' ? ' aria-current="page"' : ''}>Scores</a><a href="/classements"${path.startsWith('/classements') ? ' aria-current="page"' : ''}>Classements</a><a href="/#page=predictions">Pronostics</a><a href="/actualites/">Actualités</a></nav></div></header><main><h1>${escape(heading)}</h1>${content}</main>
${ads ? `<div class="fc-ad"><ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-7180571260643744" data-ad-slot="1991336459" data-ad-format="horizontal" data-full-width-responsive="false"></ins></div>
<script>(window.adsbygoogle = window.adsbygoogle || []).push({});</script>
` : ''}<footer class="fc-footer"><nav aria-label="Informations sur le site"><a href="/confidentialite/">Confidentialité</a> <a href="/contact/">Contact</a></nav></footer></body></html>`;
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
