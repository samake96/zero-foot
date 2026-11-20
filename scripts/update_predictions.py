#!/usr/bin/env python3
"""ZEROFOOT: build transparent pre-match comparisons; no unvalidated probabilities."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATCHES = ROOT / 'data' / 'matches.json'
STANDINGS = ROOT / 'data' / 'standings.json'
OUTPUT = ROOT / 'data' / 'predictions.json'
LEAGUES = {39: ('England', 'Premier League'), 140: ('Spain', 'Primera Division'),
           78: ('Germany', 'Bundesliga'), 135: ('Italy', 'Serie A'),
           61: ('France', 'Ligue 1')}

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def canonical(name):
    import unicodedata, re
    s = unicodedata.normalize('NFKD', name or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).casefold()
    s = re.sub(r'\b(fc|afc|sc|cf|ac|as|ssc|calcio|club|football)\b', '', s)
    return re.sub(r'[^a-z0-9]+', '', s)

def main():
    matches = load(MATCHES)
    if not isinstance(matches.get('matches'), list):
        raise SystemExit('Invalid matches.json: matches must be an array')
    standings = load(STANDINGS) if STANDINGS.exists() else {'leagues': []}
    by_id = {int(l['id']): l for l in standings.get('leagues', []) if l.get('teams') and str(l.get('id', '')).isdigit()}
    previews = []
    for m in matches['matches']:
        league = m.get('league') or {}
        lid = league.get('id')
        if lid not in LEAGUES or str(m.get('status', '')).upper() not in ('NS', 'TBD'):
            continue
        home, away = m.get('home') or {}, m.get('away') or {}
        if not home.get('name') or not away.get('name') or not m.get('kickoff'):
            continue
        standing = by_id.get(lid)
        # Exact normalized-name match only: do not silently infer team identities.
        rows = {canonical(t.get('name')): t for t in (standing or {}).get('teams', [])}
        a, b = rows.get(canonical(home['name'])), rows.get(canonical(away['name']))
        def stats(t):
            if not t: return None
            keys = ('rank', 'played', 'points', 'win', 'draw', 'lose', 'goals_for', 'goals_against', 'goal_diff')
            return {k: t.get(k) for k in keys}
        previews.append({
            'match_id': m.get('id'), 'kickoff': m['kickoff'],
            'league_id': lid, 'league': league.get('name'), 'country': league.get('country'),
            'home': {'name': home['name'], 'logo': home.get('logo'), 'stats': stats(a)},
            'away': {'name': away['name'], 'logo': away.get('logo'), 'stats': stats(b)},
            'analysis_status': 'standings_comparison' if a and b else 'insufficient_data',
            'probabilities': None,
            'note': 'Comparaison descriptive uniquement ; aucune probabilité validée.'
        })
    doc = {'source': 'ZEROFOOT', 'updated_at': datetime.now(timezone.utc).isoformat(),
           'matches_updated_at': matches.get('updated_at'),
           'standings_updated_at': standings.get('updated_at'),
           'method': 'Descriptive standings comparison; no prediction model validated',
           'previews': previews}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Created {len(previews)} previews, {sum(x["analysis_status"] == "standings_comparison" for x in previews)} with both teams matched')
    if not previews:
        print('No upcoming fixtures in target leagues in this snapshot; empty previews are valid.')

if __name__ == '__main__': main()
