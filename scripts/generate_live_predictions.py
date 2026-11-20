#!/usr/bin/env python3
"""ZEROFOOT V3.2: conservative experimental forecasts, no external calls."""
import json, math, re, unicodedata
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
LEAGUES = {39: 'PL', 140: 'PD', 78: 'BL1', 135: 'SA', 61: 'FL1'}
COUNTRIES = {39: 'England', 140: 'Spain', 78: 'Germany', 135: 'Italy', 61: 'France'}
# Exact canonical aliases, never fuzzy matching across different clubs.
ALIASES = {
 'bayern munchen': 'bayern munchen', 'fc bayern munchen': 'bayern munchen',
 'borussia dortmund': 'borussia dortmund', 'bvb': 'borussia dortmund',
 'inter': 'inter milan', 'internazionale': 'inter milan', 'fc internazionale milano': 'inter milan',
 'ac milan': 'ac milan', 'milan': 'ac milan',
 'psg': 'paris saint germain', 'paris saint germain fc': 'paris saint germain',
 'atletico madrid': 'atletico de madrid', 'club atletico de madrid': 'atletico de madrid',
 'real betis': 'real betis', 'real betis balompie': 'real betis',
 'manchester city': 'manchester city', 'manchester united': 'manchester united',
 'tottenham': 'tottenham hotspur', 'tottenham hotspur': 'tottenham hotspur',
 'wolves': 'wolverhampton wanderers', 'wolverhampton wanderers': 'wolverhampton wanderers',
 'newcastle united': 'newcastle united', 'brighton': 'brighton hove albion',
 'brighton hove albion': 'brighton hove albion',
 'bayer leverkusen': 'bayer 04 leverkusen', 'bayer 04 leverkusen': 'bayer 04 leverkusen',
 'rb leipzig': 'rasenballsport leipzig', 'rasenballsport leipzig': 'rasenballsport leipzig',
 '1 fc koln': 'fc koln', 'fc koln': 'fc koln',
 'freiburg': 'sc freiburg', 'sc freiburg': 'sc freiburg',
 'werder bremen': 'sv werder bremen', 'sv werder bremen': 'sv werder bremen',
 'stuttgart': 'vfb stuttgart', 'vfb stuttgart': 'vfb stuttgart',
 'athletic bilbao': 'athletic club', 'athletic club': 'athletic club',
 'real sociedad': 'real sociedad de futbol', 'real sociedad de futbol': 'real sociedad de futbol',
 'celta vigo': 'rc celta de vigo', 'rc celta de vigo': 'rc celta de vigo',
 'girona': 'girona', 'girona fc': 'girona',
 'rayo vallecano': 'rayo vallecano de madrid', 'rayo vallecano de madrid': 'rayo vallecano de madrid',
 'olympique lyonnais': 'olympique lyonnais', 'lyon': 'olympique lyonnais',
 'marseille': 'olympique de marseille', 'olympique de marseille': 'olympique de marseille',
 'rennes': 'stade rennais', 'stade rennais fc 1901': 'stade rennais',
 'lens': 'racing club de lens', 'racing club de lens': 'racing club de lens',
 'monaco': 'as monaco', 'as monaco fc': 'as monaco',
 'lille': 'lille osc', 'lille osc': 'lille osc',
 'strasbourg': 'rc strasbourg alsace', 'rc strasbourg alsace': 'rc strasbourg alsace',
 'brest': 'stade brestois 29', 'stade brestois 29': 'stade brestois 29',
 'nice': 'ogc nice', 'ogc nice': 'ogc nice',
}

def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii','ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    s = re.sub(r'\b(fc|afc|cf|calcio)\b$', '', s).strip()
    return ALIASES.get(s, s)

def dt(s):
    return datetime.fromisoformat(str(s).replace('Z','+00:00')).astimezone(timezone.utc)

def poisson(lam, max_goal=10):
    vals = [math.exp(-lam)]
    for i in range(1,max_goal+1): vals.append(vals[-1]*lam/i)
    vals[-1] += max(0., 1.-sum(vals))
    return vals

