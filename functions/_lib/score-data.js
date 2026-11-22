import {loadData} from './public-football.js';

const liveStatuses = new Set(['1H','2H','HT','ET','BT','P','LIVE']);
const finalStatuses = new Set(['FT','AET','PEN']);

export async function getSnapshot(context) {
  const results = await Promise.allSettled([
    loadData(context, 'matches'),
    context.env.LIVE_SCORES?.get('latest', {type:'json',cacheTtl:30}),
  ]);
  return results.filter(result=>result.status==='fulfilled')
    .map(result=>result.value)
    .filter(value=>value?.available !== false && Array.isArray(value?.matches) && Number.isFinite(Date.parse(value.updated_at)))
    .sort((a,b)=>Date.parse(b.updated_at)-Date.parse(a.updated_at))[0];
}

export function matchScore(match) {
  return match.home?.goals != null && match.away?.goals != null
    ? match.home.goals + ' – ' + match.away.goals
    : '—';
}

export function matchStatus(match, snapshot) {
  if (finalStatuses.has(match.status)) return 'Terminé';
  if (liveStatuses.has(match.status)) {
    const age = Date.now() - Date.parse(snapshot?.updated_at);
    return snapshot?.interval_seconds === 120 && age >= 0 && age <= 240000
      ? 'En cours' : 'Dernier état en cours';
  }
  return {NS:'À venir', PST:'Reporté', CANC:'Annulé', ABD:'Interrompu'}[match.status]
    || 'Statut indisponible';
}
