#!/usr/bin/env python3
"""
Scrape per-Pokemon Champions-legal movepools from Serebii.

Writes cache/champions_movepools.jsonl, one record per Serebii slug:
    {"name": "incineroar", "moves": ["acrobatics", "aerial-ace", ...]}

Why Serebii (not PokeAPI): Serebii's /pokedex-champions/<slug>/ pages list
ONLY moves that are legal in Pokemon Champions — Power Up Punch and other
removed moves are pre-filtered out. PokeAPI gives us mainline SV movepools,
which would require maintaining a Champions removed-moves blocklist.

Idempotent: skips slugs already cached (delete the file to rebuild). At
default 1s delay, ~185 slugs takes ~3 min.

Usage:
    python3 scripts/build_champions_movepools.py
    python3 scripts/build_champions_movepools.py --delay 2
    python3 scripts/build_champions_movepools.py --limit 5     # smoke test
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from urllib.error import HTTPError, URLError

INDEX_URL = "https://www.serebii.net/pokemonchampions/pokemon.shtml"
PAGE_URL = "https://www.serebii.net/pokedex-champions/{slug}/"
OUT_PATH = "cache/champions_movepools.jsonl"
HEADERS = {"User-Agent": "champions-team-builder"}

SLUG_RE = re.compile(r"/pokedex-champions/([a-z0-9\-]+)/")
# Each move row has an anchor to the attackdex page; the slug there strips
# spaces/hyphens (e.g. "Aerial Ace" → "aerialace"), so we use the visible
# anchor text instead and normalize it ourselves.
MOVE_RE = re.compile(
    r'<a href="/attackdex-champions/[^"]+\.shtml">([^<]+)</a>'
)


def fetch(url: str, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                # Serebii pages use Latin-1; UTF-8 decode chokes on é etc.
                return resp.read().decode("latin-1")
        except (HTTPError, URLError) as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"fetch failed: {e}")
    return ""


def normalize_move(name: str) -> str:
    """Match PokeAPI naming in cache/moves.jsonl: lowercase, hyphenated."""
    return (
        name.strip()
        .lower()
        .replace("_", "-")
        .replace(" ", "-")
        .replace(".", "")
        .replace("'", "")
    )


def extract_slugs(index_html: str) -> list[str]:
    return sorted(set(SLUG_RE.findall(index_html)))


def extract_moves(page_html: str) -> list[str]:
    """Pull all move anchor texts. The page only has one moves table
    (Standard Moves), so a global anchor scan is safe."""
    raw = MOVE_RE.findall(page_html)
    return sorted({normalize_move(m) for m in raw})


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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--delay", type=float, default=1.0,
                    help="Seconds between requests (default 1.0)")
    ap.add_argument("--limit", type=int, default=0,
                    help="Only fetch first N slugs (0 = all)")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    existing = load_existing_names(OUT_PATH)
    print(f"# {len(existing)} already cached at {OUT_PATH}", file=sys.stderr)

    print(f"# fetching index: {INDEX_URL}", file=sys.stderr)
    try:
        index_html = fetch(INDEX_URL)
    except RuntimeError as e:
        print(f"# FAILED to fetch index: {e}", file=sys.stderr)
        sys.exit(1)

    slugs = extract_slugs(index_html)
    if args.limit:
        slugs = slugs[: args.limit]
    todo = [s for s in slugs if s not in existing]
    print(
        f"# {len(slugs)} total slugs, {len(todo)} to fetch "
        f"(~{len(todo) * args.delay / 60:.1f} min at {args.delay}s delay)",
        file=sys.stderr,
    )

    if not todo:
        print("# nothing to fetch, done", file=sys.stderr)
        return

    succeeded = 0
    empty = 0
    failed = 0
    with open(OUT_PATH, "a") as f:
        for i, slug in enumerate(todo, 1):
            try:
                html = fetch(PAGE_URL.format(slug=slug))
                moves = extract_moves(html)
            except RuntimeError as e:
                print(f"# FAIL {slug}: {e}", file=sys.stderr)
                failed += 1
                if i < len(todo):
                    time.sleep(args.delay)
                continue

            # Pages without a moves table (rare, but possible for
            # alt-form redirects) are written with empty moves so we
            # don't refetch them on rerun.
            if not moves:
                empty += 1
            f.write(json.dumps({"name": slug, "moves": moves}) + "\n")
            f.flush()
            succeeded += 1

            if i % 25 == 0 or i == len(todo):
                print(
                    f"# [{i}/{len(todo)}] latest: {slug} ({len(moves)} moves)",
                    file=sys.stderr,
                )
            if i < len(todo):
                time.sleep(args.delay)

    print(
        f"# DONE: {succeeded} written ({empty} empty), {failed} failed → {OUT_PATH}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
