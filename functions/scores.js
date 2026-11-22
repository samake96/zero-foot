import {competitions, escape, page} from './_lib/public-football.js';

import {getSnapshot, matchScore, matchStatus} from './_lib/score-data.js';

export async function onRequestGet(context) {
  const snapshot = await getSnapshot(context);
  const groups = new Map();
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
      const score = matchScore(match);
      const status = matchStatus(match, snapshot);
      const href = '/matchs/' + encodeURIComponent(String(match.id));
      return `<tr><th scope="row"><a href="${escape(href)}">${escape(match.home?.name)} – ${escape(match.away?.name)}</a></th>
<td class="score">${escape(score)}</td><td>${escape(status)}</td></tr>`;
    }).join('')}</tbody></table></div></section>`;
  }).join('');
  return page({
    path:'/scores',title:'Scores et résultats des matchs de football',
    description:'Retrouvez les scores, résultats et matchs à venir des grands championnats de football sur FootChrono.',
    heading:'Scores et matchs de football',
    content:'<p><a href="/#page=matches">Ouvrir le direct et tous les filtres</a></p>'+
      (content || '<p>'+(snapshot?'Aucun match disponible.':'Scores temporairement indisponibles.')+'</p>'),
    status:snapshot?200:503,cache:30, ads:Boolean(content),
  });
}
