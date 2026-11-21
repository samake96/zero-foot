const SNAPSHOT = 'latest';
const allowedIntervals = new Map([
  ['*/30 * * * *', 1800],
  ['*/2 * * * *', 120],
]);

function compactFixture({fixture, league, teams, goals}) {
  if (!Number.isSafeInteger(fixture?.id) || !Number.isFinite(Date.parse(fixture.date))
      || !fixture.status?.short || !teams?.home?.name || !teams?.away?.name) {
    throw new Error('Invalid fixture record');
  }
  return {
    id: fixture.id,
    kickoff: fixture.date,
    status: fixture.status.short,
    elapsed: fixture.status.elapsed,
    league: {id: league?.id, name: league?.name, country: league?.country},
    home: {name: teams.home.name, goals: goals?.home, logo: teams.home.logo},
    away: {name: teams.away.name, goals: goals?.away, logo: teams.away.logo},
  };
}

export async function collectScores(controller, env, request = fetch) {
  const intervalSeconds = allowedIntervals.get(controller.cron);
  if (!intervalSeconds || !env.API_FOOTBALL_KEY || !env.LIVE_SCORES) {
    throw new Error('Live scores collector is not configured');
  }
  const day = new Date(controller.scheduledTime).toISOString().slice(0, 10);
  const startedAt = new Date().toISOString();
  const url = new URL('https://v3.football.api-sports.io/fixtures');
  url.search = new URLSearchParams({date: day, timezone: 'UTC'});
  const response = await request(url, {
    headers: {'x-apisports-key': env.API_FOOTBALL_KEY, accept: 'application/json'},
    signal: AbortSignal.timeout(20000),
  });
  if (!response.ok) throw new Error('Football provider HTTP ' + response.status);
  const data = await response.json();
  if (!Array.isArray(data.response) || Object.keys(data.errors || {}).length) {
    throw new Error('Football provider returned invalid data or refused the request');
  }
  const matches = data.response.map(compactFixture);
  if (matches.length !== new Set(matches.map(match => match.id)).size) {
    throw new Error('Football provider returned duplicate fixtures');
  }
  await env.LIVE_SCORES.put(SNAPSHOT, JSON.stringify({
    available: true,
    updated_at: startedAt,
    date_utc: day,
    interval_seconds: intervalSeconds,
    matches,
  }), {expirationTtl: 14400});
}

export default {
  async scheduled(controller, env) {
    await collectScores(controller, env);
  },
};
