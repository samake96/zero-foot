#!/usr/bin/env python3
"""Collect seven days of fixtures for ZEROFOOT's five supported leagues.
Does not modify data/matches.json. Uses API-Football API_FOOTBALL_KEY.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data' / 'prediction_fixtures.json'
LEAGUES = {39: 'England', 140: 'Spain', 78: 'Germany', 135: 'Italy', 61: 'France'}
KEY = os.environ.get('API_FOOTBALL_KEY')
if not KEY:
    raise SystemExit('Missing API_FOOTBALL_KEY secret')

now = datetime.now(timezone.utc)
start = now.date()
end = (now + timedelta(days=7)).date()
all_matches = {}
errors = []
for league_id in LEAGUES:
    params = urllib.parse.urlencode({'league': league_id, 'from': start.isoformat(), 'to': end.isoformat(), 'timezone': 'UTC'})
    url = 'https://v3.football.api-sports.io/fixtures?' + params
    request = urllib.request.Request(url, headers={'x-apisports-key': KEY, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
        if payload.get('errors') or not isinstance(payload.get('response'), list):
            errors.append({'league_id': league_id, 'error': str(payload.get('errors') or 'Invalid response')})
            continue
        for item in payload['response']:
            fixture = item.get('fixture') or {}
            league = item.get('league') or {}
            teams = item.get('teams') or {}
            status = fixture.get('status') or {}
            if league.get('id') != league_id:
                continue
            match_id = fixture.get('id')
            if match_id is None:
                continue
            goals = item.get('goals') or {}
            all_matches[match_id] = {
                'id': match_id, 'kickoff': fixture.get('date'),
                'status': status.get('short'), 'elapsed': status.get('elapsed'),
                'league': {'id': league.get('id'), 'name': league.get('name'), 'country': league.get('country')},
                'home': {'name': (teams.get('home') or {}).get('name'), 'logo': (teams.get('home') or {}).get('logo'), 'goals': goals.get('home')},
                'away': {'name': (teams.get('away') or {}).get('name'), 'logo': (teams.get('away') or {}).get('logo'), 'goals': goals.get('away')},
            }
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        errors.append({'league_id': league_id, 'error': type(exc).__name__})

# Never replace previously valid data with partial results.
if errors:
    raise SystemExit('Fixture collection incomplete; existing data preserved: ' + json.dumps(errors))

matches = sorted(all_matches.values(), key=lambda m: (m.get('kickoff') or '', m['id']))
output = {'source': 'API-Football', 'updated_at': now.isoformat(), 'from_utc': start.isoformat(),
          'to_utc': end.isoformat(), 'target_leagues': list(LEAGUES), 'matches': matches}
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Prediction calendar: {len(matches)} fixtures for {len(LEAGUES)} leagues')
