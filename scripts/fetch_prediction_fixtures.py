#!/usr/bin/env python3
"""ZEROFOOT V3.4: collect accessible upcoming fixtures for experimental forecasts.

Keeps the general daily calendar untouched. API-Football free-tier date limits
are recorded rather than treated as fatal, while other API failures remain fatal.
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


def fetch(day):
    params = urllib.parse.urlencode({'date': day, 'timezone': 'UTC'})
    request = urllib.request.Request(
        'https://v3.football.api-sports.io/fixtures?' + params,
        headers={'x-apisports-key': KEY, 'Accept': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise SystemExit(f'Collection failed for {day}; previous data preserved: {type(exc).__name__}') from exc
    if not isinstance(payload, dict) or not isinstance(payload.get('response'), list):
        # API-Football may return errors with an empty response list, but a
        # malformed payload is not equivalent to a plan restriction.
        if not isinstance(payload, dict) or not payload.get('errors'):
            raise SystemExit(f'Unexpected API response for {day}; previous data preserved')
    errors = payload.get('errors') or {}
    if errors:
        message = ' '.join(str(v) for v in errors.values()) if isinstance(errors, dict) else str(errors)
        if 'free plans do not have access to this date' in message.lower():
            return None, message
        raise SystemExit(f'API error for {day}; previous data preserved: {message}')
    if not isinstance(payload.get('response'), list):
        raise SystemExit(f'Unexpected API response for {day}; previous data preserved')
    return payload['response'], None


def main():
    now = datetime.now(timezone.utc)
    matches_by_id = {}
    checked_dates, blocked_dates = [], []
    for offset in range(8):
        day = (now + timedelta(days=offset)).date().isoformat()
        items, restriction = fetch(day)
        if restriction is not None:
            blocked_dates.append({'date': day, 'reason': restriction})
            print(f'Skipping unavailable date {day}: {restriction}')
            continue
        checked_dates.append(day)
        for item in items:
            fixture = item.get('fixture') or {}
            league = item.get('league') or {}
            teams = item.get('teams') or {}
            status = fixture.get('status') or {}
            lid = league.get('id')
            try:
                lid = int(lid)
            except (TypeError, ValueError):
                continue
            if lid not in LEAGUES or str(league.get('country') or '').casefold() != LEAGUES[lid].casefold():
                continue
            match_id = fixture.get('id')
            if match_id is None or not fixture.get('date'):
                continue
            goals = item.get('goals') or {}
            matches_by_id[match_id] = {
                'id': match_id, 'kickoff': fixture['date'],
                'status': status.get('short'), 'elapsed': status.get('elapsed'),
                'league': {'id': lid, 'name': league.get('name'), 'country': league.get('country')},
                'home': {'name': (teams.get('home') or {}).get('name'),
                         'logo': (teams.get('home') or {}).get('logo'), 'goals': goals.get('home')},
                'away': {'name': (teams.get('away') or {}).get('name'),
                         'logo': (teams.get('away') or {}).get('logo'), 'goals': goals.get('away')},
            }

    matches = sorted(matches_by_id.values(), key=lambda m: (m['kickoff'], str(m['id'])))
    if not checked_dates:
        raise SystemExit('No accessible dates; previous prediction calendar preserved')
    if not matches:
        raise SystemExit('No target-league fixtures on accessible dates; previous prediction calendar preserved')
    output = {
        'source': 'API-Football', 'updated_at': now.isoformat(),
        'from_utc': now.date().isoformat(),
        'to_utc': (now + timedelta(days=7)).date().isoformat(),
        'target_leagues': list(LEAGUES),
        'checked_dates': checked_dates, 'blocked_dates': blocked_dates,
        'matches': matches,
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Prediction calendar: {len(matches)} fixtures; {len(checked_dates)} accessible dates; {len(blocked_dates)} blocked dates')


if __name__ == '__main__':
    main()
