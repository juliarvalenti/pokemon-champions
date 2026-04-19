#!/usr/bin/env python3
"""
Scrape authoritative Pokemon Champions facts from Serebii.

Serebii's Champions section is the source of truth for "does this exist in
Champions / does it work differently than mainline?" The PokeAPI cache we
already have is generic Scarlet/Violet data — it doesn't know about
Champions-original abilities (Spicy Spray, Dragonize, Mega Sol, etc.), the
reduced item pool, or which Pokemon Megas into what ability.

Output files:
    cache/champions_items.jsonl       — one per item: name, effect, cost
    cache/champions_abilities.jsonl   — one per ability: name, effect,
                                        kind ("new" | "updated" | "mega"),
                                        pokemon (for mega entries)

Idempotent: deletes and rewrites the two output files on each run. Total
runtime ~5 seconds (4 pages + polite 1s delay).

Usage:
    python3 scripts/build_champions_cache.py
    python3 scripts/build_champions_cache.py --delay 2

After rebuild, `scripts/lookup.py` picks up the new files automatically.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from urllib.error import HTTPError, URLError

BASE = "https://www.serebii.net/pokemonchampions"
PAGES = {
    "items": f"{BASE}/items.shtml",
    "new": f"{BASE}/newabilities.shtml",
    "updated": f"{BASE}/updatedabilities.shtml",
    "mega": f"{BASE}/megaabilities.shtml",
}
HEADERS = {"User-Agent": "champions-team-builder"}

ITEMS_OUT = "cache/champions_items.jsonl"
ABILITIES_OUT = "cache/champions_abilities.jsonl"


def normalize(name: str) -> str:
    """Match PokeAPI-style kebab-case for cross-cache lookups."""
    return (
        name.strip()
        .lower()
        .replace("&eacute;", "e")
        .replace("&#233;", "e")
        .replace("_", "-")
        .replace(" ", "-")
        .replace(".", "")
        .replace("'", "")
    )


def clean(text: str) -> str:
    """Strip HTML tags and decode Serebii's quirky entity set."""
    text = re.sub(r"<[^>]+>", "", text)
    text = (
        text.replace("&eacute;", "e")
        .replace("&#233;", "e")
        .replace("&amp;", "&")
        .replace("&nbsp;", " ")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    return re.sub(r"\s+", " ", text).strip()


def fetch(url: str, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("latin-1")
        except (HTTPError, URLError) as e:
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"fetch failed: {e}")
    return ""


# ---------- page parsers ----------

# Items: <tr height="32"> <td class="cen"><a href="/itemdex/x"><img .../></a></td>
#   <td class="fooinfo"><a href="/itemdex/x">Name</a></td>
#   <td class="fooinfo">effect text</td>
#   <td class="fooinfo"><br /><b>Shop</b><br />700 VP</td>    (or "Beginning")
ITEM_ROW = re.compile(
    r'<tr height="32">\s*'
    r'<td class="cen"><a href="/itemdex/[^"]+">.*?</a></td>\s*'
    r'<td class="fooinfo"><a href="/itemdex/[^"]+">([^<]+)</a></td>\s*'
    r'<td class="fooinfo">(.*?)</td>\s*'
    r'<td class="fooinfo">(.*?)</td>\s*'
    r'</tr>',
    re.DOTALL,
)


def parse_items(html: str) -> list[dict]:
    out = []
    for m in ITEM_ROW.finditer(html):
        name_raw, effect_raw, cost_raw = m.groups()
        name = clean(name_raw)
        effect = clean(effect_raw)
        cost_text = clean(cost_raw)
        # cost can be "Beginning" (starting item) or "Shop 700 VP" (purchasable)
        if "Beginning" in cost_text:
            cost = {"source": "starting", "vp": 0}
        else:
            vp_match = re.search(r"(\d+)\s*VP", cost_text)
            cost = {
                "source": "shop",
                "vp": int(vp_match.group(1)) if vp_match else None,
            }
        out.append({
            "name": normalize(name),
            "display_name": name,
            "effect": effect,
            "cost": cost,
        })
    return out


# New abilities: <tr><td class="fooinfo"><a href="/abilitydex/x"><u>Name</u></a></td>
#   <td class="fooinfo">effect</td></tr>
NEW_ABILITY_ROW = re.compile(
    r'<tr>\s*'
    r'<td class="fooinfo"><a href="/abilitydex/[^"]+"><u>([^<]+)</u></a></td>\s*'
    r'<td class="fooinfo">(.*?)</td>\s*'
    r'</tr>',
    re.DOTALL,
)


def parse_new_abilities(html: str) -> list[dict]:
    out = []
    for m in NEW_ABILITY_ROW.finditer(html):
        name = clean(m.group(1))
        effect = clean(m.group(2))
        out.append({
            "name": normalize(name),
            "display_name": name,
            "kind": "new",
            "effect": effect,
        })
    return out


# Updated abilities: 3-col rows, name / description / addition
UPDATED_ABILITY_ROW = re.compile(
    r'<tr>\s*'
    r'<td class="fooinfo">\s*<a href="/abilitydex/[^"]+">([^<]+)</a>\s*</td>\s*'
    r'<td class="fooinfo">\s*(.*?)\s*</td>\s*'
    r'<td class="fooinfo">\s*(.*?)\s*</td>\s*'
    r'</tr>',
    re.DOTALL,
)


def parse_updated_abilities(html: str) -> list[dict]:
    out = []
    for m in UPDATED_ABILITY_ROW.finditer(html):
        name = clean(m.group(1))
        desc = clean(m.group(2))
        addition = clean(m.group(3))
        out.append({
            "name": normalize(name),
            "display_name": name,
            "kind": "updated",
            "effect": desc,
            "change": addition,
        })
    return out


# Mega abilities: 5-col rows — No. / Pic / "Mega X" link / type imgs / ability link
# The name cell contains a link like <a href="/pokedex-champions/clefable/">Mega Clefable</a>
MEGA_ABILITY_ROW = re.compile(
    r'<tr>\s*'
    r'<td align="center" class="fooinfo">\s*#\d+\s*</td>\s*'              # No.
    r'<td align="center" class="fooinfo">.*?</td>\s*'                     # Pic
    r'<td align="center" class="fooinfo">\s*'
    r'<a href="/pokedex-champions/([^/]+)/">([^<]+)</a>\s*</td>\s*'       # slug + display
    r'<td align="center" class="fooinfo">.*?</td>\s*'                     # types (images)
    r'<td align="center" class="fooinfo">\s*'
    r'<a href="/abilitydex/[^"]+">([^<]+)</a>\s*</td>\s*'                 # ability
    r'</tr>',
    re.DOTALL,
)


def parse_mega_abilities(html: str) -> list[dict]:
    out = []
    for m in MEGA_ABILITY_ROW.finditer(html):
        slug, display, ability = m.groups()
        ability_clean = clean(ability)
        out.append({
            "name": f"mega-{normalize(slug)}",
            "display_name": clean(display),
            "kind": "mega",
            "pokemon": normalize(slug),
            "ability": normalize(ability_clean),
            "ability_display": ability_clean,
        })
    return out


# ---------- driver ----------

def write_jsonl(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--delay", type=float, default=1.0,
                    help="Seconds between requests (default 1.0)")
    args = ap.parse_args()

    # Fetch all four pages with polite delay.
    pages = {}
    for i, (key, url) in enumerate(PAGES.items()):
        print(f"# [{i+1}/{len(PAGES)}] fetching {key}: {url}", file=sys.stderr)
        pages[key] = fetch(url)
        if i < len(PAGES) - 1:
            time.sleep(args.delay)

    items = parse_items(pages["items"])
    new_abilities = parse_new_abilities(pages["new"])
    updated_abilities = parse_updated_abilities(pages["updated"])
    mega_abilities = parse_mega_abilities(pages["mega"])

    abilities = new_abilities + updated_abilities + mega_abilities

    write_jsonl(ITEMS_OUT, items)
    write_jsonl(ABILITIES_OUT, abilities)

    print(
        f"# DONE: {len(items)} items → {ITEMS_OUT}",
        file=sys.stderr,
    )
    print(
        f"# DONE: {len(abilities)} abilities "
        f"({len(new_abilities)} new, {len(updated_abilities)} updated, "
        f"{len(mega_abilities)} mega) → {ABILITIES_OUT}",
        file=sys.stderr,
    )

    if len(items) < 10 or len(abilities) < 10:
        print(
            "# WARNING: low counts — Serebii layout may have changed, "
            "re-check regex patterns in this script.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
