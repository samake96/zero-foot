import {dateLabel, escape, loadData} from './public-football.js';

function teamKey(name) {
  return name.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

export async function matchHistory(context, match) {
  const sources = await Promise.allSettled([
    loadData(context, 'verified-results'),
    loadData(context, 'match_results_archive'),
  ]);
  const matches = new Map();
  const kickoff = Date.parse(match.kickoff);
  const kickoffDay = match.kickoff?.slice(0, 10);
  for (const source of sources) {
    if (source.status !== 'fulfilled' || !Array.isArray(source.value?.matches)) continue;
    for (const row of source.value.matches) {
      const date = row.utc_date ?? row.kickoff;
      const home = row.home_name ?? row.home?.name;
      const away = row.away_name ?? row.away?.name;
      const goals = [row.home_goals ?? row.home?.goals, row.away_goals ?? row.away?.goals];
      if (!date || !home || !away || !goals.every(Number.isInteger)) continue;
      if (row.kickoff && !['FT', 'AET', 'PEN'].includes(row.status)) continue;
      const day = date.slice(0, 10);
      if (row.id === match.id || (date.length === 10 ? day >= kickoffDay : !(Date.parse(date) < kickoff))) continue;
      const teams = [teamKey(home), teamKey(away)];
      const key = [day, ...teams].join('|');
      const previous = matches.get(key);
      matches.set(key, {date, home, away, goals, teams,
        competition: row.competition ?? row.league?.name,
        source: row.source_url ?? previous?.source,
      });
    }
  }
  const rows = [...matches.values()].sort((a, b) => b.date.localeCompare(a.date));
  const home = teamKey(match.home.name);
  const away = teamKey(match.away.name);
  const cutoff = kickoff - 365 * 86400000;
  const recent = team => rows.filter(row => row.teams.includes(team) && Date.parse(row.date) >= cutoff).slice(0, 5);
  return {home: recent(home), away: recent(away),
    meetings: rows.filter(row => row.teams.includes(home) && row.teams.includes(away)).slice(0, 6)};
}

export function resultList(rows, team) {
  const key = team && teamKey(team);
  return '<ul class="mc-results">' + rows.map(row => {
    const position = row.teams.indexOf(key);
    const difference = row.goals[position] - row.goals[1 - position];
    const outcome = difference > 0 ? ['V', 'Victoire', 'win'] : difference < 0
      ? ['D', 'Défaite', 'loss'] : ['N', 'Nul', 'draw'];
    return `<li class="mc-result">
      <div class="mc-result-info"><time datetime="${escape(row.date.slice(0, 10))}">${escape(dateLabel(row.date))}</time>
      ${row.competition ? '<span>' + escape(row.competition) + '</span>' : ''}</div>
      <div class="mc-result-teams">${[row.home, row.away].map((name, i) =>
        `<div><span>${escape(name)}</span><strong>${row.goals[i]}</strong></div>`).join('')}</div>
      ${position >= 0 ? `<span class="mc-outcome ${outcome[2]}" aria-label="${outcome[1]}">${outcome[0]}</span>` : ''}
      ${row.source?.startsWith('https://') ? `<a class="mc-source" href="${escape(row.source)}">Source</a>` : ''}
    </li>`;
  }).join('') + '</ul>';
}

export function teamLogo(team) {
  return /^https:\/\/media\.api-sports\.io\/football\/teams\/\d+\.png$/.test(team.logo)
    ? `<img src="${escape(team.logo)}" width="48" height="48" alt="" referrerpolicy="no-referrer">` : '';
}
