#!/usr/bin/env python3
"""
Build local JSONL cache of moves/abilities/items from PokeAPI.

Writes to cache/moves.jsonl, cache/abilities.jsonl, cache/items.jsonl.
Idempotent — skips entries already in the cache. Rate-limited by default
(1 second between requests) to be a good PokeAPI citizen.

Usage:
    python3 scripts/build_cache.py moves
    python3 scripts/build_cache.py abilities
    python3 scripts/build_cache.py items
    python3 scripts/build_cache.py all

    # Test run: only fetch 10 items
    python3 scripts/build_cache.py moves --limit 10

    # Slower (3s between requests)
    python3 scripts/build_cache.py all --delay 3

Expected times at default 1s delay:
    moves:     ~900 entries  → ~15 min
    abilities: ~300 entries  → ~5 min
    items:    ~2000 entries  → ~33 min
    all:                     → ~53 min

NOTE: PokeAPI data is mainline Scarlet/Violet. Champions has some
differences (new abilities like Mega Sol/Dragonize/Piercing Drill/Spicy
Spray, removed items like Life Orb/Flame Orb/Choice Specs, Power Up Punch
removed as a move, etc.). Treat this cache as "what a move/ability/item
does in mainline" and cross-reference with research/meta-snapshot.md and
CLAUDE.md for Champions-specific differences.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from urllib.error import HTTPError, URLError

# Regex to find any unsubstituted PokeAPI template placeholder like $varname.
# The only known one is $effect_chance, but this sentinel catches any new
# placeholders that appear in future data so they show up in logs instead
# of being silently written to the cache.
TEMPLATE_RE = re.compile(r"\$[a-z_]+")

BASE = "https://pokeapi.co/api/v2"
OUT_DIR = "cache"
HEADERS = {"User-Agent": "champions-team-builder"}


def fetch_json(url: str, retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError) as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"fetch failed after {retries} retries: {e}")
    return {}


def get_en_effect(entries, effect_chance=None) -> dict:
    """Return the English effect text, substituting $effect_chance% placeholder.

    PokeAPI leaves $effect_chance% as a literal placeholder in the effect
    text — e.g. 'Has a $effect_chance% chance to burn the target.' The
    actual chance is on a separate `effect_chance` field of the move. This
    helper substitutes it in. Abilities/items don't use this placeholder
    but passing effect_chance=None is safe (no-op substitution).
    """
    for e in entries or []:
        if e.get("language", {}).get("name") == "en":
            short = e.get("short_effect", "") or ""
            long_text = e.get("effect", "") or ""
            if effect_chance is not None:
                token = "$effect_chance"
                short = short.replace(token, str(effect_chance))
                long_text = long_text.replace(token, str(effect_chance))
            return {"short": short, "long": long_text}
    return {"short": "", "long": ""}


def get_en_flavor(entries) -> str:
    for e in entries or []:
        if e.get("language", {}).get("name") == "en":
            text = e.get("flavor_text") or ""
            return text.replace("\n", " ").replace("\f", " ").strip()
    return ""


def extract_move(d: dict) -> dict:
    record = {
        "name": d["name"],
        "type": d["type"]["name"] if d.get("type") else None,
        "damage_class": d["damage_class"]["name"] if d.get("damage_class") else None,
        "power": d.get("power"),
        "accuracy": d.get("accuracy"),
        "pp": d.get("pp"),
        "priority": d.get("priority"),
        "target": d["target"]["name"] if d.get("target") else None,
        "effect_chance": d.get("effect_chance"),
        "effect": get_en_effect(d.get("effect_entries"), d.get("effect_chance")),
        "flavor": get_en_flavor(d.get("flavor_text_entries")),
    }
    # Safety net: warn on any remaining template placeholder so we catch
    # new PokeAPI variables that slip through.
    eff = record["effect"]
    leftover = TEMPLATE_RE.findall(eff.get("short", "")) + TEMPLATE_RE.findall(eff.get("long", ""))
    if leftover:
        print(
            f"# WARN unsubstituted template(s) in move {d['name']!r}: "
            f"{sorted(set(leftover))}",
            file=sys.stderr,
        )
    return record


def extract_ability(d: dict) -> dict:
    return {
        "name": d["name"],
        "effect": get_en_effect(d.get("effect_entries")),
        "flavor": get_en_flavor(d.get("flavor_text_entries")),
    }


def extract_item(d: dict) -> dict:
    return {
        "name": d["name"],
        "cost": d.get("cost"),
        "category": d["category"]["name"] if d.get("category") else None,
        "attributes": [a["name"] for a in d.get("attributes", [])],
        "effect": get_en_effect(d.get("effect_entries")),
        "flavor": get_en_flavor(d.get("flavor_text_entries")),
    }


def extract_pokemon(d: dict) -> dict:
    return {
        "name": d["name"],
        "types": [t["type"]["name"] for t in d.get("types", [])],
        "base_stats": {
            s["stat"]["name"]: s["base_stat"]
            for s in d.get("stats", [])
        },
    }


CATEGORIES = {
    "moves": {"index": "/move", "extract": extract_move},
    "abilities": {"index": "/ability", "extract": extract_ability},
    # Items uses the 'holdable-active' attribute filter to avoid fetching
    # ~2000 junk items (Pokeballs, fishing rods, TMs, key items, mail, etc.).
    # holdable-active = 141 items that are held and actively used in battle
    # (berries, competitive items, type boosters). Mega stones live under
    # the 'holdable' attribute but aren't "active," so we union both.
    "items": {
        "index": "/item-attribute/holdable-active",
        "extract": extract_item,
        "index_field": "items",
    },
    "mega_stones": {
        "index": "/item-category/mega-stones",
        "extract": extract_item,
        "index_field": "items",
        "writes_to": "items",
    },
    # Pokemon: name + types + base_stats. ~1300 entries, ~22 min at 1s delay.
    # Use --limit to seed just the mons you care about, e.g. --limit 200
    # covers most of the Champions roster in ~3 min.
    "pokemon": {"index": "/pokemon", "extract": extract_pokemon},
}


def load_existing_names(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    names = set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                names.add(json.loads(line)["name"])
            except (json.JSONDecodeError, KeyError):
                continue
    return names


def build(category: str, delay: float, limit: int) -> None:
    cfg = CATEGORIES[category]
    # Some categories (like mega_stones) feed entries into a different
    # output file (items.jsonl) so they co-locate with their siblings.
    out_name = cfg.get("writes_to", category)
    out_path = os.path.join(OUT_DIR, f"{out_name}.jsonl")
    os.makedirs(OUT_DIR, exist_ok=True)

    existing = load_existing_names(out_path)
    print(f"# [{category}] {len(existing)} already cached at {out_path}", file=sys.stderr)

    # Fetch index (single request)
    try:
        index = fetch_json(f"{BASE}{cfg['index']}?limit=20000")
    except RuntimeError as e:
        print(f"# [{category}] FAILED to fetch index: {e}", file=sys.stderr)
        return

    # Different endpoints expose the result list under different keys.
    # The main indexes use 'results'; attribute and category endpoints
    # expose 'items' instead.
    index_field = cfg.get("index_field", "results")
    all_items = index.get(index_field, [])
    if limit:
        all_items = all_items[:limit]
    to_fetch = [i for i in all_items if i["name"] not in existing]
    total = len(to_fetch)
    print(
        f"# [{category}] {len(all_items)} total, {total} to fetch "
        f"(~{total * delay / 60:.1f} min at {delay}s delay)",
        file=sys.stderr,
    )

    if total == 0:
        print(f"# [{category}] nothing to fetch, done", file=sys.stderr)
        return

    succeeded = 0
    failed = 0
    with open(out_path, "a") as f:
        for i, entry in enumerate(to_fetch, 1):
            name = entry["name"]
            try:
                d = fetch_json(entry["url"])
                record = cfg["extract"](d)
                f.write(json.dumps(record) + "\n")
                f.flush()
                succeeded += 1
            except RuntimeError as e:
                print(f"# [{category}] FAIL {name}: {e}", file=sys.stderr)
                failed += 1

            if i % 25 == 0 or i == total:
                print(f"# [{category}] [{i}/{total}] latest: {name}", file=sys.stderr)

            if i < total:
                time.sleep(delay)

    print(
        f"# [{category}] DONE: {succeeded} written, {failed} failed → {out_path}",
        file=sys.stderr,
    )


def main():
    ap = argparse.ArgumentParser(description="Build local PokeAPI cache as JSONL")
    ap.add_argument("category", choices=list(CATEGORIES.keys()) + ["all"],
                    help="moves | abilities | items | mega_stones | all. "
                         "'items' builds from holdable-active + mega-stones.")
    ap.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds between PokeAPI requests (default 1.0 — be a good citizen)",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only fetch first N entries (useful for testing, 0 = all)",
    )
    args = ap.parse_args()

    if args.category == "all":
        cats = list(CATEGORIES.keys())
    elif args.category == "items":
        # 'items' builds from two sources into items.jsonl
        cats = ["items", "mega_stones"]
    else:
        cats = [args.category]

    for c in cats:
        build(c, args.delay, args.limit)


if __name__ == "__main__":
    main()
