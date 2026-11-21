import assert from 'node:assert/strict';
import test from 'node:test';
import {collectScores} from './index.mjs';

const schedule = {cron: '*/30 * * * *', scheduledTime: Date.parse('2026-11-21T19:00:00Z')};
const fixture = {
  fixture: {id: 123, date: '2026-11-21T18:00:00Z', status: {short: '2H', elapsed: 60}},
  teams: {home: {name: 'Home'}, away: {name: 'Away'}},
  league: {id: 39, name: 'Premier League', country: 'England'},
  goals: {home: 1, away: 0},
};

test('one provider call stores the score and final status for the configured interval', async () => {
  for (const [cron, seconds, status] of [['*/30 * * * *', 1800, '2H'], ['*/2 * * * *', 120, 'FT']]) {
    const writes = [];
    let calls = 0;
    await collectScores({...schedule, cron}, {
      API_FOOTBALL_KEY: 'test-key',
      LIVE_SCORES: {put: async (...args) => writes.push(args)},
    }, async (url, options) => {
      calls++;
      assert.equal(url.searchParams.get('date'), '2026-11-21');
      assert.equal(options.headers['x-apisports-key'], 'test-key');
      return Response.json({response: [
        {...fixture, fixture: {...fixture.fixture, status: {short: status, elapsed: 60}}},
      ]});
    });
    assert.equal(calls, 1);
    const [[key, body]] = writes;
    const snapshot = JSON.parse(body);
    assert.equal(key, 'latest');
    assert.equal(snapshot.interval_seconds, seconds);
    assert.equal(snapshot.matches[0].status, status);
    assert.equal(snapshot.matches[0].home.goals, 1);
    assert.equal(snapshot.matches[0].away.goals, 0);
    assert(!body.includes('test-key'));
  }
});

test('provider failure, quota errors, malformed results and unsupported schedules preserve the snapshot', async () => {
  const env = {
    API_FOOTBALL_KEY: 'test-key',
    LIVE_SCORES: {put: () => assert.fail('Must preserve the previous snapshot')},
  };
  const scenarios = [
    [schedule, () => new Response(null, {status: 429}), /HTTP 429/],
    [schedule, () => Response.json({response: [], errors: {quota: 'Exceeded'}}), /refused/],
    [schedule, () => Response.json({response: [{fixture: {id: 123}}]}), /Invalid fixture/],
    [schedule, () => Response.json({response: [fixture, fixture]}), /duplicate/],
    [{...schedule, cron: '* * * * *'}, () => assert.fail('Unexpected fetch'), /not configured/],
  ];
  for (const [controller, request, expected] of scenarios) {
    await assert.rejects(collectScores(controller, env, request), expected);
  }
});
