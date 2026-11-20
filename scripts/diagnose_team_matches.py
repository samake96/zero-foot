#!/usr/bin/env python3
"""ZEROFOOT V3.5: read-only team identity diagnostic, no automatic aliasing."""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from generate_live_predictions import norm

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
LEAGUES = {39:'PL',140:'PD',78:'BL1',135:'SA',61:'FL1'}

def normalize(value):
    value = unicodedata.normalize('NFKD', str(value or '')).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ',value).strip()

def main():
    history = json.loads((DATA/'historical_matches.json').read_text(encoding='utf-8'))['matches']
    audit = json.loads((DATA/'prediction_audit.json').read_text(encoding='utf-8'))
    names = defaultdict(set)
    for m in history:
        code = m.get('competition')
        for key in ('home_name','away_name'):
            if m.get(key): names[code].add(m[key])
    report = []
    for item in audit.get('exclusions',[]):
        if item.get('reason') != 'unmatched_team': continue
        code = LEAGUES.get(int(item.get('league_id') or 0))
        candidates = names[code]
        sides = {}
        for side in ('home','away'):
            label = item.get(side) or ''
            exact = sorted(n for n in candidates if normalize(n) == normalize(label))
            aliases = sorted(n for n in candidates if norm(n) == norm(label))
            sides[side] = {'fixture_name':label,'exact_normalized_matches':exact,'model_identity_matches':aliases,'found_exact':bool(exact),'found_by_model':bool(aliases)}
        report.append({'match_id':item.get('match_id'),'competition':code,**sides})
    result = {'total_unmatched':len(report),'potentially_resolved':sum(r['home']['found_by_model'] and r['away']['found_by_model'] for r in report),'diagnosis':report,
              'note':'Identity checks use the same explicit aliases as the prediction engine. Historical sample thresholds are still enforced by that engine.'}
    dest = DATA/'team_identity_diagnostic.json'
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Diagnosed {len(report)} unmatched fixtures; wrote {dest}')
    for r in report:
        print(r['match_id'],r['competition'],
              f"HOME {r['home']['fixture_name']} => {r['home']['exact_normalized_matches']}",
              f"AWAY {r['away']['fixture_name']} => {r['away']['exact_normalized_matches']}")

if __name__ == '__main__': main()
