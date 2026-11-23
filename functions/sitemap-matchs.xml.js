import {loadData} from './_lib/public-football.js';
import {getSnapshot} from './_lib/score-data.js';

const namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9';

export async function onRequestGet(context) {
  const sources = await Promise.allSettled([
    getSnapshot(context),
    loadData(context, 'match_results_archive'),
    loadData(context, 'prediction_fixtures'),
  ]);
  const now = Date.now();
  const ids = new Set();
  for (const [index, source] of sources.entries()) {
    if (source.status !== 'fulfilled' || !Array.isArray(source.value?.matches)) continue;
    for (const match of source.value.matches) {
      const id = String(match.id);
      if (!/^[1-9][0-9]*$/.test(id) || !match.home?.name || !match.away?.name) continue;
      if (index === 2 && !(Date.parse(match.kickoff) > now)) continue;
      ids.add(id);
      if (ids.size === 50000) break;
    }
    if (ids.size === 50000) break;
  }
  if (!ids.size) {
    return new Response('Sitemap temporairement indisponible', {
      status: 503, headers: {'cache-control': 'no-store'},
    });
  }
  const entries = [...ids].map(id => '  <url><loc>https://footchrono.com/matchs/' + id + '</loc></url>');
  return new Response(['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="' + namespace + '">',
    ...entries, '</urlset>', ''].join('\n'), {
    headers: {'content-type': 'application/xml; charset=utf-8', 'cache-control': 'public, max-age=300'},
  });
}
