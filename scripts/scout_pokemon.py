#!/usr/bin/env python3
"""
Scout report: concise competitive summary for Pokemon.
Outputs role, key moves, ability, item, teammates, and gameplan.
Enriches moves/abilities/items with short effect descriptions from the
local cache (cache/*.jsonl, built by scripts/build_cache.py) when
available — falls back silently on cache miss.

Usage: python3 scripts/scout_pokemon.py Name1 Name2 ...
"""

import sys
import urllib.request

from cache_utils import (  # noqa: F401
    load_all_caches,
    load_pokemon_cache,
    short_effect,
    format_type_matchups,
    normalize_key,
)

BASE = "https://pikalytics.com/ai/pokedex/championspreview"

def fetch(name):
    url = f"{BASE}/{name}"
    req = urllib.request.Request(url, headers={"User-Agent": "pokemon-champions-scout/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode()

def parse_pokemon(name):
    """Fetch and parse into a compact scouting report."""
    try:
        raw = fetch(name)
    except Exception as e:
        return {"name": name, "error": str(e)}

    lines = raw.strip().split("\n")

    report = {"name": name, "moves": [], "abilities": [], "items": [], "teammates": [], "stats": {}}

    section = None
    for line in lines:
        l = line.strip()
        if not l:
            continue
        # Detect sections — Pikalytics uses "## Common Moves" format
        ll = l.lower()
        if "move" in ll and l.startswith("##"):
            section = "moves"
            continue
        elif "abilit" in ll and l.startswith("##"):
            section = "abilities"
            continue
        elif "item" in ll and l.startswith("##"):
            section = "items"
            continue
        elif "teammate" in ll and l.startswith("##"):
            section = "teammates"
            continue
        elif "stat" in ll and l.startswith("##"):
            section = "stats"
            continue
        elif l.startswith("## "):
            section = "other"
            continue

        # Parse markdown list items: "- **Name**: 12.345%"
        if l.startswith("- **") and section in ("moves", "abilities", "items", "teammates"):
            import re
            m = re.match(r'- \*\*(.+?)\*\*:?\s*([\d.]+)%', l)
            if m:
                name_val = m.group(1)
                pct = float(m.group(2))

                if section == "moves" and len(report["moves"]) < 8:
                    report["moves"].append({"name": name_val, "pct": pct})
                elif section == "abilities" and len(report["abilities"]) < 3:
                    report["abilities"].append({"name": name_val, "pct": pct})
                elif section == "items" and len(report["items"]) < 5:
                    report["items"].append({"name": name_val, "pct": pct})
                elif section == "teammates" and len(report["teammates"]) < 4:
                    report["teammates"].append({"name": name_val, "pct": pct})

        # Also parse table rows as fallback
        if l.startswith("|") and not l.startswith("|-") and "---" not in l:
            cols = [c.strip() for c in l.split("|")[1:-1]]
            if len(cols) >= 2:
                if cols[0].lower() in ("move", "ability", "item", "pokemon", "teammate", "stat", "name", "property"):
                    continue

                # Stats table has integer values, not percentages.
                if section == "stats":
                    stat_name = (
                        cols[0]
                        .lower()
                        .replace("**", "")
                        .replace(".", "")
                        .replace(" ", "_")
                        .strip()
                    )
                    try:
                        val = int(cols[1].replace("**", "").strip())
                        report["stats"][stat_name] = val
                    except ValueError:
                        pass
                    continue

                try:
                    pct = float(cols[1].replace("%", ""))
                except ValueError:
                    pct = 0

                if section == "moves" and len(report["moves"]) < 8:
                    report["moves"].append({"name": cols[0], "pct": pct})
                elif section == "abilities" and len(report["abilities"]) < 3:
                    report["abilities"].append({"name": cols[0], "pct": pct})
                elif section == "items" and len(report["items"]) < 5:
                    report["items"].append({"name": cols[0], "pct": pct})
                elif section == "teammates" and len(report["teammates"]) < 4:
                    report["teammates"].append({"name": cols[0], "pct": pct})

    return report


def classify_stats(stats: dict) -> list[str]:
    """Return role tags derived from base stat distribution.

    Complements classify_role (which is move-based). Stats reveal identity
    that moves alone can't — e.g. Avalugg is a Body Press wall regardless
    of which attacks are on the set, because Defense 184 dwarfs everything
    else. These tags capture that structural identity.
    """
    if not stats:
        return []

    hp = stats.get("hp", 0)
    atk = stats.get("attack", 0)
    d_def = stats.get("defense", 0)
    spa = stats.get("sp_atk", 0)
    spd = stats.get("sp_def", 0)
    spe = stats.get("speed", 0)

    tags: list[str] = []

    # Speed tier — determines speed control needs
    if spe <= 40:
        tags.append("TR candidate")
    elif spe <= 60:
        tags.append("Slow (wants TR/Tailwind)")
    elif spe >= 110:
        tags.append("Fast natural speed")

    # Defensive profile
    phys_wall = d_def >= 130 and hp >= 80
    spec_wall = spd >= 130 and hp >= 80
    if phys_wall and spec_wall:
        tags.append("Mixed wall")
    elif phys_wall:
        tags.append("Physical wall")
    elif spec_wall:
        tags.append("Special wall")

    # Body Press scaling — high Def + modest Attack means the Def stat IS the offense
    if d_def >= 140 and atk < 100:
        tags.append("Body Press user (Def-scales)")

    # Offensive bias
    if atk >= 120 and spa <= 70:
        tags.append("Pure physical")
    elif spa >= 120 and atk <= 70:
        tags.append("Pure special")
    elif atk >= 100 and spa >= 100:
        tags.append("Mixed attacker")

    # Glass cannon flag — high offense, low HP, fragile
    if hp <= 65 and max(atk, spa) >= 110:
        tags.append("Glass cannon")

    # Defensive glass jaw — strong one defense but weak on the other side
    if (d_def >= 120 and spd <= 60) or (spd >= 120 and d_def <= 60):
        tags.append("One-sided defense (mixed threats break it)")

    return tags

def classify_role(report):
    """Infer the competitive role from move distribution."""
    moves = {m["name"].lower(): m["pct"] for m in report.get("moves", [])}

    tags = []

    # Support indicators
    support_moves = ["fake out", "follow me", "rage powder", "helping hand", "parting shot",
                     "tailwind", "trick room", "light screen", "reflect", "will-o-wisp",
                     "thunder wave", "yawn", "sleep powder", "spore", "encore", "taunt",
                     "ally switch", "heal pulse", "life dew", "friend guard", "coaching",
                     "icy wind", "electroweb", "snarl", "haze", "wide guard", "quick guard",
                     "super fang", "u-turn", "flip turn", "volt switch"]
    setup_moves = ["swords dance", "dragon dance", "calm mind", "nasty plot", "belly drum",
                   "curse", "shell smash", "quiver dance", "shift gear", "iron defense",
                   "bulk up", "work up"]
    protect_moves = ["protect", "detect", "king's shield", "baneful bunker", "spiky shield",
                     "silk trap", "burning bulwark"]

    support_pct = sum(moves.get(m, 0) for m in support_moves)
    setup_pct = sum(moves.get(m, 0) for m in setup_moves)
    protect_pct = sum(moves.get(m, 0) for m in protect_moves)

    # Check for specific roles
    if moves.get("fake out", 0) > 10:
        tags.append("Fake Out lead")
    if moves.get("tailwind", 0) > 10:
        tags.append("Tailwind setter")
    if moves.get("trick room", 0) > 10:
        tags.append("Trick Room setter")
    if moves.get("follow me", 0) > 5 or moves.get("rage powder", 0) > 5:
        tags.append("Redirector")
    if moves.get("parting shot", 0) > 5 or moves.get("u-turn", 0) > 10 or moves.get("flip turn", 0) > 10 or moves.get("volt switch", 0) > 10:
        tags.append("Pivot")
    if any(moves.get(m, 0) > 5 for m in ["will-o-wisp", "thunder wave", "sleep powder", "spore", "yawn"]):
        tags.append("Status spreader")
    if any(moves.get(m, 0) > 5 for m in ["light screen", "reflect"]):
        tags.append("Screens setter")
    if any(moves.get(m, 0) > 5 for m in setup_moves):
        setup_name = [m for m in setup_moves if moves.get(m, 0) > 5][0].title()
        tags.append(f"Setup ({setup_name})")
    if moves.get("perish song", 0) > 3:
        tags.append("Perish trapper")

    if support_pct > 40:
        tags.insert(0, "Support")
    elif setup_pct > 10:
        tags.insert(0, "Setup sweeper")
    else:
        tags.insert(0, "Attacker")

    return tags

def format_report(report, moves_cache=None, abilities_cache=None, items_cache=None, pokemon_cache=None):
    """Format a single pokemon into a compact text block.

    If cache dicts are provided, appends short effect descriptions inline
    for moves, abilities, and items. Cache misses are skipped silently.
    pokemon_cache is used to look up types for type matchup display.
    """
    moves_cache = moves_cache or {}
    abilities_cache = abilities_cache or {}
    items_cache = items_cache or {}
    pokemon_cache = pokemon_cache or {}

    if "error" in report:
        err = report["error"]
        if "404" in str(err):
            msg = "no Pikalytics data — zero or near-zero Champions ladder usage"
        else:
            msg = f"fetch error: {err}"
        return f"### {report['name']}\n({msg})\n"

    name = report["name"]
    moves = sorted(report.get("moves", []), key=lambda x: x["pct"], reverse=True)
    abilities = sorted(report.get("abilities", []), key=lambda x: x["pct"], reverse=True)
    items = sorted(report.get("items", []), key=lambda x: x["pct"], reverse=True)
    teammates = sorted(report.get("teammates", []), key=lambda x: x["pct"], reverse=True)

    move_roles = classify_role(report)
    stat_roles = classify_stats(report.get("stats", {}))
    seen = set()
    roles = []
    for tag in move_roles + stat_roles:
        if tag not in seen:
            seen.add(tag)
            roles.append(tag)

    pkmn_entry = pokemon_cache.get(normalize_key(name))
    types = pkmn_entry.get("types") if pkmn_entry else None
    type_str = "/".join(t.title() for t in types) if types else "???"

    lines = [f"### {name} [{type_str}]"]
    lines.append(f"**Role:** {' / '.join(roles)}")

    stats = report.get("stats", {})
    if stats:
        parts = []
        for key, label in [
            ("hp", "HP"),
            ("attack", "Atk"),
            ("defense", "Def"),
            ("sp_atk", "SpA"),
            ("sp_def", "SpD"),
            ("speed", "Spe"),
        ]:
            if key in stats:
                parts.append(f"{label} {stats[key]}")
        if parts:
            lines.append(f"**Stats:** {' / '.join(parts)}")

    if types:
        weak_str, def_str = format_type_matchups(types)
        if weak_str:
            lines.append(f"**Weak to:** {weak_str}")
        if def_str:
            lines.append(f"**Defenses:** {def_str}")

    if abilities:
        top_ab = abilities[0]
        low_sample = top_ab["pct"] < 10
        ab_str = f"**Ability:** {top_ab['name']} ({top_ab['pct']}%)"
        if low_sample:
            # Data too thin for a clear winner — show all options
            if len(abilities) > 1:
                alt = " | ".join(f"{a['name']} ({a['pct']}%)" for a in abilities[1:])
                ab_str += f" | {alt}"
            ab_str += "  ⚠️ low sample"
        elif len(abilities) > 1 and abilities[1]["pct"] > 5:
            ab_str += f" | {abilities[1]['name']} ({abilities[1]['pct']}%)"
        lines.append(ab_str)
        desc = short_effect(abilities_cache, top_ab["name"])
        if desc:
            lines.append(f"    ↳ {desc}")

    if items:
        items_str = " > ".join(f"{i['name']} ({i['pct']}%)" for i in items[:3])
        lines.append(f"**Items:** {items_str}")
        top_item = items[0]
        desc = short_effect(items_cache, top_item["name"])
        if desc:
            lines.append(f"    ↳ {top_item['name']}: {desc}")

    if moves:
        top4 = moves[:4]
        rest = moves[4:]
        moves_str = ", ".join(f"**{m['name']}** ({m['pct']}%)" for m in top4)
        lines.append(f"**Core moves:** {moves_str}")
        for mv in top4:
            desc = short_effect(moves_cache, mv["name"])
            if desc:
                lines.append(f"    ↳ {mv['name']}: {desc}")
        if rest:
            alt_str = ", ".join(f"{m['name']} ({m['pct']}%)" for m in rest)
            lines.append(f"**Alt moves:** {alt_str}")

    if teammates:
        tm_str = ", ".join(f"{t['name']} ({t['pct']}%)" for t in teammates[:4])
        lines.append(f"**Pairs with:** {tm_str}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/scout_pokemon.py Name1 Name2 ...")
        sys.exit(1)

    # Load caches once per invocation — graceful no-op if files don't exist.
    caches = load_all_caches()
    pkmn_cache = load_pokemon_cache()

    names = sys.argv[1:]
    for name in names:
        report = parse_pokemon(name)
        print(
            format_report(
                report,
                moves_cache=caches["moves"],
                abilities_cache=caches["abilities"],
                items_cache=caches["items"],
                pokemon_cache=pkmn_cache,
            )
        )
        print()
