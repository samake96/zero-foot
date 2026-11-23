"""Build the FootChrono European results archive from an OpenFootball checkout."""
import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

COMPETITIONS = {'cl': 'Ligue des champions', 'el': 'Ligue Europa', 'conf': 'Ligue Conférence'}
DATE = re.compile(r'^\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([A-Z][a-z]{2}) (\d{1,2})(?: (\d{4}))?\s*$')
GAME = re.compile(r'^\s*(?:\d{1,2}:\d{2}\s+)?(.+?) \([A-Z]{3}\)\s+v\s+(.+?) \([A-Z]{3}\)\s+(\d+)-(\d+)(.*)$')
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()


def read_season(path):
    start = int(path.parent.name.split('-')[0])
    date = None
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if header := DATE.match(line):
            month = MONTHS.index(header[1]) + 1
            year = int(header[3]) if header[3] else start + (month < 7)
            date = dt.date(year, month, int(header[2])).isoformat()
        elif date and (game := GAME.match(line)):
            home, away, first, second, extra = game.groups()
            if re.match(r'^\s*pen\.', extra):
                # Keep the match score after extra time and exclude the shootout tally.
                score = re.search(r'(\d+)-(\d+)\s+a\.e\.t\.', extra)
                if not score:
                    continue
                first, second = score.groups()
            yield date, home, away, int(first), int(second)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    args = parser.parse_args()
    root = args.checkout
    pools = {key: sorted(root.glob(f'20??-??/{key}.txt')) for key in COMPETITIONS}
    if any(not paths for paths in pools.values()):
        parser.error('The checkout must contain the three European club competitions.')
    teams = {}
    matches = set()
    for code, paths in pools.items():
        for path in paths:
            for date, home, away, first, second in read_season(path):
                home_id = teams.setdefault(home, len(teams))
                away_id = teams.setdefault(away, len(teams))
                matches.add((date, home_id, away_id, first, second, code))
    revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    payload = {'revision': revision, 'teams': list(teams), 'competitions': COMPETITIONS,
               'matches': sorted(matches, reverse=True)}
    output = Path(__file__).resolve().parents[1] / 'data/openfootball-europe.json'
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'{len(matches)} résultats, {len(teams)} noms de clubs')


if __name__ == '__main__':
    main()
