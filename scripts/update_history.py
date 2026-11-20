#!/usr/bin/env python3
"""ZEROFOOT: import completed historical matches from football-data.org v4."""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

COMPETITIONS = {"PL": "Premier League", "PD": "La Liga", "BL1": "Bundesliga", "SA": "Serie A", "FL1": "Ligue 1"}
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "historical_matches.json"
TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
SEASON = int(os.environ.get("HISTORY_SEASON", "2025"))


def fetch(code, season):
    url = "https://api.football-data.org/v4/competitions/" + code + "/matches?" + urllib.parse.urlencode({"season": season, "status": "FINISHED"})
    request = urllib.request.Request(url, headers={"X-Auth-Token": TOKEN, "Accept": "application/json", "User-Agent": "ZEROFOOT-history/1.0"})
    with urllib.request.urlopen(request, timeout=35) as response:
        return json.load(response)


def normalize(match, code, season):
    score = match.get("score") or {}
    full = score.get("fullTime") or {}
    home, away = match.get("homeTeam") or {}, match.get("awayTeam") or {}
    h, a = full.get("home"), full.get("away")
    if match.get("status") != "FINISHED" or not all(isinstance(v, int) and not isinstance(v, bool) for v in (h, a)):
        return None
    if not isinstance(home.get("id"), int) or not isinstance(away.get("id"), int):
        return None
    return {"id": match.get("id"), "competition": code, "season": season, "utc_date": match.get("utcDate"), "matchday": match.get("matchday"), "home_id": home["id"], "home_name": home.get("name"), "away_id": away["id"], "away_name": away.get("name"), "home_goals": h, "away_goals": a, "winner": "HOME" if h > a else "AWAY" if a > h else "DRAW"}


def main():
    if not TOKEN:
        sys.exit("Missing secret FOOTBALL_DATA_TOKEN")
    if not 2000 <= SEASON <= datetime.now(timezone.utc).year:
        sys.exit("Invalid HISTORY_SEASON")
    previous = {}
    if OUTPUT.exists():
        try:
            raw = json.loads(OUTPUT.read_text(encoding="utf-8"))
            previous = {str(m["id"]): m for m in raw.get("matches", []) if m.get("id") is not None}
        except (OSError, ValueError, KeyError, TypeError):
            sys.exit("Existing historical file is invalid; refusing to overwrite")
    merged = dict(previous)
    successful = 0
    failures = []
    for i, (code, label) in enumerate(COMPETITIONS.items()):
        if i:
            time.sleep(7)  # Stay comfortably under 10 requests/minute.
        try:
            payload = fetch(code, SEASON)
            matches = payload.get("matches")
            if not isinstance(matches, list):
                raise ValueError("Unexpected response: missing matches array")
            valid = [m for raw in matches if (m := normalize(raw, code, SEASON)) and m.get("id") is not None]
            if not valid:
                raise ValueError("No completed matches returned")
            for m in valid:
                merged[str(m["id"])] = m
            successful += 1
            print(f"{label}: {len(valid)} completed matches imported")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
            status = getattr(exc, "code", None)
            msg = f"{label}: unavailable" + (f" (HTTP {status})" if status else f" ({type(exc).__name__})")
            failures.append(msg)
            print(msg)
    if not successful:
        sys.exit("No competition imported; historical file left unchanged. Check account access and workflow logs.")
    matches = sorted(merged.values(), key=lambda m: (m.get("utc_date") or "", str(m["id"])))
    document = {"source": "football-data.org", "updated_at": datetime.now(timezone.utc).isoformat(), "last_requested_season": SEASON, "matches": matches}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(matches)} unique completed matches; {successful}/5 competitions updated")
    if failures:
        print("Partial collection: " + "; ".join(failures))


if __name__ == "__main__":
    main()
