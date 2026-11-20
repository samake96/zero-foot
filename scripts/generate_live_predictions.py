#!/usr/bin/env python3
"""ZEROFOOT V3.3 — forecasts with strict data checks and auditable exclusions.
Offline, standard library only. Run from any working directory.
"""
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
LEAGUES = {39: ('PL', 'England'), 140: ('PD', 'Spain'), 78: ('BL1', 'Germany'),
           135: ('SA', 'Italy'), 61: ('FL1', 'France')}
# Explicit, reviewed synonyms; do not use fuzzy similarity for club identity.
ALIASES = {
    'bayern munchen': 'bayern munchen', 'fc bayern munchen': 'bayern munchen',
    '1 fc koln': 'koln', 'fc koln': 'koln',
    'bvb': 'borussia dortmund',
    'inter': 'internazionale milano', 'inter milan': 'internazionale milano',
    'fc internazionale milano': 'internazionale milano', 'internazionale': 'internazionale milano',
    'ac milan': 'milan',
    'paris saint germain': 'paris saint germain', 'psg': 'paris saint germain',
    'club atletico de madrid': 'atletico madrid', 'atletico de madrid': 'atletico madrid',
    'real betis balompie': 'real betis',
    'tottenham': 'tottenham hotspur',
    'wolves': 'wolverhampton wanderers',
    'brighton': 'brighton hove albion',
    'bayer leverkusen': 'bayer 04 leverkusen',
    'rb leipzig': 'rasenballsport leipzig',
    'freiburg': 'sc freiburg',
    'werder bremen': 'sv werder bremen',
    'stuttgart': 'vfb stuttgart',
    'athletic bilbao': 'athletic club',
    'real sociedad': 'real sociedad de futbol',
    'celta vigo': 'rc celta de vigo',
    'girona': 'girona',
    'rayo vallecano': 'rayo vallecano de madrid',
    'lyon': 'olympique lyonnais',
    'marseille': 'olympique de marseille',
    'rennes': 'stade rennais 1901',
    'stade rennais': 'stade rennais 1901',
    'lens': 'racing club de lens',
    'monaco': 'as monaco',
    'lille': 'lille osc',
    'strasbourg': 'rc strasbourg alsace',
    'brest': 'stade brestois 29',
    'nice': 'ogc nice',
    # V3.5: verified API-Football labels against football-data.org 2025/26 club names.
    'le havre': 'le havre ac',
    'espanyol': 'rcd espanyol de barcelona',
    'alaves': 'deportivo alaves',
    'como': 'como 1907',
    'cagliari': 'cagliari calcio',
    'lazio': 'ss lazio',
    'lecce': 'us lecce',
    '1899 hoffenheim': 'tsg 1899 hoffenheim',
    'union berlin': '1 fc union berlin',
    'bournemouth': 'afc bournemouth',
    'nottingham forest': 'nottingham forest',
    'leeds': 'leeds united',
    'parma': 'parma calcio 1913',
    'newcastle': 'newcastle united',
    'napoli': 'ssc napoli',
    'torino': 'torino',
    'auxerre': 'aj auxerre',
}

def norm(value):
    s = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    s = re.sub(r'\b(fc|afc|cf)\b$', '', s).strip()
    return ALIASES.get(s, s)

def parse_dt(value):
    d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('Missing timezone')
    return d.astimezone(timezone.utc)

def poisson(lam, max_goal=12):
    p = [math.exp(-lam)]
    for n in range(1, max_goal + 1):
        p.append(p[-1] * lam / n)
    p[-1] += max(0.0, 1.0 - sum(p))
    return p

