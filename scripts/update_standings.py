#!/usr/bin/env python3
"""Fetch public league standings via API-Football; never print the API key."""
import json, os, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

LEAGUES = {39: 'Premier League', 140: 'La Liga', 78: 'Bundesliga', 135: 'Serie A', 61: 'Ligue 1'}
KEY = os.environ.get('API_FOOTBALL_KEY')
if not KEY:
    raise SystemExit('Missing GitHub secret API_FOOTBALL_KEY')
season = int(os.environ.get('FOOTBALL_SEASON', '2026'))
output = Path(__file__).resolve().parents[1] / 'data' / 'standings.json'
existing = {}
if output.exists():
    try:
        existing = {str(l['id']):l for l in json.loads(output.read_text(encoding='utf-8')).get('leagues',[]) if l.get('teams')}
    except (ValueError, OSError):
        pass
result = []
errors = []
for lid, label in LEAGUES.items():
    url = 'https://v3.football.api-sports.io/standings?' + urllib.parse.urlencode({'league': lid, 'season': season})
    try:
        req = urllib.request.Request(url, headers={'x-apisports-key': KEY, 'Accept': 'application/json', 'User-Agent': 'ZEROFOOT/1.0'})
        with urllib.request.urlopen(req, timeout=25) as resp:
            payload = json.load(resp)
        if payload.get('errors'):
            raise ValueError('API reported an error')
        response = payload.get('response') or []
        if not response:
            raise ValueError('No standings available for requested season')
        league = response[0]['league']
        groups = league.get('standings') or []
        if not groups or not groups[0]:
            raise ValueError('Empty standings')
        teams=[]
        for row in groups[0]:
            t=row.get('team') or {}; all_=row.get('all') or {}; goals=all_.get('goals') or {}
            teams.append({'rank':row.get('rank'),'name':t.get('name'),'logo':t.get('logo'),'played':all_.get('played'),'win':all_.get('win'),'draw':all_.get('draw'),'lose':all_.get('lose'),'goals_for':goals.get('for'),'goals_against':goals.get('against'),'goal_diff':row.get('goalsDiff'),'points':row.get('points'),'form':row.get('form')})
        result.append({'id':lid,'name':label,'season':season,'updated_at':datetime.now(timezone.utc).isoformat(),'teams':teams})
        print(f'{label}: {len(teams)} teams')
    except Exception as e:
        errors.append(f'{label}: {type(e).__name__} ({str(e)[:90]})')
        if str(lid) in existing:
            result.append(existing[str(lid)])
            print(f'{label}: keeping last valid snapshot')
        else:
            print(f'{label}: unavailable')
if not result:
    raise SystemExit('No standings returned and no existing snapshot; refusing to overwrite data')
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps({'source':'API-Football','updated_at':datetime.now(timezone.utc).isoformat(),'season_requested':season,'leagues':result},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Saved {len(result)} leagues; {len(errors)} retrieval issues')
