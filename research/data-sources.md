# Data Sources

*Status of every external data source we've evaluated for Pokemon Champions team building. Read this before suggesting "let's try X" — we may have already checked X.*

## Active Sources (in use)

### Pikalytics championspreview ✅
- **URL:** `https://pikalytics.com/ai/pokedex/championspreview` (top 50) and `/{Name}` (per-Pokemon)
- **Script:** `scripts/fetch_meta.py`, `scripts/fetch_pokemon.py`
- **What it gives us:** Real Champions usage data — moves, items, abilities, teammates, sample teams, with usage percentages
- **Caveats:**
  - Updates monthly, may lag behind tournament meta shifts
  - Includes items that don't exist in Champions (Life Orb, Flame Orb, Choice Band/Specs, Assault Vest, Rocky Helmet, etc.) — cross-reference against `CLAUDE.md` items list
  - Does NOT include Paradox Pokemon (Flutter Mane, Iron Hands, etc.) — they're either filtered or not in Champions' legal pool
  - References Tera types in sample team data — IGNORE, Tera doesn't exist in Champions

### Smogon Strategy Pokedex (via data.pkmn.cc) ✅
- **URL:** `https://data.pkmn.cc/sets/{format}.json` (gen9vgc2024, gen9doublesou, gen9)
- **Script:** `scripts/fetch_smogon.py`
- **What it gives us:** Named expert-tuned competitive sets (moves/ability/item/nature/EVs/tera) across multiple formats. Has doubles-vs-singles split.
- **Caveats:**
  - VGC2024 / DoublesOU files only cover ~50-80 most popular meta mons
  - Singles formats (gen9.json) are a fallback for less popular doubles mons but DON'T translate directly — they lack Fake Out / Wide Guard / spread moves
  - References Tera types — IGNORE
  - Many recommended items don't exist in Champions

## Evaluated, NOT in use

### limitlessvgc.com ⚠️ (no Champions data, wrong site)
- **URL:** `https://limitlessvgc.com/tournaments`
- **Status:** Site exists, has a "CHAMPIONS" format filter, but **returns no results** as of 2026-04-13. They're still cataloging mainline VGC tournaments only (most recent is "Scarlet & Violet - Regulation I").
- **Verdict:** Wrong site for Champions data. Use `play.limitlesstcg.com` instead (see below).

### play.limitlesstcg.com ✅ (HAS Champions tournament data)
- **URLs:**
  - Standings: `https://play.limitlesstcg.com/tournament/{tournamentId}/standings`
  - Teamlist: `https://play.limitlesstcg.com/tournament/{tournamentId}/player/{username}/teamlist`
- **Status:** This is the **actual** Limitless tournament-running platform that hosts live Champions events. Different from `limitlessvgc.com` (which is the archive site). Has real Champions tournaments like "Pokemon Champions Challenge #1" with 100+ players and full team lists.
- **What it gives us:** For each player team — Pokemon, held item, ability, all 4 moves. Full enough to clone a winning build.
- **What it does NOT give us:** Nature, EVs / Stat Points, exact spreads. These are not displayed publicly. You'd have to infer the build from typical optimization principles.
- **⚠️ Tera Type field caveat:** The site shows a "Tera Type" for each Pokemon, but this is **vestigial UI data** from Limitless's standard VGC team format. Champions doesn't have Tera. Ignore the Tera field even though it appears in the data.
- **Verdict:** **Worth building a fetcher.** Best source for Champions tournament team data discovered so far. Script not built yet — see TODO below.

**Script:** `scripts/fetch_limitless_tournament.py <tournament_id> [--top N]` ✅ Built 2026-04-13.

### Champions Lab (championslab.xyz) ⚠️ (open source but static data)
- **URL:** `https://www.championslab.xyz/`, source at `https://github.com/Andrew21P/ChampionsLab`
- **Status:** Active site with team builder, meta dashboard, battle simulator. Claims to have tournament data from 250+ real results. **Open source MIT license.**
- **Data structure:** All Pokemon data is statically baked into TypeScript files in `src/lib/`. No live API. Tournament data is hand-transcribed from "Victory Road, Pokemon Global Link, Limitless VGC archives" per the source comments.
- **What we could do:** Fetch raw `.ts` files from GitHub and parse them. Would give us their hand-curated tournament team data and tier rankings.
- **Verdict:** Potential next integration if we want tournament context that Limitless doesn't have. Not built yet.

### Smogon Forums Champions OU / BSS threads
- **Status:** Active community discussion threads, but unstructured prose. Not scrapeable into clean data.
- **Verdict:** Useful for human reading but not a programmatic data source.

### Pokemon Showdown ladder stats (Champions)
- **Status:** No Champions ladder on Showdown as of 2026-04-13. The actual game IS Pokemon Champions, so Showdown doesn't host a duplicate ladder.
- **Verdict:** N/A for Champions specifically. Adjacent VGC formats (gen9vgc2024) are tracked.

### Pokemon Champions in-game tournament system
- **Status:** Champions has its own in-game tournament system that hosts events like "Champions Cup" and "Alpenz Tour" referenced in third-party meta articles. **No public API or web interface to query results.**
- **Verdict:** Not queryable from outside the game.

## Lookups that have failed

- `pokemoncodex.fyi` — does not exist for Champions
- `vgcstats.com` — has Pokemon stats but not for Champions specifically
- Pikalytics for Paradox Pokemon — 404, not in their data set
- Limitless VGC `/api/tournaments` and `/tournaments.json` — both 404, no JSON API