def forecast(rows, home, away):
    hg = sum(r['home_goals'] for r in rows) / len(rows)
    ag = sum(r['away_goals'] for r in rows) / len(rows)
    hh = [r for r in rows if r['_home'] == home]
    aa = [r for r in rows if r['_away'] == away]
    if len(hh) < 5 or len(aa) < 5:
        return None
    prior = 8
    hf = (sum(r['home_goals'] for r in hh) + prior * hg) / (len(hh) + prior)
    hd = (sum(r['away_goals'] for r in hh) + prior * ag) / (len(hh) + prior)
    af = (sum(r['away_goals'] for r in aa) + prior * ag) / (len(aa) + prior)
    ad = (sum(r['home_goals'] for r in aa) + prior * hg) / (len(aa) + prior)
    lh = max(.15, min(4., hf * ad / max(hg, .1)))
    la = max(.15, min(4., af * hd / max(ag, .1)))
    ph, pa = poisson(lh), poisson(la)
    home_p = sum(a * b for i, a in enumerate(ph) for j, b in enumerate(pa) if i > j)
    draw_p = sum(a * b for i, a in enumerate(ph) for j, b in enumerate(pa) if i == j)
    away_p = 1.0 - home_p - draw_p
    return ({'home': round(home_p, 4), 'draw': round(draw_p, 4), 'away': round(away_p, 4)},
            {'home': round(lh, 3), 'away': round(la, 3)},
            {'home': len(hh), 'away': len(aa)})

def explain_forecast(probs, goals, samples, home_name, away_name):
    """Evidence-backed editorial opinion, never a guarantee or fabricated team news."""
    choices = [('home', home_name), ('draw', 'Match nul'), ('away', away_name)]
    winner, label = max(choices, key=lambda pair: probs[pair[0]])
    gap = sorted(probs.values(), reverse=True)[0] - sorted(probs.values(), reverse=True)[1]
    confidence = 'moderee' if gap >= .12 else 'prudente'
    evidence = [
        {'type': 'expected_goals', 'home': goals['home'], 'away': goals['away'],
         'text_fr': f"Buts attendus selon le modele : {goals['home']:.2f} pour {home_name}, {goals['away']:.2f} pour {away_name}.",
         'text_en': f"Model expected goals: {home_name} {goals['home']:.2f}, {away_name} {goals['away']:.2f}."},
        {'type': 'historical_samples', 'home': samples['home'], 'away': samples['away'],
         'text_fr': f"Base statistique : {samples['home']} matchs a domicile de {home_name} et {samples['away']} matchs a l'exterieur de {away_name}.",
         'text_en': f"Statistical sample: {samples['home']} home games for {home_name} and {samples['away']} away games for {away_name}."},
    ]
    return {
        'pick': winner, 'pick_label': label, 'confidence': confidence,
        'reasons': evidence,
        'opinion_fr': f"Notre avis : {label}. Cette orientation repose sur les buts attendus et les performances historiques domicile/exterieur. L'ecart entre les scenarios reste {'limite' if gap < .12 else 'notable'}, et une surprise demeure possible.",
        'opinion_en': f"Our view: {('draw' if winner == 'draw' else label + ' to win')}. This opinion uses expected goals and historical home/away performance. The gap between outcomes is {'narrow' if gap < .12 else 'meaningful'}, and an upset remains possible.",
        'limitations_fr': "Avis statistique, sans prise en compte confirmee des blessures, compositions ou informations de derniere minute. Aucun resultat garanti.",
        'limitations_en': "Statistical opinion; injuries, lineups and late news have not been verified. No outcome is guaranteed.",
    }

