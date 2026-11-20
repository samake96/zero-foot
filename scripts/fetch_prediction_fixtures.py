#!/usr/bin/env python3
"""Fetch fixtures for the next 7 days without touching the global calendar.
Uses daily API-Football queries, which avoid season-dependent league filtering.
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
all_matches = {}
for day_offset in range(8):
    day = (now + timedelta(days=day_offset)).date().isoformat()
    params = urllib.parse.urlencode({'date': day, 'timezone': 'UTC'})
    url = 'https://v3.football.api-sports.io/fixtures?' + params
    request = urllib.request.Request(url, headers={'x-apisports-key': KEY, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise SystemExit(f'Collection failed for {day}; previous data preserved: {type(exc).__name__}') from exc
    if payload.get('errors') or not isinstance(payload.get('response'), list):
        raise SystemExit(f'API error for {day}; previous data preserved: {payload.get("errors")}')
    for item in payload['response']:
        fixture = item.get('fixture') or {}
        league = item.get('league') or {}
        teams = item.get('teams') or {}
        status = fixture.get('status') or {}
        if league.get('id') not in LEAGUES or league.get('country', '').casefold() != LEAGUES[league['id']].casefold():
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

matches = sorted(all_matches.values(), key=lambda m: (m.get('kickoff') or '', m['id']))
if not matches:
    raise SystemExit('No eligible fixtures returned; previous calendar preserved')
output = {'source': 'API-Football', 'updated_at': now.isoformat(),
          'from_utc': now.date().isoformat(), 'to_utc': (now + timedelta(days=7)).date().isoformat(),
          'target_leagues': list(LEAGUES), 'matches': matches}
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Prediction calendar: {len(matches)} fixtures across {len(LEAGUES)} target leagues')
