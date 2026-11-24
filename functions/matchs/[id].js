import {matchSummary, recentComparison} from '../_lib/match-summary.js';
import {matchCenterStyle} from '../_lib/match-center-style.js';
import {matchHistory, resultList, teamLink, teamLogo} from '../_lib/match-center.js';
import {historicalComparison} from '../_lib/openfootball.js';
import {competitions, dateLabel, escape, loadData, page} from '../_lib/public-football.js';
import {getSnapshot, matchScore, matchStatus} from '../_lib/score-data.js';

async function publishedAnalysis(db, matchId) {
  if (!db) return null;
  try {
    const row = await db.prepare(
      "SELECT content FROM match_editorial_revisions WHERE match_id = ? AND state = 'published'"
    ).bind(matchId).first();
    return row ? JSON.parse(row.content) : null;
  } catch {
    return null;
  }
}


const statLabels = {
  'Ball Possession':'Possession', 'Total Shots':'Tirs', 'Shots on Goal':'Tirs cadrés',
  'Shots off Goal':'Tirs non cadrés', 'Blocked Shots':'Tirs contrés', 'Shots insidebox':'Tirs dans la surface',
  'Corner Kicks':'Corners', 'Total passes':'Passes', 'Passes accurate':'Passes réussies',
  'Passes %':'Précision des passes', 'Fouls':'Fautes', 'Offsides':'Hors-jeu',
  'Yellow Cards':'Cartons jaunes', 'Red Cards':'Cartons rouges', 'Goalkeeper Saves':'Arrêts',
};
function detailSections(detail, match) {
  if (!detail) return [];
  const sections = [];
  const add = (id, title, body) => {
    if (body) sections.push([id, title, '<section id="' + id + '" class="mc-section"><h2>' + title + '</h2>' + body + '</section>']);
  };
  const ordered = (rows, team) => rows?.find(row =>
    row.team?.name === team.name || (team.logo && row.team?.logo === team.logo));
  const stats = [match.home, match.away].map(team => new Map(
    (ordered(detail.statistics, team)?.statistics || []).map(row => [row.type, row.value])));
  const statRows = Object.entries(statLabels).filter(([key]) => stats.some(side => side.get(key) != null))
    .map(([key, label]) => '<tr><th scope="row">' + label + '</th>' +
      stats.map(side => '<td>' + escape(side.get(key) ?? '—') + '</td>').join('') + '</tr>').join('');
  if (statRows) add('statistiques', 'Statistiques', '<div class="table-wrap"><table><thead><tr><th scope="col">Indicateur</th>' +
    [match.home,match.away].map(team => '<th scope="col">' + escape(team.name) + '</th>').join('') +
    '</tr></thead><tbody>' + statRows + '</tbody></table></div>');
  const lineups = (detail.lineups || []).filter(row => row.startXI?.length).map(row =>
    '<div><h3>' + escape(row.team?.name || 'Équipe') + '</h3>' +
    (row.formation ? '<p>Formation : ' + escape(row.formation) + '</p>' : '') +
    '<ol>' + row.startXI.map(({player}) => '<li>' + escape([player?.number, player?.name].filter(value => value != null).join(' ')) + '</li>').join('') + '</ol></div>').join('');
  if (lineups) add('compositions', 'Compositions', '<div class="mc-form">' + lineups + '</div>');
  const eventLabels = {Goal:'But', Card:'Carton', subst:'Remplacement', Var:'VAR'};
  const timeline = (detail.events || []).filter(row => row.time?.elapsed != null && Object.hasOwn(eventLabels,row.type)).map(row => {
    const minute = row.time.elapsed + (row.time.extra ? '+' + row.time.extra : '') + '′';
    return '<li><strong>' + escape(minute) + '</strong> ' +
      escape([eventLabels[row.type], row.team?.name, row.player?.name, row.assist?.name].filter(Boolean).join(' · ')) + '</li>';
  }).join('');
  if (timeline) add('chronologie', 'Chronologie', '<ol>' + timeline + '</ol>');
  return sections;
}

const scoresLink = '<p><a href="/scores">Tous les scores</a></p>';

