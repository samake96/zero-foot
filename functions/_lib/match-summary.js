import {teamKey} from './match-center.js';
import {dateLabel, escape} from './public-football.js';

function quantity(count, singular, plural = singular + 's') {
  return count + ' ' + (count === 1 ? singular : plural);
}

function formParagraph(team, rows) {
  if (!rows.length) return '';
  const key = teamKey(team);
  let wins = 0, draws = 0, scored = 0, conceded = 0;
  for (const row of rows) {
    const side = row.teams.indexOf(key);
    const goals = row.goals[side];
    const against = row.goals[1 - side];
    wins += Number(goals > against);
    draws += Number(goals === against);
    scored += goals;
    conceded += against;
  }
  const last = rows[0];
  const position = last.teams.indexOf(key);
  const opponent = position === 0 ? last.away : last.home;
  const goals = last.goals[position];
  const against = last.goals[1 - position];
  const verb = goals > against ? 'a battu' : goals < against ? 's’est incliné face à' : 'a fait match nul contre';
  return `<p><strong>${escape(team)}</strong> affiche un bilan de ${quantity(wins, 'victoire')},
    ${quantity(draws, 'match nul', 'matchs nuls')} et ${quantity(rows.length - wins - draws, 'défaite')}
    sur la période du ${escape(dateLabel(rows.at(-1).date))} au ${escape(dateLabel(last.date))}.
    Le club a marqué ${quantity(scored, 'but')} et en a encaissé ${conceded}.
    Le ${escape(dateLabel(last.date))}, il ${verb} ${escape(opponent)} (${goals}–${against}).</p>`;
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
    ? `<p><strong>Face-à-face.</strong> Le ${escape(dateLabel(latest.date))},
      ${escape(latest.home)} et ${escape(latest.away)} ont terminé sur le score de ${latest.goals.join('–')}.</p>`
    : '';
  const article = editorialArticle(editorial, upcoming);
  const context = form || headToHead
    ? `${upcoming ? '' : '<h3>Contexte avant le coup d’envoi</h3>'}${form}${headToHead}`
    : '';
  return `<section id="resume" class="mc-section mc-summary"><h2>${title}</h2>${lead}${article}${upcoming && article ? '' : context}</section>`;
}