def forecast(rows, home, away):
    # Historical-season-only prototype. Smooth rates with league prior.
    hg = sum(r['home_goals'] for r in rows)/len(rows)
    ag = sum(r['away_goals'] for r in rows)/len(rows)
    hh = [r for r in rows if norm(r['home_name']) == home]
    aa = [r for r in rows if norm(r['away_name']) == away]
    if len(hh) < 5 or len(aa) < 5: return None
    prior = 8
    hf = (sum(r['home_goals'] for r in hh)+prior*hg)/(len(hh)+prior)
    hd = (sum(r['away_goals'] for r in hh)+prior*ag)/(len(hh)+prior)
    af = (sum(r['away_goals'] for r in aa)+prior*ag)/(len(aa)+prior)
    ad = (sum(r['home_goals'] for r in aa)+prior*hg)/(len(aa)+prior)
    lam_h = max(.15,min(4.,hf*ad/max(hg,.1)))
    lam_a = max(.15,min(4.,af*hd/max(ag,.1)))
    ph,pa = poisson(lam_h),poisson(lam_a)
    win = sum(ph[i]*pa[j] for i in range(11) for j in range(11) if i>j)
    draw = sum(ph[i]*pa[i] for i in range(11))
    lose = max(0.,1-win-draw)
    return {'home':round(win,4),'draw':round(draw,4),'away':round(lose,4)}, {'home':round(lam_h,3),'away':round(lam_a,3)}, {'home':len(hh),'away':len(aa)}

def main():
    historical = json.loads((DATA/'historical_matches.json').read_text(encoding='utf8'))['matches']
    fixtures = json.loads((DATA/'matches.json').read_text(encoding='utf8'))['matches']
    now = datetime.now(timezone.utc)
    grouped = defaultdict(list)
    for r in historical:
        if r.get('competition') in LEAGUES.values() and isinstance(r.get('home_goals'),int) and isinstance(r.get('away_goals'),int) and dt(r['utc_date']) < now:
            grouped[r['competition']].append(r)
    result=[]; skipped=defaultdict(int)
    for m in fixtures:
        lid=(m.get('league') or {}).get('id')
        if lid not in LEAGUES: skipped['unsupported_competition']+=1;continue
        league=m.get('league') or {}
        if league.get('country') != COUNTRIES[lid]: skipped['country_mismatch']+=1;continue
        if m.get('status') not in ('NS','TBD'): skipped['not_scheduled']+=1;continue
        try: kickoff=dt(m['kickoff'])
        except (ValueError,TypeError): skipped['invalid_date']+=1;continue
        if not (now < kickoff <= now+timedelta(days=7)): skipped['outside_next_7_days']+=1;continue
        rows=[r for r in grouped[LEAGUES[lid]] if dt(r['utc_date']) < kickoff]
        if len(rows)<100: skipped['insufficient_league_history']+=1;continue
        names={norm(r[k]) for r in rows for k in ('home_name','away_name')}
        home,away=norm((m.get('home') or {}).get('name')),norm((m.get('away') or {}).get('name'))
        if not home or not away or home==away or home not in names or away not in names:
            skipped['unmatched_team']+=1;continue
        calc=forecast(rows,home,away)
        if calc is None: skipped['insufficient_team_history']+=1;continue
        probs,expected,sample=calc
        result.append({'match_id':m.get('id'),'kickoff':m['kickoff'],'competition':LEAGUES[lid],
                       'league':league.get('name'),'home':(m.get('home') or {}).get('name'),
                       'away':(m.get('away') or {}).get('name'),'probabilities_1x2':probs,
                       'expected_goals':expected,'historical_samples':sample,
                       'model':'poisson_v32_prototype','experimental':True})
    output={'source':'ZEROFOOT','created_at':now.isoformat(),'model':'poisson_v32_prototype',
            'warning':'Experimental only; uses historical 2025-26 season, not current-season form. Not validated for future matches or betting.',
            'input_matches':len(fixtures),'predictions_count':len(result),'skipped':dict(skipped),
            'predictions':sorted(result,key=lambda x:x['kickoff'])}
    DATA.mkdir(exist_ok=True)
    (DATA/'live_predictions.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Generated',len(result),'experimental forecasts; skipped',dict(skipped))

if __name__=='__main__': main()
