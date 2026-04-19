# pokemon-champions

Personal Claude Code project for building competitive Pokemon Champions VGC 2026 teams.

A team-building agent grounded in real usage data — Pikalytics meta stats, Smogon sample sets, Limitless tournament results, and a local PokeAPI cache for authoritative move/ability/item lookups. Champions-specific movepools are scraped from Serebii since the format diverges from mainline Scarlet/Violet (removed moves, new mega abilities, no Tera, smaller item pool).

## Layout

- **`CLAUDE.md`** — project instructions, format rules, item/ability/nature reference
- **`team/`** — current roster, active comp, planned alts
- **`research/`** — meta snapshot, archetype templates, type-trait gotchas
- **`scripts/`** — data fetchers (Pikalytics, Smogon, Limitless, Reddit, PokePaste, Serebii) + local cache lookup/query
- **`cache/`** — local JSONL cache of moves, abilities, items, Pokemon stats, Champions movepools

## Usage

Open in Claude Code and ask team-building questions. The agent reads `CLAUDE.md`, `team/`, and `research/` for context, runs the data scripts as needed, and grounds recommendations in current usage.
