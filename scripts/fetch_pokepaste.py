#!/usr/bin/env python3
"""
Fetch and parse a PokePaste team into structured JSON.

PokePaste (https://pokepast.es) is the standard public pastebin for Pokemon
teams in Showdown format. Team builders and tournament reports link to paste
URLs everywhere in the VGC community, so this lets Julia drop any paste URL
and get a fully-parsed, cache-enriched team analysis.

Usage:
    python3 scripts/fetch_pokepaste.py https://pokepast.es/3cf32474136c06f5
    python3 scripts/fetch_pokepaste.py 3cf32474136c06f5

Output: JSON with the paste title, author, notes, and each of 6 mons parsed
into name / species / item / ability / nature / evs / ivs / moves, plus short
effect descriptions from the local PokeAPI cache where available.

Champions caveats handled:
- Tera Type is stripped from the Champions view (vestigial in that format)
  but preserved under raw_tera for reference.
- Items that don't exist in Champions are flagged with a warning field.
"""

import argparse
import json
import re
import urllib.request
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError

from cache_utils import load_all_caches, short_effect

BASE = "https://pokepast.es"
HEADERS = {"User-Agent": "champions-team-builder"}

# Items known to NOT exist in Champions (from CLAUDE.md items list).
# Used to flag Smogon-format pastes that will need item substitution.
CHAMPIONS_MISSING_ITEMS = {
    "life orb", "choice band", "choice specs", "assault vest",
    "rocky helmet", "flame orb", "toxic orb", "loaded dice",
    "eject button", "safety goggles", "clear amulet", "throat spray",
    "air balloon", "covert cloak", "mirror herb", "heavy-duty boots",
    "black sludge", "weakness policy", "eject pack", "power herb",
    "shed shell", "eviolite",
}


class TagStripper(HTMLParser):
    """Minimal HTML tag stripper — keeps text content only."""

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data):
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def strip_tags(html: str) -> str:
    p = TagStripper()
    p.feed(html)
    return p.text()


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def normalize_url(user_input: str) -> str:
    """Accept full URL or bare ID, return full URL."""
    user_input = user_input.strip()
    if user_input.startswith("http"):
        return user_input
    # Strip any accidental pokepast.es/ prefix without scheme
    user_input = re.sub(r"^(www\.)?pokepast\.es/", "", user_input)
    return f"{BASE}/{user_input}"


def extract_articles(html: str) -> list[str]:
    """Return the plain-text inside each <article><pre>...</pre></article>."""
    articles = re.findall(r"<article>(.*?)</article>", html, re.DOTALL)
    pastes = []
    for a in articles:
        pre_match = re.search(r"<pre>(.*?)</pre>", a, re.DOTALL)
        if not pre_match:
            continue
        pastes.append(strip_tags(pre_match.group(1)))
    return pastes


def parse_paste_meta(html: str) -> dict[str, str | None]:
    """Extract title / author / notes from the HTML head + metadata."""
    meta: dict[str, str | None] = {"title": None, "author": None, "notes": None}
    title_m = re.search(r"<title>([^<]*)</title>", html)
    if title_m:
        meta["title"] = title_m.group(1).strip() or None
    aside_m = re.search(r'<aside[^>]*>(.*?)</aside>', html, re.DOTALL)
    if aside_m:
        aside_text = strip_tags(aside_m.group(1)).strip()
        # Author / notes usually live in the aside. Keep raw text.
        meta["notes"] = aside_text or None
    return meta


def parse_evs_ivs(text: str) -> dict[str, int]:
    """Parse '252 HP / 4 Def / 252 SpD' → {'hp': 252, 'def': 4, 'spd': 252}."""
    out: dict[str, int] = {}
    for chunk in text.split("/"):
        chunk = chunk.strip()
        m = re.match(r"(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)", chunk, re.IGNORECASE)
        if m:
            out[m.group(2).lower()] = int(m.group(1))
    return out


