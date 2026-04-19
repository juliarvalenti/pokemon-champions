---
name: gacha
description: Handle new Pokemon Champions gacha pulls. Single mon → add to roster bench with brief context. Multiple mons → ranked meta analysis comparing them. Use when Julia says "I pulled X", "/gacha X", "gacha X / Y / Z", or references a gacha pool.
argument-hint: "<Pokemon> [Pokemon2 Pokemon3 ...]"
allowed-tools: Bash(python3 scripts/*) Read Edit Grep
---

# Gacha Handler

Julia is doing Pokemon Champions gacha pulls. Parse `$ARGUMENTS` into Pokemon names (split on whitespace and commas, normalize capitalization to match Pikalytics naming — e.g. `Rotom-Wash`, `Arcanine-Hisui`, `Flutter-Mane`).

**Branch on count:** 1 mon → add to roster. 2+ mons → ranked meta analysis.

---

## Branch 1: Single Pokemon (just add it, no analysis)

Julia pulled one mon and wants it added. **Do not do meta analysis. Do not fetch Pikalytics. Do not read research files.** Just add and confirm.

**Steps:**

1. **Check if already owned** — grep `team/roster.md` for the Pokemon name. If present, tell her it's already there and stop.

2. **Check the wishlist** — grep ONLY the "Recruit Wishlist" section of `team/roster.md` for the name. If it's there, mention it in one short sentence ("**wishlist priority #N**"). If not, don't say anything about priority.

3. **Add to roster** — Edit `team/roster.md`. Append the Pokemon name to the end of the "Bench pool (untrained, no current build plan)" comma-separated line. Don't create a named entry.

4. **Respond in ONE sentence.** Format: "Added X to the bench." Optionally append "— wishlist priority #N" if step 2 matched. That's it. No moves, no abilities, no teammates, no archetype talk, no training advice.

**Example good responses:**

> Added Palafin to the bench.

> Added Sneasler to the bench — wishlist priority #1.

> Added Pidgeot to the bench.

**Bad responses (do NOT do this):**

> Added Pidgeot to the bench. Niche — not in tournament winner data, Pikalytics usage is very low. Not a priority train, but Mega Pidgeot with No Guard Hurricane is a fun cope pick. *(too much! single-mon mode is silent.)*

---

## Branch 2: Multiple Pokemon (pool analysis)

Julia is picking from a gacha pool. She wants a ranked opinionated recommendation with meta data AND a quick role/vibe-check on each mon.

**Steps:**

1. **Fetch raw usage data** — `python3 scripts/fetch_pokemon.py <Name1> <Name2> ...`. Gets Pikalytics usage numbers, items, abilities, teammates, sample teams. Note 404s as low-usage.

2. **Fetch scout reports** — `python3 scripts/scout_pokemon.py <Name1> <Name2> ...`. Gets typing, competitive role (attacker / support / setup sweeper), **4x weaknesses** (flagged with ⚠️), core moves with usage%, gameplan summary. This is the "how does this mon actually play in VGC?" read.

   Run both scripts in parallel. They're fast and give complementary data:
   - fetch_pokemon.py = raw numbers for ranking
   - scout_pokemon.py = role/vibe-check for understanding

3. **Read roster context** — Read `team/roster.md` to know what she already owns, what's on the wishlist, and what archetypes she's building.

4. **Read meta context** — Read `research/meta-snapshot.md` for current tier list and tournament winner data. Read `research/core-pairs.md` if any of the pool mons are known to pair with something she already has.

5. **Rank each mon** on:
   - **Wishlist match** — is it a current wishlist target? (biggest signal)
   - **Tournament winner presence** — appears in winner data?
   - **Core pair activation** — does it unlock a core with a mon she has?
   - **Archetype activation** — does it enable a new viable archetype (sand, rain, stall, etc)?
   - **Pikalytics usage** — ladder presence (weaker signal than tournament data — see the meta-snapshot caveat)
   - **Already owned? → check duplicate value, don't auto-exclude.** Duplicates ARE allowed in Champions (one mon = one moveset; a duplicate is a second individual that can be trained with a different moveset). When a pool mon is already owned, don't silently drop it — evaluate whether a duplicate would enable a team configuration the current copy can't support. Examples:
     - **Current Gengar** is trained as sun-team special attacker (Shadow Ball / Sludge Bomb / Dazzling Gleam / Protect). A second Gengar enables the Mega Gengar Shadow Tag Perish trap archetype (needs Perish Song in its set) without re-skilling the first.
     - **Current Whimsicott** runs Moonblast / Encore / Tailwind / Protect. A second Whimsicott could run a different support set (e.g. Fake Tears / Helping Hand for a Trick Room supporter) without re-skilling.
     - **Current Conkeldurr** runs Iron Fist Drain Punch. A second could run Guts (for the "Burn Bull" team) if that comp needs a different ability setup.
   - If a duplicate has no alternate-team value (e.g., the current trained moveset is already "flexible enough" for every archetype she's building), THEN downrank or skip it.
   - **Never** just say "already owned — skip" without checking if a duplicate unlocks something new.

6. **Check item/ability availability** — if a mon's best build requires an item that doesn't exist in Champions (Life Orb, Flame Orb, Choice Specs, etc. — see `CLAUDE.md` items list), flag it.

7. **Give an opinionated ranked recommendation** with:
   - A one-sentence **role summary** per mon (from the scout report) so Julia understands the vibe at a glance
   - **ONE top choice** committed to and explained. Don't hedge across multiple "equally good" picks.
   - A short ranked list for context

**Output style:**

Keep it scannable. Julia is likely on mobile mid-gacha. Lead with the top pick, then give a ranked list with a one-line role summary per mon.

> **Top pick: Sneasler.** 89% tournament winner usage, you don't have it, activates the #1 gap in your roster.
>
> **Full ranking:**
> - 🥇 **Sneasler** — *Fighting/Poison fast support attacker. Fake Out / Close Combat / Dire Claw status spreader, Unburden doubles speed post-item.* Wishlist #1, tournament auto-include.
> - 🥈 **Farigiraf** — *Normal/Psychic bulky TR setter. Armor Tail blocks Fake Out priority, Foul Play off defensive ally.* Direct upgrade for your TR team's Fake Out problem.
> - 🥉 **Cresselia** — *Psychic bulky support. Lunar Dance revives ally, Calm Mind setup option.* Stall enabler for future builds.
> - 🚫 Skip: Furret (no role), Luvdisc (no), Dunsparce (cope)

---

## Key principles

- **Respect her bracket.** Julia plays casually. If she says "I like X", weight that. Don't push top-cut meta over personal preference.
- **Check ownership before recommending.** Grep `team/roster.md` first. If owned, evaluate duplicate value — don't auto-exclude.
- **Wishlist beats raw data.** If a pool mon is on the current wishlist, that's almost always the pick.
- **Flag Champions item caveats.** If a mon's Pikalytics build is full of items that don't exist in Champions, mention it (user may otherwise build something that can't actually exist).
- **Duplicates have value when they unlock a different trained moveset.** Each individual mon has one moveset. If Julia wants a species in two teams with incompatible movesets, a duplicate avoids re-skilling the original. This is ESPECIALLY true for: Gengar (sun attacker vs Mega trap), Whimsicott (offensive vs defensive support), Conkeldurr (Iron Fist vs Guts), and any mon with a clear "role divergence" between archetypes.
- **Be brief.** Short responses win. Julia is mid-gacha on mobile.
- **Tournament data > Pikalytics data** when they disagree. Tournament winners are the better meta signal; see the caveat in `research/meta-snapshot.md`.
