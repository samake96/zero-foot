import {matchHistory, resultList, teamId, teamKey, teamLogo} from '../_lib/match-center.js';
import {matchCenterStyle} from '../_lib/match-center-style.js';
import {competitions, dateLabel, escape, loadData, page} from '../_lib/public-football.js';
import {getSnapshot} from '../_lib/score-data.js';

export async function onRequestGet(context) {
  const id = context.params.id;
  const path = '/equipes/' + encodeURIComponent(id);
  const valid = /^[1-9][0-9]*$/.test(id);
  const sources = valid ? await Promise.allSettled([
    getSnapshot(context),
    loadData(context, 'prediction_fixtures'),
    loadData(context, 'match_results_archive'),
    loadData(context, 'standings'),
  ]) : [];
  const values = sources.map(source => source.status === 'fulfilled' ? source.value : undefined);
  const fixtures = new Map();
  let team;
  for (const source of values.slice(0, 3)) {
    for (const fixture of source?.matches ?? []) {
      const selected = [fixture.home, fixture.away].find(candidate => teamId(candidate) === id);
      if (!selected?.name) continue;
      team ??= selected;
      if (/^[1-9][0-9]*$/.test(String(fixture.id)) && !fixtures.has(fixture.id)) fixtures.set(fixture.id, fixture);
    }
  }
  if (!team) {
    const unavailable = valid && values.slice(0,3).some(value => !Array.isArray(value?.matches));
    const title = unavailable ? 'Équipe temporairement indisponible' : 'Équipe introuvable';
    return page({path, title, heading:title, description:title,
      content:'<p><a href="/scores">Voir les scores</a></p>', status:unavailable ? 503 : 404, ads:false});
  }

  const now = Date.now();
  const key = teamKey(team.name);
  const upcoming = [...fixtures.values()].filter(fixture =>
    ['NS','TBD'].includes(fixture.status) && Date.parse(fixture.kickoff) > now)
    .sort((first, second) => Date.parse(first.kickoff) - Date.parse(second.kickoff)).slice(0,5);
  const history = await matchHistory(context, {home:team, away:{name:''}, kickoff:new Date(now).toISOString()});
  const standings = (values[3]?.leagues ?? []).flatMap(league => {
    const row = league.teams?.find(entry => teamKey(entry.name) === key);
    const competition = competitions.find(entry => entry.id === league.id);
    return row && competition ? [{row, competition}] : [];
  });
  const calendar = upcoming.length ? '<ul class="mc-results">' + upcoming.map(fixture =>
    `<li class="mc-result">
      <div class="mc-result-info">${escape(dateLabel(fixture.kickoff,true))} UTC · ${escape(fixture.league?.name)}</div>
      <a href="/matchs/${fixture.id}">${escape(fixture.home?.name)} – ${escape(fixture.away?.name)}</a>
    </li>`).join('') + '</ul>' : '<p>Aucun prochain match dans le calendrier disponible.</p>';
  return page({
    path, title:team.name + ' | Calendrier et résultats', heading:team.name,
    description:'Retrouvez les prochains matchs, les résultats récents et le classement disponible de ' + team.name + '.',
    content:`<div class="mc-center">
      <div class="mc-kicker">${teamLogo(team)}</div>
      <nav class="mc-nav" aria-label="Dans cette fiche équipe">
        <a href="#calendrier">Calendrier</a><a href="#resultats">Résultats</a>
        ${standings.length ? '<a href="#classement">Classement</a>' : ''}
      </nav>
      <section id="calendrier" class="mc-section"><h2>Prochains matchs</h2>${calendar}</section>
      <section id="resultats" class="mc-section"><h2>Derniers résultats</h2>
        ${history.home.length ? resultList(history.home,team.name) : '<p>Aucun résultat récent dans les archives disponibles.</p>'}
      </section>
      ${standings.length ? `<section id="classement" class="mc-section"><h2>Classement</h2><ul class="mc-results">
        ${standings.map(({row, competition}) => `<li class="mc-result"><a href="/classements/${competition.slug}">${escape(competition.name)}</a>
          <strong>${escape(row.rank)}e · ${escape(row.points)} pts</strong></li>`).join('')}</ul></section>` : ''}
      <p><a href="/scores">Tous les scores</a></p></div>`,
    ads:false, style:matchCenterStyle,
  });
}
