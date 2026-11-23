import {teamKey} from './match-center.js';
import {dateLabel, escape} from './public-football.js';

function formParagraph(team, rows) {
  if (!rows.length) return '';
  const key = teamKey(team);
  let wins = 0, draws = 0, scored = 0, conceded = 0, clean = 0;
  for (const row of rows) {
    const side = row.teams.indexOf(key);
    const goals = row.goals[side];
    const against = row.goals[1 - side];
    wins += Number(goals > against);
    draws += Number(goals === against);
    scored += goals;
    conceded += against;
    clean += Number(against === 0);
  }
  const last = rows[0];
  const position = last.teams.indexOf(key);
  const opponent = position === 0 ? last.away : last.home;
  return `<p><strong>${escape(team)}</strong> compte ${wins} V, ${draws} N et ${rows.length - wins - draws} D sur ${rows.length}
    ${rows.length === 1 ? 'match disponible' : 'matchs disponibles'}, avec ${scored} buts marqués, ${conceded} encaissés
    et ${clean} ${clean === 1 ? 'match sans encaisser' : 'matchs sans encaisser'}.
    Son dernier résultat disponible remonte au ${escape(dateLabel(last.date))} contre ${escape(opponent)}
    (${last.goals[position]}–${last.goals[1 - position]} du point de vue de ${escape(team)}).</p>`;
}

function editorialArticle(editorial, upcoming) {
  if (!editorial?.title || !Array.isArray(editorial.paragraphs)) return '';
  const links = (editorial.sources ?? []).filter(source => source.url?.startsWith('https://'))
    .map(source => `<li><a href="${escape(source.url)}">${escape(source.label)}</a></li>`).join('');
  return `<article class="mc-editorial">
    <p class="mc-kicker">${upcoming ? 'Analyse FootChrono' : 'Notre analyse avant le match'}</p>
    <h3>${escape(editorial.title)}</h3>
    ${editorial.paragraphs.map(paragraph => `<p>${escape(paragraph)}</p>`).join('')}
    ${links ? `<h4>Sources et lectures</h4><ul>${links}</ul>` : ''}
  </article>`;
}

export function matchSummary(match, history, status, editorial) {
  const home = match.home.name;
  const away = match.away.name;
  const goals = [match.home.goals, match.away.goals];
  const final = ['FT', 'AET', 'PEN'].includes(match.status);
  const upcoming = ['NS', 'TBD'].includes(match.status);
  const hasScore = goals.every(Number.isInteger);
  const title = upcoming ? 'Avant-match' : final ? 'Bilan du match' : 'Point sur le match';
  let lead = '';
  if (hasScore) {
    const result = escape(home) + ' ' + goals.join('–') + ' ' + escape(away);
    lead = `<p><strong>${result}</strong> · ${escape(status)}.</p>`;
  }
  const form = formParagraph(home, history.home) + formParagraph(away, history.away);
  const latest = history.meetings[0];
  const headToHead = latest
    ? `<p><strong>Dernier face-à-face archivé.</strong> Le ${escape(dateLabel(latest.date))},
      ${escape(latest.home)} et ${escape(latest.away)} ont terminé sur le score de ${latest.goals.join('–')}.</p>`
    : '';
  const context = form || headToHead
    ? `${upcoming ? '' : '<h3>Contexte avant le coup d’envoi</h3>'}${form}${headToHead}`
    : '<p>Les résultats historiques disponibles sont insuffisants pour établir une comparaison.</p>';
  return `<section id="resume" class="mc-section mc-summary"><h2>${title}</h2>${lead}${editorialArticle(editorial, upcoming)}${context}</section>`;
}
