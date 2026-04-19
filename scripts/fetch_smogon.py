#!/usr/bin/env python3
"""
Fetch Smogon sample sets for one or more Pokemon across multiple formats.

Pulls from data.pkmn.cc, which mirrors Smogon's sample set database. Covers:
  - gen9vgc2024 (most relevant — closest format to Champions)
  - gen9doublesou (broader doubles meta)
  - gen9 (singles fallback — UU/OU/Ubers/etc, useful for less-popular mons)

Usage:
    python3 scripts/fetch_smogon.py Skarmory
    python3 scripts/fetch_smogon.py Charizard Venusaur Whimsicott
"""

import json
import sys
import urllib.request
from urllib.error import HTTPError, URLError

SOURCES = [
    ("gen9vgc2024", "VGC 2024 (closest to Champions format)", "doubles"),
    ("gen9doublesou", "Doubles OU", "doubles"),
    ("gen9", "Singles formats (UU/OU/Ubers/etc — fallback)", "singles"),
]

# Doubles sub-formats that may appear under the gen9 umbrella file.
DOUBLES_SUBFORMATS = {
    "doublesou", "doublesuu", "vgc2024", "vgc2025",
    "nationaldexdoubles", "nationaldexdoublesuu",
}

BASE_URL = "https://data.pkmn.cc/sets/{format}.json"


def fetch_format(fmt: str) -> dict:
    url = BASE_URL.format(format=fmt)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "champions-team-builder"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError) as e:
        print(f"# warning: failed to fetch {fmt}: {e}", file=sys.stderr)
        return {}


def fetch_pokemon(name: str, all_data: dict) -> dict:
    """Return all known sets for `name`, grouped by doubles vs singles."""
    result = {
        "name": name,
        "doubles": {},
        "singles": {},
        "warning": None,
    }
    for fmt, label, kind in SOURCES:
        data = all_data.get(fmt, {})
        mon = data.get(name)
        if mon is None:
            continue
        if fmt == "gen9":
            # gen9.json is keyed by sub-format (ou, uu, ubers, doublesou, etc).
            # Sort each entry into doubles/singles based on sub-format name.
            for sub_fmt, sets in mon.items():
                key = f"gen9{sub_fmt}"
                bucket_kind = "doubles" if sub_fmt in DOUBLES_SUBFORMATS else "singles"
                bucket = result[bucket_kind]
                bucket[key] = {
                    "label": f"{'Doubles' if bucket_kind == 'doubles' else 'Singles'} {sub_fmt.upper()}",
                    "sets": sets,
                }
        else:
            result[kind][fmt] = {"label": label, "sets": mon}

    if not result["doubles"] and result["singles"]:
        result["warning"] = (
            "No doubles data available for this Pokemon. Singles sets are shown as a "
            "fallback but DO NOT translate directly to doubles: they lack Fake Out / "
            "Follow Me / Wide Guard / spread moves, often run hazard-heavy game plans, "
            "and use different EV spreads. Use them only to understand the Pokemon's "
            "general role and move pool, not as a direct build template."
        )
    elif not result["doubles"] and not result["singles"]:
        result["warning"] = "No Smogon data available for this Pokemon in any format."

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_smogon.py <Pokemon> [Pokemon ...]", file=sys.stderr)
        sys.exit(1)

    names = sys.argv[1:]
    all_data = {fmt: fetch_format(fmt) for fmt, _, _ in SOURCES}

    results = [fetch_pokemon(n, all_data) for n in names]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
