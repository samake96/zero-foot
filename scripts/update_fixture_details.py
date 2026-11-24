"""Collect fixture detail in bounded batches for public match pages."""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1] / 'data'
FIELDS = ('statistics', 'lineups', 'events', 'players')

def collect():
    token = os.environ.get('API_FOOTBALL_KEY')
    if not token:
        print('Match detail skipped: configuration missing.')
        return
    output = ROOT / 'fixture-details.json'
    old = json.loads(output.read_text()) if output.exists() else {}
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=30)).date().isoformat()
    details = {key: row for key, row in old.items() if row['date'] >= cutoff}
    current = json.loads((ROOT / 'matches.json').read_text())['matches']
    archive = json.loads((ROOT / 'match_results_archive.json').read_text())['matches']
    candidates = [row for row in current + archive if
                  str(row.get('kickoff', ''))[:10] >= (now-timedelta(days=1)).date().isoformat()]
    ids = list(dict.fromkeys(str(row['id']) for row in candidates if str(row.get('id', '')).isdigit()))
    for start in range(0, min(len(ids), 400), 20):
        batch = ids[start:start + 20]
        request = Request('https://v3.football.api-sports.io/fixtures?' + urlencode({'ids':'-'.join(batch)}),
                          headers={'x-apisports-key':token})
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.load(response)
            if payload.get('errors') or not isinstance(payload.get('response'), list):
                print('Match detail provider returned an error.')
                break
        except (OSError, ValueError):
            print('Match detail provider unavailable.')
            break
        for row in payload['response']:
            fixture = row.get('fixture') or {}
            key = str(fixture.get('id'))
            if key not in batch:
                continue
            values = {field: row[field] for field in FIELDS if isinstance(row.get(field), list) and row[field]}
            if values:
                details[key] = {**details.get(key, {}), **values, 'date':fixture['date'][:10]}
    output.write_text(json.dumps(details, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

if __name__ == '__main__':
    collect()
