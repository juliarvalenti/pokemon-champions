#!/usr/bin/env python3
"""
Discover recent Pokemon Champions tournaments on play.limitlesstcg.com.

Limitless files Champions under gameId=VGC alongside legacy mainline VGC formats
(Reg I, Reg G, Reg H, etc.) with no clean format filter. This script scrapes
the completed tournaments list and filters for tournaments whose name marks them
as Champions (contains "champions", "m-a", "m/a", or "reg m"). It excludes
mainline VGC tournaments (Reg I, Reg G, Reg H, Reg F).

Use the returned tournament IDs with `scripts/fetch_limitless_tournament.py`
to pull full team data for the top placements.

Usage:
    python3 scripts/fetch_limitless_list.py
    python3 scripts/fetch_limitless_list.py --min-players 50
    python3 scripts/fetch_limitless_list.py --sort players
"""

import argparse
import json
import re
import sys
import urllib.request
from urllib.error import HTTPError, URLError

BASE = "https://play.limitlesstcg.com"
HEADERS = {"User-Agent": "champions-team-builder"}

# Pokemon Champions launched 2026-04-08. Tournaments before that are mainline VGC.
CHAMPIONS_LAUNCH = "2026-04-08"

# Name keywords that mark a tournament as mainline VGC (NOT Champions).
# Excludes if the name signals an old Scarlet/Violet regulation set.
MAINLINE_REGS = re.compile(
    r"\b(reg(ulation)?\s*[fghi]\b|sv\s*reg|scarlet[\s/&]+violet)",
    re.IGNORECASE,
)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_tournaments(html: str) -> list[dict]:
    """Return all tournament rows on the listing page."""
    # Each row begins with <tr data-date="..."
    chunks = re.split(r"(<tr data-date=)", html)
    rows_html = [chunks[i] + chunks[i + 1] for i in range(1, len(chunks) - 1, 2)]

    tournaments = []
    for row in rows_html:
        date_m = re.search(r'data-date="([^"]+)"', row)
        name_m = re.search(r'data-name="([^"]+)"', row)
        org_m = re.search(r'data-organizer="([^"]*)"', row)
        players_m = re.search(r'data-players="(\d+)"', row)
        winner_m = re.search(r'data-winner="([^"]*)"', row)
        id_m = re.search(r"/tournament/([a-f0-9]{16,})", row)

        if not (date_m and name_m and id_m):
            continue

        tournaments.append(
            {
                "id": id_m.group(1),
                "name": name_m.group(1),
                "date": date_m.group(1),
                "organizer": org_m.group(1) if org_m else None,
                "players": int(players_m.group(1)) if players_m else 0,
                "winner": winner_m.group(1) if winner_m else None,
            }
        )
    return tournaments


def is_champions(name: str, date: str) -> bool:
    """True if a tournament is likely Champions format.

    Heuristic: dated after Champions launch (2026-04-08) AND not explicitly
    tagged as a mainline Scarlet/Violet regulation. This catches major
    tournaments like 'Alpensee Anniversary' that don't put 'Champions' in
    the name but are still Champions format because they ran post-launch.
    """
    if date < CHAMPIONS_LAUNCH:
        return False
    if MAINLINE_REGS.search(name):
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="List recent Champions tournaments on Limitless TCG")
    ap.add_argument("--min-players", type=int, default=0,
                    help="Only show tournaments with at least N registered players")
    ap.add_argument("--sort", choices=["date", "players"], default="date",
                    help="Sort order (default: date descending)")
    ap.add_argument("--limit", type=int, default=20,
                    help="Max tournaments to return (default 20)")
    ap.add_argument("--include-mainline", action="store_true",
                    help="Don't filter out mainline VGC tournaments (Reg I/G/H/F)")
    args = ap.parse_args()

    url = f"{BASE}/tournaments/completed?game=VGC"
    try:
        html = fetch(url)
    except (HTTPError, URLError) as e:
        print(json.dumps({"error": f"failed to fetch listing: {e}"}))
        sys.exit(1)

    all_tournaments = parse_tournaments(html)

    if args.include_mainline:
        filtered = all_tournaments
    else:
        filtered = [t for t in all_tournaments if is_champions(t["name"], t["date"])]

    if args.min_players:
        filtered = [t for t in filtered if t["players"] >= args.min_players]

    if args.sort == "players":
        filtered.sort(key=lambda t: -t["players"])
    else:
        filtered.sort(key=lambda t: t["date"], reverse=True)

    filtered = filtered[: args.limit]

    print(json.dumps(
        {
            "source": url,
            "total_seen": len(all_tournaments),
            "matched": len(filtered),
            "tournaments": filtered,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