export async function onRequestGet(context) {
  const id = context.params.id;
  const path = '/matchs/' + encodeURIComponent(id);
  let snapshot;
  let match;
  let archiveUnavailable = false;

  if (/^[1-9][0-9]*$/.test(id)) {
    snapshot = await getSnapshot(context);
    match = snapshot?.matches.find(row => String(row.id) === id);
    if (!match) {
      const sources = await Promise.allSettled([
        loadData(context, 'match_results_archive'),
        loadData(context, 'prediction_fixtures'),
      ]);
      for (const [index, source] of sources.entries()) {
        if (source.status !== 'fulfilled' || !Array.isArray(source.value.matches)) {
          archiveUnavailable = true;
          continue;
        }
        match = source.value.matches.find(row => String(row.id) === id &&
          (index === 0 || Date.parse(row.kickoff) > Date.now()));
        if (match) {
          snapshot = source.value;
          break;
        }
      }
    }
  }

  if (!match?.home?.name || !match?.away?.name) {
    const status = /^[1-9][0-9]*$/.test(id) && (!snapshot || archiveUnavailable) ? 503 : 404;
    const heading = status === 503 ? 'Match temporairement indisponible' : 'Match introuvable';
    return page({path, title:heading, heading, description:heading, content:scoresLink, status, ads:false});
  }

  const heading = match.home.name + ' – ' + match.away.name;
  const competition = competitions.find(row => row.id === match.league?.id);
  const league = competition?.name || match.league?.name || 'Football';
  const date = dateLabel(match.kickoff, true);
  const score = matchScore(match);
  const status = matchStatus(match, snapshot);
  const standings = competition
    ? '<p><a href="/classements/' + competition.slug + '">Classement ' + escape(league) + '</a></p>'
    : '';
  const [history, archive, editorials, published, details] = await Promise.all([
    matchHistory(context, match),
    historicalComparison(context, match),
    loadData(context, 'match-editorials').catch(() => null),
    publishedAnalysis(context.env.COMMUNITY_DB, id),
    loadData(context, 'fixture-details').catch(() => null),
  ]);
  const upcoming = match.status === 'NS' || match.status === 'TBD';
  const scoreboard = `<section class="mc-section" aria-label="Tableau du match">
      <p class="mc-kicker">${escape(league)} <span aria-hidden="true">·</span> ${escape(date)} UTC</p>
      <div class="mc-scoreboard">
        <div>${teamLogo(match.home)}<strong>${teamLink(match.home)}</strong></div>
        <div><strong class="mc-score">${escape(upcoming ? 'VS' : score)}</strong><span class="mc-status">${escape(status)}</span></div>
        <div>${teamLogo(match.away)}<strong>${teamLink(match.away)}</strong></div>
      </div>
    </section>`;
  const sections = [['resume', 'Résumé', matchSummary(match, status, published ?? editorials?.[id])]];
  sections.push(...detailSections(details?.[id], match));
  if (history.home.length || history.away.length) {
    sections.push(['forme', 'Forme', `<section id="forme" class="mc-section">
      <h2>Derniers résultats</h2>
      ${recentComparison(match, history)}
      <div class="mc-form">${[[match.home.name, history.home], [match.away.name, history.away]]
        .filter(([, rows]) => rows.length)
        .map(([team, rows]) => `<div><h3>${escape(team)}</h3>${resultList(rows, team)}</div>`).join('')}</div></section>`]);
  }
  if (history.meetings.length) {
    sections.push(['confrontations', 'Face-à-face', `<section id="confrontations" class="mc-section">
      <h2>Confrontations directes</h2>${resultList(history.meetings)}</section>`]);
  }
  if (archive) {
    sections.push(['archives', 'Archives', `<section id="archives" class="mc-section">${archive}</section>`]);
  }
  return page({
    path, title:heading + ' | Score et résultat', heading,
    description:heading + ', ' + league + '. ' + status + (score === '—' ? '.' : ' · ' + score + '.'),
    content:`<div class="mc-center">
      ${scoreboard}
      <nav class="mc-nav" aria-label="Dans cette fiche">${sections.map(([anchor, label]) =>
        `<a href="#${anchor}">${label}</a>`).join('')}</nav>
      ${sections.map(([, , html]) => html).join('')}
      ${standings}${scoresLink}</div>`,
    cache:30, ads:false, style:matchCenterStyle,
  });
}
