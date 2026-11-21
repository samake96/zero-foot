import {competitions, dateLabel, escape, loadData, page} from './_lib/public-football.js';

const liveStatuses = new Set(['1H','2H','HT','ET','BT','P','LIVE']);
const finalStatuses = new Set(['FT','AET','PEN']);

async function getSnapshot(context) {
  const results = await Promise.allSettled([
    loadData(context, 'matches'),
    context.env.LIVE_SCORES?.get('latest', {type:'json',cacheTtl:30}),
  ]);
  return results.filter(result=>result.status==='fulfilled')
    .map(result=>result.value)
    .filter(value=>Array.isArray(value?.matches) && Number.isFinite(Date.parse(value.updated_at)))
    .sort((a,b)=>Date.parse(b.updated_at)-Date.parse(a.updated_at))[0];
}

export async function onRequestGet(context) {
  const snapshot = await getSnapshot(context);
  const groups = new Map();
  const recent = snapshot?.interval_seconds === 120 && Date.now() - Date.parse(snapshot.updated_at) <= 240000;
  for (const match of snapshot?.matches || []) {
    const key = String(match.league?.id);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(match);
  }
  const featured = [{id:2,name:'Ligue des champions'}, ...competitions, {id:5,name:'Ligue des nations'}];
  const order = [...new Set([...featured.map(row=>String(row.id)),...groups.keys()])];
  const selected = order.filter(key=>groups.has(key)).slice(0,12);
  const content = selected.map(key=>{
    const matches=groups.get(key);
    const name=featured.find(row=>String(row.id)===key)?.name || matches[0].league?.name || 'Autres matchs';
    return `<section><h2>${escape(name)}</h2><div class="table-wrap"><table><thead><tr>
<th scope="col">Match</th><th scope="col">Score</th><th scope="col">Statut</th></tr></thead><tbody>${matches.slice(0,30).map(match=>{
      const score=match.home?.goals!=null&&match.away?.goals!=null ? match.home.goals+' – '+match.away.goals : '—';
      const status=finalStatuses.has(match.status)?'Terminé':liveStatuses.has(match.status)?
        (recent?'En cours':'Dernier état en cours'):match.status==='NS'?'À venir':match.status==='PST'?'Reporté':'Autre statut';
      const href='/#page=matches&match='+encodeURIComponent(String(match.id));
      return `<tr><th scope="row"><a href="${escape(href)}">${escape(match.home?.name)} – ${escape(match.away?.name)}</a></th>
<td class="score">${escape(score)}</td><td>${escape(status)}</td></tr>`;
    }).join('')}</tbody></table></div></section>`;
  }).join('');
  const updated = snapshot ? '<p class="muted">Dernière collecte · '+escape(dateLabel(snapshot.updated_at,true))+' UTC</p>' : '';
  return page({
    path:'/scores',title:'Scores et résultats des matchs de football',
    description:'Retrouvez les scores, résultats et matchs à venir des grands championnats de football sur MATCHSCOPE.',
    heading:'Scores et matchs de football',
    content:updated+'<p><a href="/#page=matches">Ouvrir le direct et tous les filtres</a></p>'+
      (content || '<p>'+(snapshot?'Aucun match dans la dernière collecte.':'Scores temporairement indisponibles.')+'</p>'),
    status:snapshot?200:503,cache:30,
  });
}
