"""Import completed fixtures from the public-domain OpenFootball archive."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

COMPETITIONS = {39: 'en.1', 140: 'es.1', 78: 'de.1', 135: 'it.1', 61: 'fr.1'}
SEASONS = ('2024-25', '2025-26')


def score_pair(value):
    return isinstance(value, list) and len(value) == 2 and all(type(n) is int and n >= 0 for n in value)


def fetch(league, season, revision):
    url = f'https://raw.githubusercontent.com/openfootball/football.json/{revision}/{season}/{COMPETITIONS[league]}.json'
    with urlopen(url, timeout=20) as response:
        payload = json.load(response)
    matches = []
    for row in payload['matches']:
        score = row.get('score')
        full_time = score.get('ft') if isinstance(score, dict) else score
        if not score_pair(full_time):
            continue
        half_time = score.get('ht') if isinstance(score, dict) else None
        matches.append([row['date'], row['team1'], row['team2'], full_time, half_time if score_pair(half_time) else None])
    if not matches:
        raise ValueError(f'No results for {league} in {season}')
    return league, matches


if __name__ == '__main__':
    revision = sys.argv[1]
    grouped = {key: [] for key in COMPETITIONS}
    with ThreadPoolExecutor(max_workers=10) as pool:
        jobs = [pool.submit(fetch, key, season, revision) for key in COMPETITIONS for season in SEASONS]
        for job in jobs:
            league, rows = job.result()
            grouped[league].extend(rows)
    for league, rows in grouped.items():
        output = Path(__file__).resolve().parents[1] / 'data' / f'openfootball-{league}.json'
        output.write_text(json.dumps({'revision': revision, 'matches': sorted(rows, reverse=True)},
                                     ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
        print(league, len(rows))
