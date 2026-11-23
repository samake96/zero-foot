import {historicalComparison} from '../_lib/openfootball.js';
import {competitions, dateLabel, escape, loadData, page} from '../_lib/public-football.js';
import {getSnapshot, matchScore, matchStatus} from '../_lib/score-data.js';

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
  const history = await historicalComparison(context, match);
  return page({
    path, title:heading + ' | Score et résultat', heading,
    description:heading + ', ' + league + '. ' + status + (score === '—' ? '.' : ' · ' + score + '.'),
    content:'<p>' + escape(league) + ' · ' + escape(date) + ' UTC</p>' +
      '<p><strong class="score">' + escape(score) + '</strong> · ' + escape(status) + '</p>' +
      history + standings + scoresLink,
    cache:30, ads:false,
  });
}
