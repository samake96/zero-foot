import {dateLabel, escape, loadData} from './public-football.js';

const aliases = {
  39: {'brighton': 'brighton hove albion', 'man united': 'manchester united',
    'man city': 'manchester city', 'wolves': 'wolverhampton wanderers', 'tottenham': 'tottenham hotspur'},
  140: {'atletico madrid': 'club atletico de madrid', 'osasuna': 'ca osasuna',
    'real sociedad': 'real sociedad de futbol', 'celta vigo': 'rc celta de vigo'},
  78: {'fsv mainz 05': '1 fsv mainz 05',
    'werder bremen': 'sv werder bremen', 'bayern munich': 'bayern munchen'},
  135: {'atalanta': 'atalanta bc', 'bologna': 'bologna 1909', 'inter': 'internazionale milano',
    'genoa': 'genoa cfc', 'sassuolo': 'us sassuolo calcio', 'udinese': 'udinese calcio'},
  61: {'angers': 'angers sco', 'marseille': 'olympique de marseille', 'rennes': 'stade rennais 1901',
    'lyon': 'olympique lyonnais', 'lens': 'racing club de lens', 'lille': 'lille osc',
    'psg': 'paris saint germain', 'strasbourg': 'rc strasbourg alsace'},
};

function teamKey(name, league) {
  const normalized = name.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ').trim().split(' ')
    .filter(word => !['fc', 'afc', 'cf'].includes(word)).join(' ');
  return Object.hasOwn(aliases[league], normalized) ? aliases[league][normalized] : normalized;
}

export async function historicalComparison(context, match) {
  const league = match.league?.id;
  if (!Object.hasOwn(aliases, league)) return '';
  let archive;
  try {
    archive = await loadData(context, 'openfootball-' + league);
  } catch {
    return '';
  }
  const before = match.kickoff?.slice(0, 10);
  if (!before || !Array.isArray(archive.matches)) return '';
  const home = teamKey(match.home.name, league);
  const away = teamKey(match.away.name, league);
  if (home === away) return '';
  const rows = archive.matches.filter(row => row[0] < before);
  const keys = row => [teamKey(row[1], league), teamKey(row[2], league)];
  const meetings = rows.filter(row => {
    const [first, second] = keys(row);
    return (first === home && second === away) || (first === away && second === home);
  }).slice(0, 5);
  const form = [home, away].map(team => rows.filter(row => keys(row).includes(team)).slice(0, 5));
  if (!meetings.length && form.every(matches => !matches.length)) return '';

  const table = meetings.length ? `<h3>Dernières confrontations dans le championnat</h3>
    <div class="table-wrap"><table><thead><tr><th scope="col">Date</th><th scope="col">Rencontre</th><th scope="col">Mi-temps</th><th scope="col">Score final</th></tr></thead>
    <tbody>${meetings.map(([date, first, second, full, half]) => `<tr>
      <td>${escape(dateLabel(date))}</td><th scope="row">${escape(first)} – ${escape(second)}</th>
      <td>${half?.join(' – ') ?? '—'}</td><td>${full.join(' – ')}</td></tr>`).join('')}</tbody></table></div>` : '';
  const cards = form.map((matches, index) => {
    if (!matches.length) return '';
    let scored = 0;
    let conceded = 0;
    const results = matches.map(row => {
      const position = keys(row).indexOf(index === 0 ? home : away);
      const goals = row[3][position];
      const against = row[3][1 - position];
      scored += goals;
      conceded += against;
      return goals === against ? 'N' : goals > against ? 'V' : 'D';
    });
    const name = index === 0 ? match.home.name : match.away.name;
    return `<article><h3>${escape(name)}</h3><p>${results.join(' · ')} · ${matches.length} match(s)</p>
      <p>${scored} buts marqués · ${conceded} encaissés</p></article>`;
  }).join('');
  return `<section><h2>Historique et forme</h2>
    <p>Championnat uniquement · saisons 2024/25 et 2025/26 · du plus récent au plus ancien.</p>
    ${table}<h3>Jusqu’à cinq matchs par équipe</h3><p>V = victoire, N = nul, D = défaite.</p>
    <div class="fc-news-grid">${cards}</div>
    <p>Source des résultats historiques <a href="https://github.com/openfootball/football.json">OpenFootball</a>.</p></section>`;
}
