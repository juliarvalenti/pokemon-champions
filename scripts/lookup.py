#!/usr/bin/env python3
"""
Look up a move, ability, or item from the local caches.

Auto-detects category: searches all cache files for an entry matching the
normalized name. Returns all matches as JSON (since e.g. "Rage" was
historically both a move and an ability in different games, and many
abilities/items appear in BOTH the mainline PokeAPI cache and the
Champions-specific Serebii cache with different effects).

Category semantics:
    moves, abilities, items                 — mainline Scarlet/Violet data
                                              from PokeAPI (cache/*.jsonl)
    champions_items, champions_abilities    — Champions-authoritative data
                                              from Serebii (cache/champions_*.jsonl)

When a name appears in both a mainline file and a Champions file, results
from both are returned — the Champions entry is authoritative for "does
it exist / does it work differently in Champions?" while the mainline
entry gives mechanics detail (damage class, priority, accuracy, etc).

Normalization: input is lowercased, spaces and underscores become
hyphens, periods are stripped. So "Fake Out", "fake out", and "fake-out"
all match the same entry.

Usage:
    python3 scripts/lookup.py telepathy
    python3 scripts/lookup.py "fake out"
    python3 scripts/lookup.py choice-scarf
    python3 scripts/lookup.py "spicy spray"               # Champions-original
    python3 scripts/lookup.py --category champions_items  # Champions shop check
    python3 scripts/lookup.py --fuzzy protect             # partial matches
"""

import argparse
import json
import os
import sys

CACHE_DIR = "cache"
CATEGORIES = [
    "moves",
    "abilities",
    "items",
    "champions_items",
    "champions_abilities",
]


def normalize(name: str) -> str:
    """Convert user input to PokeAPI kebab-case form."""
    return (
        name.strip()
        .lower()
        .replace("_", "-")
        .replace(" ", "-")
        .replace(".", "")
        .replace("'", "")
    )


def load_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def find_exact(name: str, category: str) -> list[dict]:
    path = os.path.join(CACHE_DIR, f"{category}.jsonl")
    entries = load_jsonl(path)
    return [
        {"category": category, **e}
        for e in entries
        if e.get("name") == name
    ]


def find_fuzzy(name: str, category: str) -> list[dict]:
    """Partial-match search: returns entries whose name contains the query."""
    path = os.path.join(CACHE_DIR, f"{category}.jsonl")
    entries = load_jsonl(path)
    return [
        {"category": category, **e}
        for e in entries
        if name in e.get("name", "")
    ]


def main():
    ap = argparse.ArgumentParser(description="Lookup a cached move/ability/item")
    ap.add_argument("name", help="Entry name (case/space insensitive)")
    ap.add_argument(
        "--category",
        choices=CATEGORIES,
        default=None,
        help="Limit search to a specific category (default: all)",
    )
    ap.add_argument(
        "--fuzzy",
        action="store_true",
        help="Partial-match search instead of exact",
    )
    args = ap.parse_args()

    query = normalize(args.name)
    cats = [args.category] if args.category else CATEGORIES
    finder = find_fuzzy if args.fuzzy else find_exact

    results = []
    for c in cats:
        results.extend(finder(query, c))

    if not results:
        print(
            json.dumps(
                {
                    "query": query,
                    "matches": 0,
                    "note": (
                        "No entries found. Cache may not be populated yet — "
                        "check `cache/*.jsonl` files or run `scripts/build_cache.py`. "
                        "Try --fuzzy for partial matches."
                    ),
                },
                indent=2,
            )
        )
        sys.exit(1)

    print(
        json.dumps(
            {
                "query": query,
                "matches": len(results),
                "results": results,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
