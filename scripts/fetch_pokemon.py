#!/usr/bin/env python3
"""Fetch detailed Pokemon usage data from Pikalytics AI endpoints."""

import json
import re
import sys
import urllib.request

from cache_utils import load_all_caches, load_pokemon_cache, normalize_key, get_type_matchups, format_type_matchups  # noqa: F401

BASE_URL = "https://pikalytics.com/ai/pokedex/championspreview"


def parse_section(text, header):
    """Extract bullet list items under a ## header."""
    pattern = rf"## {re.escape(header)}\s*\n((?:- .+\n?)+)"
    m = re.search(pattern, text)
    if not m:
        return []
    items = []
    for line in m.group(1).strip().splitlines():
        # Format: - **Name**: 12.34%
        im = re.match(r"- \*\*(.+?)\*\*:\s*([\d.]+)%", line)
        if im:
            items.append({"name": im.group(1), "usage": float(im.group(2))})
    return items


def parse_stats(text):
    """Extract base stats table."""
    stats = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*(HP|Attack|Defense|Sp\. Atk|Sp\. Def|Speed|BST)\s*\|\s*(\d+)\s*\|", line)
        if m:
            key = m.group(1).lower().replace(". ", "_").replace(" ", "_")
            stats[key] = int(m.group(2))
    return stats


def parse_teams(text):
    """Extract featured teams."""
    teams = []
    # Split by ### Team N
    team_blocks = re.split(r"### Team \d+", text)
    for block in team_blocks[1:]:  # skip text before first team
        pokemon_m = re.search(r"\*\*Pokemon\*\*:\s*(.+)", block)
        ability_m = re.search(r"\*\*Ability\*\*:\s*(.+)", block)
        item_m = re.search(r"\*\*Item\*\*:\s*(.+)", block)
        if pokemon_m:
            team = {
                "pokemon": [p.strip() for p in pokemon_m.group(1).split(",")],
                "ability": ability_m.group(1).strip() if ability_m else None,
                "item": item_m.group(1).strip() if item_m else None,
            }
            teams.append(team)
    return teams


def enrich_with_types(data: dict, pokemon_cache: dict) -> dict:
    """Add types, weaknesses, resistances, immunities fields from pokemon cache."""
    entry = pokemon_cache.get(normalize_key(data["name"]))
    if not entry:
        return data
    types = entry.get("types", [])
    if not types:
        return data
    weaknesses, resistances, immunities = get_type_matchups(types)
    data["types"] = types
    data["weaknesses"] = {t: m for t, m in sorted(weaknesses.items(), key=lambda x: -x[1])}
    data["resistances"] = {t: m for t, m in sorted(resistances.items(), key=lambda x: x[1])}
    data["immunities"] = sorted(immunities)
    return data


def fetch_pokemon(name: str, pokemon_cache: dict | None = None) -> dict:
    url = f"{BASE_URL}/{name}"
    req = urllib.request.Request(url, headers={"User-Agent": "pokemon-champions-agent/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8")

    data = {
        "name": name,
        "moves": parse_section(text, "Common Moves"),
        "abilities": parse_section(text, "Common Abilities"),
        "items": parse_section(text, "Common Items"),
        "teammates": parse_section(text, "Common Teammates"),
        "base_stats": parse_stats(text),
        "teams": parse_teams(text),
    }
    if pokemon_cache is not None:
        data = enrich_with_types(data, pokemon_cache)
    return data


def fetch_multiple(names: list[str], pokemon_cache: dict | None = None) -> list[dict]:
    results = []
    for name in names:
        try:
            results.append(fetch_pokemon(name, pokemon_cache))
        except Exception as e:
            results.append({"name": name, "error": str(e)})
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: fetch_pokemon.py <Name> [Name2 ...]", file=sys.stderr)
        sys.exit(1)

    pkmn_cache = load_pokemon_cache()
    names = sys.argv[1:]
    try:
        if len(names) == 1:
            data = fetch_pokemon(names[0], pkmn_cache)
        else:
            data = fetch_multiple(names, pkmn_cache)
        json.dump(data, sys.stdout, indent=2)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
