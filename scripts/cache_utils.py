"""
Shared helpers for reading the local PokeAPI cache built by build_cache.py.

Expose a small surface area that any script can import to enrich output
with move / ability / item descriptions without duplicating the loading
and normalization logic. All lookups are best-effort — cache misses
return None so callers can degrade gracefully when the cache isn't fully
populated yet.

Also provides TYPE_CHART (static 18-type multiplier table) and
get_type_matchups() — pair these with types fetched from the pokemon
cache (cache/pokemon.jsonl, built by build_cache.py pokemon) to compute
weakness/resistance/immunity breakdowns for any mon.

Usage:
    from cache_utils import load_all_caches, load_pokemon_cache, short_effect, get_type_matchups

    caches = load_all_caches()
    pkmn = load_pokemon_cache()                      # {normalized_name: {name, types, ...}}
    entry = pkmn.get("charizard")                    # {"name": "charizard", "types": ["fire", "flying"]}
    weak, resist, immune = get_type_matchups(entry["types"])
"""

import json
import os

CACHE_DIR = "cache"
CATEGORIES = ("moves", "abilities", "items")


def normalize_key(display_name: str) -> str:
    """Convert a display-cased move/ability/item name to PokeAPI kebab-case.

    Handles common user inputs: 'Fake Out' -> 'fake-out', 'Rotom-Wash' ->
    'rotom-wash', "King's Shield" -> 'kings-shield', 'Mr. Rime' ->
    'mr-rime'. Matches the normalization used by PokeAPI names.
    """
    return (
        display_name.strip()
        .lower()
        .replace("_", "-")
        .replace(" ", "-")
        .replace("'", "")
        .replace(".", "")
    )


def load_cache(category: str) -> dict[str, dict]:
    """Load cache/{category}.jsonl as a dict keyed by PokeAPI kebab-case name.

    Returns an empty dict if the file doesn't exist yet. Silent failure —
    enrichment is best-effort, not a hard requirement.
    """
    if category not in CATEGORIES:
        raise ValueError(f"unknown category {category!r}, expected one of {CATEGORIES}")

    path = os.path.join(CACHE_DIR, f"{category}.jsonl")
    if not os.path.exists(path):
        return {}

    out: dict[str, dict] = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    out[entry["name"]] = entry
                except (json.JSONDecodeError, KeyError):
                    continue
    except OSError:
        return {}
    return out


def load_all_caches() -> dict[str, dict[str, dict]]:
    """Load all three caches in one call. Returns {'moves': {...}, 'abilities': {...}, 'items': {...}}."""
    return {cat: load_cache(cat) for cat in CATEGORIES}


def lookup(cache_map: dict, display_name: str) -> dict | None:
    """Return the full cache entry for a display-cased name, or None on miss."""
    return cache_map.get(normalize_key(display_name))


def short_effect(cache_map: dict, display_name: str) -> str | None:
    """Return the short effect description for a name, or None on miss.

    Scrubbed of leading/trailing whitespace. Returns None for both
    'entry not in cache' and 'entry exists but has no short effect'.
    """
    entry = lookup(cache_map, display_name)
    if not entry:
        return None
    eff = entry.get("effect") or {}
    short = (eff.get("short") or "").strip()
    return short or None


def long_effect(cache_map: dict, display_name: str) -> str | None:
    """Return the long effect description for a name, or None on miss."""
    entry = lookup(cache_map, display_name)
    if not entry:
        return None
    eff = entry.get("effect") or {}
    long_text = (eff.get("long") or "").strip()
    return long_text or None


# ---------------------------------------------------------------------------
# Pokemon cache (types + base stats, built by build_cache.py pokemon)
# ---------------------------------------------------------------------------

def load_pokemon_cache() -> dict[str, dict]:
    """Load cache/pokemon.jsonl as a dict keyed by PokeAPI kebab-case name.

    Each entry: {"name": "charizard", "types": ["fire", "flying"], "base_stats": {...}}
    Also adds base-name aliases for form-only mons (e.g. morpeko-full-belly → morpeko)
    so lookups by display name work even when PokeAPI stores only form variants.
    Returns empty dict if cache not built yet.
    """
    path = os.path.join(CACHE_DIR, "pokemon.jsonl")
    if not os.path.exists(path):
        return {}
    out: dict[str, dict] = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    out[entry["name"]] = entry
                except (json.JSONDecodeError, KeyError):
                    continue
    except OSError:
        return {}

    # Add base-name aliases for form-only mons: if "morpeko" isn't a key but
    # "morpeko-full-belly" is, register "morpeko" → that entry so display-name
    # lookups don't silently miss. Prefer default-ish suffixes (full-belly,
    # disguised, shield, average, male, etc.) over hangry/blade/etc. so the
    # "representative" form wins when multiple forms share a base.
    _DEFAULT_SUFFIXES = (
        "full-belly", "disguised", "shield", "average", "male",
        "family-of-three", "curly", "zero",
    )
    aliases: dict[str, dict] = {}
    for key, entry in out.items():
        if "-" in key:
            base = key.rsplit("-", 1)[0]
            if base in out or base in aliases:
                continue
            aliases[base] = entry  # first seen — may be overridden below

    # Override with preferred-suffix forms where available
    for key, entry in out.items():
        if "-" in key:
            suffix = key.rsplit("-", 1)[1]
            base = key.rsplit("-", 1)[0]
            if base not in out and suffix in _DEFAULT_SUFFIXES:
                aliases[base] = entry

    out.update(aliases)
    return out


