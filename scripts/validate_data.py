"""Validate FootChrono static data before publication. Standard library only."""
from datetime import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REQUIRED = ["matches.json", "historical_matches.json", "match_results_archive.json",
            "standings.json", "news.json", "live_predictions.json"]
errors = []
for filename in REQUIRED:
    path = DATA / filename
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, (dict, list)):
            errors.append(f"{filename}: unexpected root type")
            continue
        if filename in {"matches.json", "match_results_archive.json"}:
            matches = payload.get("matches") if isinstance(payload, dict) else None
            if not isinstance(matches, list):
                errors.append(f"{filename}: matches must be a list")
                continue
            seen = set()
            archive = filename == "match_results_archive.json"
            for match in matches:
                if not isinstance(match, dict):
                    errors.append(f"{filename}: non-object match")
                    continue
                fixture_id = match.get("id")
                label = f"{filename}: match {fixture_id}"
                if type(fixture_id) is not int or fixture_id < 1 or fixture_id in seen:
                    errors.append(f"{label}: invalid or duplicate fixture ID")
                else:
                    seen.add(fixture_id)
                try:
                    if datetime.fromisoformat(match.get("kickoff", "")).utcoffset() is None:
                        raise ValueError
                except (ValueError, TypeError):
                    errors.append(f"{label}: invalid kickoff or missing timezone")
                league = match.get("league")
                if not isinstance(league, dict) or type(league.get("id")) is not int or league["id"] < 1:
                    errors.append(f"{label}: invalid competition")
                status = match.get("status")
                final = isinstance(status, str) and status in {"FT", "AET", "PEN"}
                if not isinstance(status, str) or not status.strip() or (archive and not final):
                    errors.append(f"{label}: invalid match status")
                logos = []
                for side in ("home", "away"):
                    team = match.get(side)
                    if not isinstance(team, dict) or not isinstance(team.get("name"), str) or not team["name"].strip():
                        errors.append(f"{label}: missing {side} team")
                        continue
                    logo = team.get("logo")
                    if isinstance(logo, str) and logo.startswith("https://media.api-sports.io/football/teams/"):
                        logos.append(logo)
                    score = team.get("goals")
                    if (final or score is not None) and (type(score) is not int or score < 0):
                        errors.append(f"{label}: invalid {side} score")
                if len(logos) == 2 and logos[0] == logos[1]:
                    errors.append(f"{label}: same provider team on both sides")
            if archive and payload.get("total") != len(matches):
                errors.append("archive: total does not match matches length")
    except (OSError, ValueError, UnicodeError) as exc:
        errors.append(f"{filename}: {type(exc).__name__}: {exc}")
if errors:
    print("DATA VALIDATION FAILED")
    for error in errors[:30]:
        print(" -", error)
    raise SystemExit(1)
print("FootChrono data validation passed")
