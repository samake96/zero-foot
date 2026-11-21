import {competitions, competitionLinks, dateLabel, escape, loadData, page, standingsTable} from '../_lib/public-football.js';

export async function onRequestGet(context) {
  const competition = competitions.find(row => row.slug === context.params.competition);
  if (!competition) {
    return page({path:'/classements',title:'Classement introuvable',description:'Classements de football',
      heading:'Classement introuvable',content:competitionLinks(),status:404});
  }
  let league;
  try {
    const data = await loadData(context, 'standings');
    league = data.leagues.find(row => String(row.id) === String(competition.id));
  } catch {
    // A transient failure must not look like a valid empty standings page.
  }
  const title = 'Classement ' + competition.name;
  const path = '/classements/' + competition.slug;
  const description = 'Classement de ' + competition.name + ' avec les points, les victoires, les nuls et la différence de buts.';
  const season = Number(league?.season);
  const label = Number.isInteger(season) && season >= 1900 ? ' · Saison ' + season + '–' + (season + 1) : '';
  const teams = Array.isArray(league?.teams) ? league.teams : [];
  const content = teams.length
    ? '<p class="muted">Mis à jour le '+escape(dateLabel(league.updated_at))+' · football-data.org</p>'+
      standingsTable(teams)+'<p><a href="/#page=stats&amp;league='+competition.id+'">Comparer les équipes</a></p>'
    : '<p>Classement temporairement indisponible.</p>';
  return page({path,title,description,heading:title+label,content:content+competitionLinks(),status:teams.length?200:503,cache:300});
}
