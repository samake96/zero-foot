import {competitionLinks, page} from '../_lib/public-football.js';

export function onRequestGet() {
  return page({
    path: '/classements',
    title: 'Classements des championnats de football',
    description: 'Consultez le classement, les points et la différence de buts en Premier League, Liga, Bundesliga, Serie A et Ligue 1.',
    heading: 'Classements de football',
    content: '<p>Classement par championnat, avec les points, les résultats et la différence de buts de chaque équipe.</p>'+competitionLinks(),
  });
}
