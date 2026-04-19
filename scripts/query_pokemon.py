#!/usr/bin/env python3
"""
Query Champions Pokemon by stats + movepool.

Joins cache/pokemon.jsonl (base stats from PokeAPI) with
cache/champions_movepools.jsonl (Champions-legal movepools from Serebii)
to answer questions like:

    # Mons under 50 base speed that learn Tailwind
    python3 scripts/query_pokemon.py --move tailwind --max-speed 50

    # All mons that learn Ice Punch
    python3 scripts/query_pokemon.py --move ice-punch

    # Fastest mon with Rage Powder
    python3 scripts/query_pokemon.py --move rage-powder --sort-by speed --desc --limit 1

    # Trick Room sweepers: high attack, low speed, learns a strong move
    python3 scripts/query_pokemon.py --max-speed 50 --min-attack 110 --sort-by attack --desc

    # Multi-move filter (must learn ALL listed moves)
    python3 scripts/query_pokemon.py --move tailwind --move protect

Move names use PokeAPI hyphen format: "ice-punch", "rage-powder",
"fake-out". Spaces and underscores in input are normalized.

NOTE: pokemon.jsonl uses PokeAPI naming (e.g. charizard-mega-x), while
champions_movepools.jsonl uses Serebii base slugs (e.g. charizard).
Mega forms inherit their base form's movepool — same in mainline, same
in Champions. We match by stripping "-mega*", "-gmax", etc. suffixes.
"""

import argparse
import json
import os
import re
import sys

POKEMON_PATH = "cache/pokemon.jsonl"
MOVEPOOLS_PATH = "cache/champions_movepools.jsonl"

# Suffixes on PokeAPI pokemon names that map to the Serebii base slug.
# Mega/Gmax/regional forms share movepool with the base species in
# Serebii's Champions dex (one consolidated table per species).
FORM_SUFFIX_RE = re.compile(
    r"-(mega(-[xy])?|gmax|alola|galar|hisui|paldea|origin|therian|"
    r"crowned|eternamax|primal|sky|black|white|resolute|pirouette|"
    r"ash|cap|f|m)$"
)


def normalize_move(name: str) -> str:
    return (
        name.strip().lower()
        .replace("_", "-")
        .replace(" ", "-")
        .replace(".", "")
        .replace("'", "")
    )


def load_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        print(f"# missing cache: {path}", file=sys.stderr)
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def base_slug(pokeapi_name: str) -> str:
    """Strip form suffixes to get the Serebii movepool key."""
    return FORM_SUFFIX_RE.sub("", pokeapi_name)


def matches_filters(mon: dict, moves: set[str], args) -> bool:
    stats = mon.get("base_stats", {})
    spd = stats.get("speed", 0)
    atk = stats.get("attack", 0)
    spa = stats.get("special-attack", 0)
    hp = stats.get("hp", 0)

    if args.max_speed is not None and spd > args.max_speed:
        return False
    if args.min_speed is not None and spd < args.min_speed:
        return False
    if args.min_attack is not None and atk < args.min_attack:
        return False
    if args.min_spatk is not None and spa < args.min_spatk:
        return False
    if args.min_hp is not None and hp < args.min_hp:
        return False
    if args.type and not any(t in mon.get("types", []) for t in args.type):
        return False
    if args.move:
        required = {normalize_move(m) for m in args.move}
        if not required.issubset(moves):
            return False
    return True


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--move", action="append", default=[],
                    help="Filter to mons that learn this move (repeatable; ALL must match)")
    ap.add_argument("--type", action="append", default=[],
                    help="Filter to mons of this type (repeatable; ANY match)")
    ap.add_argument("--max-speed", type=int)
    ap.add_argument("--min-speed", type=int)
    ap.add_argument("--min-attack", type=int)
    ap.add_argument("--min-spatk", type=int)
    ap.add_argument("--min-hp", type=int)
    ap.add_argument("--sort-by", choices=["speed", "attack", "special-attack",
                                          "defense", "special-defense", "hp", "name"],
                    default="speed")
    ap.add_argument("--desc", action="store_true", help="Sort descending")
    ap.add_argument("--limit", type=int, default=0, help="Show first N (0 = all)")
    ap.add_argument("--show-moves", action="store_true",
                    help="Print full movepool for each result")
    args = ap.parse_args()

    pokemon = load_jsonl(POKEMON_PATH)
    movepools = {r["name"]: set(r["moves"]) for r in load_jsonl(MOVEPOOLS_PATH)}
    if not pokemon or not movepools:
        sys.exit(1)

    results = []
    for mon in pokemon:
        slug = base_slug(mon["name"])
        moves = movepools.get(slug)
        if moves is None:
            # No Champions movepool → not a Champions-legal species. Skip
            # unless the user is filtering on stats/types only AND didn't
            # ask for a move (in which case all 1300 PokeAPI mons would
            # show, which isn't useful for a Champions tool).
            continue
        if matches_filters(mon, moves, args):
            results.append((mon, moves))

    sort_key = args.sort_by
    if sort_key == "name":
        results.sort(key=lambda r: r[0]["name"], reverse=args.desc)
    else:
        results.sort(
            key=lambda r: r[0]["base_stats"].get(sort_key, 0),
            reverse=args.desc,
        )

    if args.limit:
        results = results[: args.limit]

    if not results:
        print("# no matches", file=sys.stderr)
        return

    for mon, moves in results:
        s = mon["base_stats"]
        types = "/".join(mon["types"])
        line = (
            f"{mon['name']:30s} {types:18s} "
            f"HP {s.get('hp',0):3d}  Atk {s.get('attack',0):3d}  "
            f"Def {s.get('defense',0):3d}  SpA {s.get('special-attack',0):3d}  "
            f"SpD {s.get('special-defense',0):3d}  Spe {s.get('speed',0):3d}"
        )
        print(line)
        if args.show_moves:
            print(f"  moves: {', '.join(sorted(moves))}")

    print(f"\n# {len(results)} match(es)", file=sys.stderr)


if __name__ == "__main__":
    main()
