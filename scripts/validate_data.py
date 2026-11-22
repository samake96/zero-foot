"""Validate FootChrono static data before publication. Standard library only."""
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
        if filename == "matches.json":
            matches = payload.get("matches") if isinstance(payload, dict) else None
            if not isinstance(matches, list):
                errors.append("matches.json: matches must be a list")
            else:
                ids = [str(x.get("id")) for x in matches if isinstance(x, dict) and x.get("id") is not None]
                if len(ids) != len(set(ids)):
                    errors.append("matches.json: duplicate fixture IDs")
        if filename == "match_results_archive.json":
            matches = payload.get("matches") if isinstance(payload, dict) else None
            if not isinstance(matches, list):
                errors.append("match_results_archive.json: matches must be a list")
            else:
                ids = []
                for m in matches:
                    if not isinstance(m, dict):
                        errors.append("archive: non-object match")
                        continue
                    if m.get("status") not in {"FT", "AET", "PEN"}:
                        errors.append(f"archive: non-final status for {m.get('id')}")
                    for side in ("home", "away"):
                        score = (m.get(side) or {}).get("goals")
                        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
                            errors.append(f"archive: invalid {side} score for {m.get('id')}")
                    if m.get("id") is not None:
                        ids.append(str(m["id"]))
                if len(ids) != len(set(ids)):
                    errors.append("archive: duplicate fixture IDs")
                if payload.get("total") != len(matches):
                    errors.append("archive: total does not match matches length")
    except (OSError, ValueError, UnicodeError) as exc:
        errors.append(f"{filename}: {type(exc).__name__}: {exc}")
if errors:
    print("DATA VALIDATION FAILED")
    for error in errors[:30]:
        print(" -", error)
    raise SystemExit(1)
print("FootChrono data validation passed")
