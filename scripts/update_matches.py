import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data' / 'matches.json'
KEY = os.environ.get('API_FOOTBALL_KEY')
if not KEY:
    raise SystemExit('Missing API_FOOTBALL_KEY secret')

url = 'https://v3.football.api-sports.io/fixtures?date=' + datetime.now(timezone.utc).strftime('%Y-%m-%d')
request = urllib.request.Request(url, headers={'x-apisports-key': KEY, 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.load(response)
except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
    raise SystemExit(f'API request failed: {type(exc).__name__}') from exc

if payload.get('errors'):
    raise SystemExit('API returned errors; refusing to overwrite last valid data')
if not isinstance(payload.get('response'), list):
    raise SystemExit('Unexpected API response; refusing to overwrite data')

matches = []
for item in payload['response']:
    fixture = item.get('fixture') or {}
    league = item.get('league') or {}
    teams = item.get('teams') or {}
    goals = item.get('goals') or {}
    status = fixture.get('status') or {}
    matches.append({
        'id': fixture.get('id'),
        'kickoff': fixture.get('date'),
        'status': status.get('short'),
        'elapsed': status.get('elapsed'),
        'league': {'id': league.get('id'), 'name': league.get('name'), 'country': league.get('country')},
        'home': {'name': (teams.get('home') or {}).get('name'), 'logo': (teams.get('home') or {}).get('logo'), 'goals': goals.get('home')},
        'away': {'name': (teams.get('away') or {}).get('name'), 'logo': (teams.get('away') or {}).get('logo'), 'goals': goals.get('away')},
    })

DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps({'source': 'API-Football', 'updated_at': datetime.now(timezone.utc).isoformat(), 'date_utc': datetime.now(timezone.utc).strftime('%Y-%m-%d'), 'matches': matches}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Updated {len(matches)} fixtures')
