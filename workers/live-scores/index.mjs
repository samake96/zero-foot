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

function providerError(errors, headers) {
  const details = JSON.stringify(errors).toLowerCase();
  if (/too many|per minute|rate.?limit/.test(details)) {
    const remaining = headers.get('x-ratelimit-requests-remaining');
    const quota = remaining && /^\d+$/.test(remaining) ? ' (daily requests remaining: ' + remaining + ')' : '';
    return 'Football provider refused the request: rate limit' + quota;
  }
  if (/quota|daily|per day/.test(details)) return 'Football provider refused the request: daily quota';
  if (/api.?key|unauthori[sz]ed|invalid token|authentication/.test(details)) return 'Football provider refused the request: authentication';
  if (/plan|subscription|suspend/.test(details)) return 'Football provider refused the request: subscription or account';
  return 'Football provider refused the request: unclassified API error';
}

async function fetchFixtures(url, key, request) {
  for (let attempt = 0; attempt < 2; attempt++) {
    let response;
    try {
      response = await request(url, {
        headers: {'x-apisports-key': key, accept: 'application/json'},
        signal: AbortSignal.timeout(12000),
      });
    } catch {
      if (attempt === 1) throw new Error('Football provider network failure');
    }
    if (response && response.status < 500) {
      if (!response.ok) throw new Error('Football provider HTTP ' + response.status);
      const data = await response.json().catch(() => null);
      if (Object.keys(data?.errors || {}).length) throw new Error(providerError(data.errors, response.headers));
      if (Array.isArray(data?.response)) return data.response;
      if (attempt === 1) throw new Error('Football provider returned invalid data: response array missing');
    }
    if (attempt === 1) throw new Error('Football provider HTTP ' + response.status);
    await new Promise(resolve => setTimeout(resolve, 1500));
  }
}

export async function collectScores(controller, env, request = fetch) {
  const intervalSeconds = allowedIntervals.get(controller.cron);
  if (!intervalSeconds || !env.API_FOOTBALL_KEY || !env.LIVE_SCORES) {
    throw new Error('Live scores collector is not configured');
  }
  const day = new Date(controller.scheduledTime).toISOString().slice(0, 10);
  const startedAt = new Date().toISOString();
  const url = new URL('https://v3.football.api-sports.io/fixtures');
  url.search = new URLSearchParams({date: day, timezone: 'UTC'}).toString();
  const fixtures = await fetchFixtures(url, env.API_FOOTBALL_KEY, request);
  const matches = fixtures.map(compactFixture);
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