# ---------------------------------------------------------------------------
# Type chart (static 18-type multiplier table)
# ---------------------------------------------------------------------------

TYPE_CHART: dict[str, dict[str, float]] = {
    # {attacking_type: {defending_type: multiplier}}
    "normal":   {"rock": 0.5, "ghost": 0, "steel": 0.5},
    "fire":     {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 2, "bug": 2, "rock": 0.5, "dragon": 0.5, "steel": 2},
    "water":    {"fire": 2, "water": 0.5, "grass": 0.5, "ground": 2, "rock": 2, "dragon": 0.5},
    "grass":    {"fire": 0.5, "water": 2, "grass": 0.5, "poison": 0.5, "ground": 2, "flying": 0.5, "bug": 0.5, "rock": 2, "dragon": 0.5, "steel": 0.5},
    "electric": {"water": 2, "grass": 0.5, "electric": 0.5, "ground": 0, "flying": 2, "dragon": 0.5},
    "ice":      {"fire": 0.5, "water": 0.5, "grass": 2, "ice": 0.5, "ground": 2, "flying": 2, "dragon": 2, "steel": 0.5},
    "fighting": {"normal": 2, "ice": 2, "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0, "dark": 2, "steel": 2, "fairy": 0.5},
    "poison":   {"grass": 2, "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5, "steel": 0, "fairy": 2},
    "ground":   {"fire": 2, "grass": 0.5, "electric": 2, "poison": 2, "flying": 0, "bug": 0.5, "rock": 2, "steel": 2},
    "flying":   {"grass": 2, "electric": 0.5, "fighting": 2, "bug": 2, "rock": 0.5, "steel": 0.5},
    "psychic":  {"fighting": 2, "poison": 2, "psychic": 0.5, "dark": 0, "steel": 0.5},
    "bug":      {"fire": 0.5, "grass": 2, "fighting": 0.5, "poison": 0.5, "flying": 0.5, "psychic": 2, "ghost": 0.5, "dark": 2, "steel": 0.5, "fairy": 0.5},
    "rock":     {"fire": 2, "ice": 2, "fighting": 0.5, "ground": 0.5, "flying": 2, "bug": 2, "steel": 0.5},
    "ghost":    {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5},
    "dragon":   {"dragon": 2, "steel": 0.5, "fairy": 0},
    "dark":     {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5, "fairy": 0.5},
    "steel":    {"fire": 0.5, "water": 0.5, "electric": 0.5, "ice": 2, "rock": 2, "steel": 0.5, "fairy": 2},
    "fairy":    {"fire": 0.5, "poison": 0.5, "fighting": 2, "dragon": 2, "dark": 2, "steel": 0.5},
}


def get_type_matchups(defending_types: list[str]) -> tuple[dict[str, float], dict[str, float], list[str]]:
    """Calculate all type matchups for a list of defending types (lowercase).

    Returns (weaknesses, resistances, immunities):
      weaknesses  — {attacking_type: multiplier} for mult > 1.0
      resistances — {attacking_type: multiplier} for 0 < mult < 1.0
      immunities  — [attacking_type] for mult == 0
    """
    def_types = [t.lower() for t in defending_types]
    weaknesses: dict[str, float] = {}
    resistances: dict[str, float] = {}
    immunities: list[str] = []
    for atk_type, chart in TYPE_CHART.items():
        mult = 1.0
        for def_type in def_types:
            mult *= chart.get(def_type, 1.0)
        if mult > 1.0:
            weaknesses[atk_type] = mult
        elif mult == 0:
            immunities.append(atk_type)
        elif mult < 1.0:
            resistances[atk_type] = mult
    return weaknesses, resistances, immunities


def format_type_matchups(types: list[str]) -> tuple[str | None, str | None]:
    """Return (weak_str, def_str) markdown given a list of defending types.

    weak_str: ⚠️ 4x weaknesses bolded, then 2x weaknesses.
    def_str:  immunities + 0.25x quad resistances.
    """
    weaknesses, resistances, immunities = get_type_matchups(types)

    weak_parts: list[str] = []
    quad_weak = [f"**{t.title()} (4x!)**" for t, m in sorted(weaknesses.items()) if m >= 4]
    double_weak = [t.title() for t, m in sorted(weaknesses.items()) if 1 < m < 4]
    if quad_weak:
        weak_parts.append("⚠️ " + ", ".join(quad_weak))
    if double_weak:
        weak_parts.append(", ".join(double_weak))
    weak_str = " | ".join(weak_parts) if weak_parts else None

    def_parts: list[str] = []
    if immunities:
        def_parts.append("🛡️ Immune: " + ", ".join(t.title() for t in sorted(immunities)))
    quad_resist = [f"{t.title()} (0.25x)" for t, m in sorted(resistances.items()) if m <= 0.25]
    if quad_resist:
        def_parts.append("Quad resists: " + ", ".join(quad_resist))
    def_str = " | ".join(def_parts) if def_parts else None

    return weak_str, def_str
