import {teamKey} from './match-center.js';
import {escape} from './public-football.js';

export function recentComparison(match, history) {
  const sides = [history.home, history.away];
  if (sides.some(rows => rows.length < 3)) return '';
  const count = Math.min(...sides.map(rows => rows.length));
  const teams = [match.home.name, match.away.name];
  const stats = sides.map((rows, index) => {
    const key = teamKey(teams[index]);
    const sample = rows.slice(0, count);
    const goals = sample.map(row => {
      const side = row.teams.indexOf(key);
      return [row.goals[side], row.goals[1 - side]];
    });
    return [goals.filter(([a,b]) => a>b).length,
      goals.reduce((sum,[a]) => sum+a,0), goals.reduce((sum,[,b]) => sum+b,0),
      goals.filter(([,b]) => b===0).length];
  });
  const labels = ['Victoires', 'Buts marqués', 'Buts encaissés', 'Matchs sans encaisser'];
  const [home, away] = stats;
  const striking = home[1] === away[1]
    ? 'Les deux équipes ont marqué autant de buts sur cette série.'
    : `${escape(teams[home[1] > away[1] ? 0 : 1])} a marqué davantage sur cette série (${Math.max(home[1],away[1])} buts contre ${Math.min(home[1],away[1])}).`;
  return `<h3>Comparaison sur ${count} matchs par équipe</h3><p>${striking}</p>
    <table><thead><tr><th scope="col">Indicateur</th>${teams.map(team=>`<th scope="col">${escape(team)}</th>`).join('')}</tr></thead>
    <tbody>${labels.map((label,i)=>`<tr><th scope="row">${label}</th><td>${home[i]}</td><td>${away[i]}</td></tr>`).join('')}</tbody></table>`;
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

export function matchSummary(match, status, editorial) {
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
  const article = editorialArticle(editorial, upcoming);
  const context = upcoming && !article
    ? `<p><strong>${escape(home)}</strong> reçoit <strong>${escape(away)}</strong>${match.league?.name ? ' en ' + escape(match.league.name) : ''}.</p>`
    : '';
  return `<section id="resume" class="mc-section mc-summary"><h2>${title}</h2>${lead}${article}${context}</section>`;
}