def main():
    history = json.loads((DATA / 'historical_matches.json').read_text(encoding='utf-8'))['matches']
    fixtures = json.loads((DATA / 'prediction_fixtures.json').read_text(encoding='utf-8'))['matches']
    now = datetime.now(timezone.utc)
    grouped = defaultdict(list)
    bad_history = 0
    for item in history:
        try:
            r = dict(item)
            if r.get('competition') not in {v[0] for v in LEAGUES.values()}:
                continue
            if type(r.get('home_goals')) is not int or type(r.get('away_goals')) is not int:
                continue
            if min(r['home_goals'], r['away_goals']) < 0:
                continue
            r['_date'] = parse_dt(r['utc_date'])
            if r['_date'] >= now:
                continue
            r['_home'], r['_away'] = norm(r['home_name']), norm(r['away_name'])
            grouped[r['competition']].append(r)
        except (ValueError, TypeError, KeyError):
            bad_history += 1
    for rows in grouped.values():
        rows.sort(key=lambda r: r['_date'])
    predictions, skipped = [], Counter()
    exclusions = []
    for m in fixtures:
        reason = None
        league = m.get('league') or {}
        lid = league.get('id')
        try:
            lid = int(lid)
        except (TypeError, ValueError):
            pass
        if lid not in LEAGUES:
            reason = 'unsupported_competition'
        elif str(league.get('country') or '').casefold() != LEAGUES[lid][1].casefold():
            reason = 'country_mismatch'
        elif m.get('status') not in ('NS', 'TBD'):
            reason = 'not_scheduled'
        else:
            try:
                kickoff = parse_dt(m['kickoff'])
            except (ValueError, TypeError, KeyError):
                reason = 'invalid_date'
            if reason is None and not (now < kickoff <= now + timedelta(days=7)):
                reason = 'outside_next_7_days'
        if reason is None:
            rows = [r for r in grouped[LEAGUES[lid][0]] if r['_date'] < kickoff]
            if len(rows) < 100:
                reason = 'insufficient_league_history'
            else:
                home = norm((m.get('home') or {}).get('name'))
                away = norm((m.get('away') or {}).get('name'))
                known = {r['_home'] for r in rows} | {r['_away'] for r in rows}
                if not home or not away or home == away or home not in known or away not in known:
                    reason = 'unmatched_team'
                else:
                    calculated = forecast(rows, home, away)
                    if calculated is None:
                        reason = 'insufficient_team_history'
                    else:
                        probs, goals, samples = calculated
                        predictions.append({
                            'match_id': m.get('id'), 'kickoff': m['kickoff'],
                            'competition': LEAGUES[lid][0], 'league': league.get('name'),
                            'home': (m.get('home') or {}).get('name'),
                            'away': (m.get('away') or {}).get('name'),
                            'probabilities_1x2': probs, 'expected_goals': goals,
                            'historical_samples': samples,
                            'analysis': explain_forecast(probs, goals, samples, (m.get('home') or {}).get('name'), (m.get('away') or {}).get('name')),
                            'model': 'poisson_v33_prototype',
                            'experimental': True,
                        })
        if reason:
            skipped[reason] += 1
            exclusions.append({'match_id': m.get('id'), 'reason': reason,
                               'league_id': lid, 'home': (m.get('home') or {}).get('name'),
                               'away': (m.get('away') or {}).get('name')})
    predictions.sort(key=lambda p: p['kickoff'])
    output = {
        'source': 'ZEROFOOT', 'created_at': now.isoformat(), 'model': 'poisson_v33_prototype',
        'warning': 'Experimental forecasts based on available historical data, not validated for future betting or guaranteed returns.',
        'input_matches': len(fixtures), 'historical_matches': sum(map(len, grouped.values())),
        'predictions_count': len(predictions), 'skipped': dict(skipped), 'predictions': predictions,
    }
    audit = {
        'created_at': now.isoformat(), 'historical_by_competition': {k: len(v) for k, v in grouped.items()},
        'invalid_historical_rows': bad_history, 'fixture_count': len(fixtures),
        'predictions_count': len(predictions), 'excluded_count': len(exclusions),
        'exclusion_reasons': dict(skipped), 'exclusions': exclusions,
    }
    assert len(predictions) + len(exclusions) == len(fixtures)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / 'live_predictions.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (DATA / 'prediction_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'V3.3: {len(predictions)} predictions / {len(fixtures)} fixtures; excluded: {dict(skipped)}')

if __name__ == '__main__':
    main()
