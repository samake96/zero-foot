#!/usr/bin/env python3
"""Collect current league tables from football-data.org, keeping valid snapshots."""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LEAGUES = {'PL': (39, 'Premier League'), 'PD': (140, 'La Liga'), 'BL1': (78, 'Bundesliga'), 'SA': (135, 'Serie A'), 'FL1': (61, 'Ligue 1')}
TOKEN = os.environ.get('FOOTBALL_DATA_TOKEN')
if not TOKEN:
    raise SystemExit('Missing repository secret FOOTBALL_DATA_TOKEN')
output = Path(__file__).resolve().parents[1] / 'data' / 'standings.json'
existing = {}
if output.exists():
    try:
        old = json.loads(output.read_text(encoding='utf-8'))
        existing = {str(item['id']): item for item in old.get('leagues', []) if item.get('teams')}
    except (OSError, ValueError, KeyError, TypeError):
        pass
now = datetime.now(timezone.utc).isoformat()
result = []
failures = []
for code, (lid, label) in LEAGUES.items():
    try:
        req = urllib.request.Request(f'https://api.football-data.org/v4/competitions/{code}/standings', headers={'X-Auth-Token': TOKEN, 'Accept': 'application/json', 'User-Agent': 'ZEROFOOT/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
        groups = payload.get('standings') or []
        table = next((group.get('table') for group in groups if group.get('type') == 'TOTAL' and group.get('table')), None)
        if not table:
            raise ValueError('No TOTAL standings returned')
        teams = []
        for row in table:
            team = row.get('team') or {}
            teams.append({'rank': row.get('position'), 'name': team.get('name'), 'logo': team.get('crest'), 'played': row.get('playedGames'), 'win': row.get('won'), 'draw': row.get('draw'), 'lose': row.get('lost'), 'goals_for': row.get('goalsFor'), 'goals_against': row.get('goalsAgainst'), 'goal_diff': row.get('goalDifference'), 'points': row.get('points'), 'form': row.get('form')})
        season = payload.get('season') or {}
        result.append({'id': lid, 'name': label, 'season': int(season['startDate'][:4]) if season.get('startDate') else None, 'updated_at': now, 'teams': teams})
        print(f'{label}: {len(teams)} teams collected')
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
        reason = f'HTTP {exc.code}' if isinstance(exc, urllib.error.HTTPError) else type(exc).__name__
        failures.append(f'{label}: {reason}')
        if str(lid) in existing:
            result.append(existing[str(lid)])
            print(f'{label}: retained existing snapshot ({reason})')
        else:
            print(f'{label}: unavailable ({reason})')
if not result:
    raise SystemExit('No tables retrieved; existing standings.json preserved')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({'source': 'football-data.org', 'updated_at': now, 'leagues': result}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Saved {len(result)} leagues; {len(failures)} collection issues')
