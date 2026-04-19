#!/usr/bin/env python3
"""
Fetch a Pokemon Champions tournament from play.limitlesstcg.com.

Returns top-N standings with full team lists (Pokemon, item, ability, moves).
Note: Limitless does NOT publish Nature or EVs/Stat Points — only the visible fields.

The Tera Type field appears in source HTML but is vestigial — Champions does not
have Tera. This script strips it.

Usage:
    python3 scripts/fetch_limitless_tournament.py <tournament_id>
    python3 scripts/fetch_limitless_tournament.py <tournament_id> --top 8
    python3 scripts/fetch_limitless_tournament.py 69c8294d36f5b5c303dc036e

Find tournament IDs at https://play.limitlesstcg.com/tournaments?game=VGC
(filter by name containing 'Champions' or 'Reg M-A' since Limitless doesn't
have a Champions-specific filter — Champions tournaments are filed under VGC).
"""

import argparse
import json
import re
import sys
import urllib.request
from urllib.error import HTTPError, URLError

from cache_utils import load_all_caches, short_effect

BASE = "https://play.limitlesstcg.com"
HEADERS = {"User-Agent": "champions-team-builder"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_standings(html: str, top_n: int) -> list[dict]:
    """Return top-N entries as [{place, name, slug}]."""
    rows = re.findall(
        r'<tr data-placing="(\d+)" data-name="([^"]+)"[^>]*>(.*?)</tr>',
        html,
        re.DOTALL,
    )
    standings = []
    for place, name, body in rows:
        place = int(place)
        if place > top_n:
            continue
        m = re.search(r'href="/tournament/[^/]+/player/([^"]+)"', body)
        if not m:
            continue
        standings.append({"place": place, "name": name, "slug": m.group(1)})
    standings.sort(key=lambda s: s["place"])
    return standings


def parse_teamlist(html: str, caches: dict | None = None) -> list[dict]:
    """Parse the 6 Pokemon blocks from a player's teamlist page.

    When `caches` is provided (from cache_utils.load_all_caches), enriches
    each move/ability/item with a short effect description from the local
    PokeAPI cache. Cache misses leave effect fields as None.
    """
    caches = caches or {}
    moves_cache = caches.get("moves", {})
    abilities_cache = caches.get("abilities", {})
    items_cache = caches.get("items", {})

    chunks = re.split(r'<div class="pkmn">', html)[1:]
    team = []
    for chunk in chunks:
        # Cut off at the next pkmn boundary or end of teamlist
        chunk = chunk.split('<div class="pkmn">')[0]

        name_m = re.search(r'<div class="name">.*?<span>([^<]+)</span>', chunk, re.DOTALL)
        item_m = re.search(r'<div class="item">([^<]*)</div>', chunk)
        ability_m = re.search(r'<div class="ability">Ability:\s*([^<]*)</div>', chunk)
        attacks = re.findall(r'<li>([^<]+)</li>', chunk)

        if not name_m:
            continue

        item_name = item_m.group(1).strip() if item_m else None
        ability_name = ability_m.group(1).strip() if ability_m else None
        move_names = [m.strip() for m in attacks[:4]]

        team.append(
            {
                "pokemon": name_m.group(1).strip(),
                "item": {
                    "name": item_name,
                    "effect": short_effect(items_cache, item_name) if item_name else None,
                } if item_name else None,
                "ability": {
                    "name": ability_name,
                    "effect": short_effect(abilities_cache, ability_name) if ability_name else None,
                } if ability_name else None,
                "moves": [
                    {"name": mv, "effect": short_effect(moves_cache, mv)}
                    for mv in move_names
                ],
                # Nature/EVs not published; Tera stripped (vestigial in Champions)
            }
        )
    return team


def fetch_tournament_meta(html: str) -> dict:
    """Extract the tournament name and player count from the standings HTML."""
    name_m = re.search(r"<title>([^<]+)</title>", html)
    name = name_m.group(1).strip() if name_m else None
    # Strip " – Limitless TCG" suffix if present
    if name:
        name = re.sub(r"\s*[–-]\s*Limitless.*$", "", name)
    return {"name": name}


def fetch_tournament(tournament_id: str, top_n: int) -> dict:
    standings_url = f"{BASE}/tournament/{tournament_id}/standings"
    try:
        standings_html = fetch(standings_url)
    except (HTTPError, URLError) as e:
        return {"error": f"failed to fetch standings: {e}", "tournament_id": tournament_id}

    meta = fetch_tournament_meta(standings_html)
    standings = parse_standings(standings_html, top_n)

    # Load the local cache once per invocation — graceful no-op on miss.
    caches = load_all_caches()

    teams = []
    for entry in standings:
        team_url = f"{BASE}/tournament/{tournament_id}/player/{entry['slug']}/teamlist"
        try:
            team_html = fetch(team_url)
            team = parse_teamlist(team_html, caches=caches)
        except (HTTPError, URLError) as e:
            print(f"# warning: failed to fetch {entry['slug']}: {e}", file=sys.stderr)
            team = []
        teams.append(
            {
                "place": entry["place"],
                "player": entry["name"],
                "team": team,
            }
        )

    return {
        "tournament_id": tournament_id,
        "name": meta["name"],
        "standings_url": standings_url,
        "top_n": top_n,
        "results": teams,
    }


def main():
    ap = argparse.ArgumentParser(description="Fetch a Champions tournament from Limitless TCG")
    ap.add_argument("tournament_id", help="Tournament ID (long hex string from the URL)")
    ap.add_argument("--top", type=int, default=8, help="How many top placements to fetch (default 8)")
    args = ap.parse_args()

    result = fetch_tournament(args.tournament_id, args.top)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
