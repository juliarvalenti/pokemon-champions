#!/usr/bin/env python3
"""
Quick Pokemon type lookup from local cache. No API calls.

Fuzzy-matches names so typos still resolve — "mimiyu" finds "mimikyu",
"typhlosion hisui" finds "typhlosion-hisui", etc.

Usage:
    python3 scripts/pokemon.py charizard
    python3 scripts/pokemon.py toxapex skarmory dragapult
    python3 scripts/pokemon.py "mimiyu" "typhlosion hisui"
"""

import difflib
import sys

from cache_utils import load_pokemon_cache, normalize_key, get_type_matchups


def resolve(query: str, cache: dict) -> tuple[str, dict] | None:
    """Return (matched_name, entry) for query, or None if no match.

    Tries exact normalized match first, then falls back to difflib
    closest-match across all cache keys.
    """
    key = normalize_key(query)

    # Exact match
    if key in cache:
        return key, cache[key]

    # Fuzzy match
    matches = difflib.get_close_matches(key, cache.keys(), n=1, cutoff=0.75)
    if matches:
        matched = matches[0]
        return matched, cache[matched]

    return None


def display(query: str, matched_key: str, entry: dict) -> str:
    lines = []

    types = entry.get("types", [])
    type_str = "/".join(t.title() for t in types) if types else "???"

    # Display the query name (what the user typed / Pikalytics name), not the
    # internal PokeAPI form name (e.g. show "Morpeko" not "Morpeko-Hangry").
    display_name = query.title()
    header = f"{display_name} [{type_str}]"
    if normalize_key(query) != matched_key:
        header += f"  # '{query}' → '{matched_key}'"
    lines.append(header)

    if types:
        weaknesses, resistances, immunities = get_type_matchups(types)

        buckets: dict[str, list[str]] = {"4x": [], "2x": [], "0.5x": [], "0.25x": [], "immune": []}
        for t, m in weaknesses.items():
            bucket = "4x" if m >= 4 else "2x"
            buckets[bucket].append(t.title())
        for t, m in resistances.items():
            bucket = "0.25x" if m <= 0.25 else "0.5x"
            buckets[bucket].append(t.title())
        for t in immunities:
            buckets["immune"].append(t.title())

        for label, types_in_bucket in buckets.items():
            if types_in_bucket:
                lines.append(f"  {label:<7} {', '.join(sorted(types_in_bucket))}")

    stats = entry.get("base_stats", {})
    if stats:
        stat_order = [
            ("hp", "HP"), ("attack", "Atk"), ("defense", "Def"),
            ("special-attack", "SpA"), ("special-defense", "SpD"), ("speed", "Spe"),
        ]
        parts = [f"{label} {stats[k]}" for k, label in stat_order if k in stats]
        if parts:
            lines.append(f"  stats   {' / '.join(parts)}")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/pokemon.py <Name> [Name2 ...]")
        sys.exit(1)

    cache = load_pokemon_cache()
    if not cache:
        print("pokemon cache is empty — run: python3 scripts/build_cache.py pokemon")
        sys.exit(1)

    queries = sys.argv[1:]
    exit_code = 0

    for query in queries:
        result = resolve(query, cache)
        if result:
            matched_key, entry = result
            print(display(query, matched_key, entry))
        else:
            print(f"No match for '{query}' (cache has {len(cache)} entries)")
            exit_code = 1
        print()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
