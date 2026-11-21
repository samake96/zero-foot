"""Freeze the first published pre-match forecast and attach subsequent results."""
import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'
LEDGER = DATA / 'forecast_results.json'


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def update_ledger(ledger, predictions, archive, now):
    entries = {str(row['match_id']): row for row in ledger}
    for forecast in predictions['predictions']:
        key = str(forecast['match_id'])
        if key in entries or not timestamp(predictions['created_at']) <= now < timestamp(forecast['kickoff']):
            continue
        chances = forecast['probabilities_1x2']
        if set(chances) != {'home', 'draw', 'away'} or not all(0 <= x <= 1 for x in chances.values()):
            continue
        if abs(sum(chances.values()) - 1) > 0.01:
            continue
        entries[key] = {
            'match_id': forecast['match_id'],
            'kickoff': forecast['kickoff'],
            'recorded_at': now.isoformat(),
            'competition': forecast['competition'],
            'home': forecast['home'],
            'away': forecast['away'],
            'model': forecast.get('model', predictions.get('model')),
            'probabilities_1x2': chances,
        }
    for result in archive:
        entry = entries.get(str(result['id']))
        if not entry or timestamp(result['kickoff']) != timestamp(entry['kickoff']) or timestamp(result['kickoff']) >= now:
            continue
        if result['status'] in {'AET', 'PEN'}:
            entry['result'] = {'status': 'regulation_score_unavailable'}
            continue
        if result['status'] != 'FT':
            continue
        home, away = result['home']['goals'], result['away']['goals']
        if type(home) is not int or type(away) is not int or min(home, away) < 0:
            continue
        entry['result'] = {
            'status': 'final',
            'home_goals': home,
            'away_goals': away,
            'outcome_1x2': 'home' if home > away else 'away' if home < away else 'draw',
        }
    return list(entries.values())


def main():
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    entries = update_ledger(
        read(LEDGER) if LEDGER.exists() else [],
        read(DATA / 'live_predictions.json'),
        read(DATA / 'match_results_archive.json')['matches'],
        datetime.now(timezone.utc),
    )
    temporary = LEDGER.with_suffix('.tmp')
    temporary.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(LEDGER)
    print(f'{len(entries)} forecasts recorded, {sum(e.get("result", {}).get("status") == "final" for e in entries)} settled')


if __name__ == '__main__':
    main()