def parse_pokemon_block(text: str) -> dict[str, Any]:
    """Parse a single Showdown-format Pokemon block into structured fields."""
    lines = [l.rstrip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return {}

    mon: dict[str, Any] = {
        "nickname": None,
        "species": None,
        "gender": None,
        "item": None,
        "ability": None,
        "level": None,
        "shiny": False,
        "raw_tera": None,  # preserved from paste; ignore for Champions play
        "nature": None,
        "evs": {},
        "ivs": {},
        "moves": [],
    }

    # First line: [Nickname] (Species) (Gender) @ Item
    first = lines[0]
    # Split off item first
    item_match = re.search(r"\s+@\s+(.+?)\s*$", first)
    if item_match:
        mon["item"] = item_match.group(1).strip()
        first = first[: item_match.start()]
    # Now: Nickname (Species) (Gender), or just Species, or Species (Gender)
    gender_match = re.search(r"\s*\((M|F)\)\s*$", first)
    if gender_match:
        mon["gender"] = gender_match.group(1)
        first = first[: gender_match.start()]
    # If there's a parenthesized species, it's "Nickname (Species)"
    species_match = re.search(r"^(.+?)\s*\((.+?)\)\s*$", first)
    if species_match:
        mon["nickname"] = species_match.group(1).strip()
        mon["species"] = species_match.group(2).strip()
    else:
        mon["species"] = first.strip()

    # Remaining lines
    for line in lines[1:]:
        if line.startswith("-"):
            move = line.lstrip("- ").strip()
            if move:
                mon["moves"].append(move)
        elif line.startswith("Ability:"):
            mon["ability"] = line.split(":", 1)[1].strip()
        elif line.startswith("Level:"):
            try:
                mon["level"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("Shiny:"):
            mon["shiny"] = "yes" in line.lower()
        elif line.startswith("Tera Type:"):
            mon["raw_tera"] = line.split(":", 1)[1].strip()
        elif line.startswith("EVs:"):
            mon["evs"] = parse_evs_ivs(line.split(":", 1)[1])
        elif line.startswith("IVs:"):
            mon["ivs"] = parse_evs_ivs(line.split(":", 1)[1])
        elif line.endswith("Nature"):
            mon["nature"] = line.replace("Nature", "").strip()

    return mon


def enrich(mon: dict, caches: dict) -> dict:
    """Add short effect descriptions from the local cache."""
    moves_cache = caches.get("moves", {})
    abilities_cache = caches.get("abilities", {})
    items_cache = caches.get("items", {})

    enriched = dict(mon)

    if mon["item"]:
        enriched["item_effect"] = short_effect(items_cache, mon["item"])
        if mon["item"].lower() in CHAMPIONS_MISSING_ITEMS:
            enriched["item_warning"] = (
                f"{mon['item']} is NOT available in Pokemon Champions — "
                "this build needs a substitute (see CLAUDE.md items list)."
            )
    if mon["ability"]:
        enriched["ability_effect"] = short_effect(abilities_cache, mon["ability"])
    if mon["moves"]:
        enriched["moves_enriched"] = [
            {"name": mv, "effect": short_effect(moves_cache, mv)}
            for mv in mon["moves"]
        ]
    return enriched


def fetch_paste(user_input: str) -> dict:
    url = normalize_url(user_input)
    try:
        html = fetch(url)
    except (HTTPError, URLError) as e:
        return {"error": f"failed to fetch {url}: {e}", "url": url}

    meta = parse_paste_meta(html)
    articles = extract_articles(html)
    if not articles:
        return {"error": "no team found at URL", "url": url, **meta}

    caches = load_all_caches()
    team = [enrich(parse_pokemon_block(a), caches) for a in articles]

    return {
        "url": url,
        "title": meta["title"],
        "notes": meta["notes"],
        "team_size": len(team),
        "team": team,
    }


def main():
    ap = argparse.ArgumentParser(
        description="Fetch and parse a PokePaste team into structured JSON",
    )
    ap.add_argument("paste", help="PokePaste URL or bare ID")
    args = ap.parse_args()

    result = fetch_paste(args.paste)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
