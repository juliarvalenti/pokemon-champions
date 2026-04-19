# Meta Snapshot

*Last updated: 2026-04-13 (verified against Pikalytics championspreview AND Limitless TCG winner data from 9 recent Champions tournaments ≥50p). Pokemon Champions launched 2026-04-08 — the meta is brand new and shifts fast. Re-fetch with `python3 scripts/fetch_meta.py` and `python3 scripts/fetch_limitless_list.py` if more than ~1 week old.*

## Rising Archetype (2026-04-18 update)

**Mega Scovillain glue teams** — Wolfey hit #1 on ladder with Mega Scovillain; Mauntra reached 1800+ ELO 20-4. Spicy Spray burns contact attackers, Rage Powder forces targeting, bulky spread tanks 2HKOs from most meta attackers. Full writeup with reference list in [`scovillain-glue.md`](scovillain-glue.md). Expect heavy ladder representation.

## Current Top 16 (Pikalytics championspreview)

| Rank | Pokemon | Usage |
|------|---------|-------|
| 1 | Incineroar | 48.3% |
| 2 | Sneasler | 29.1% |
| 3 | Sinistcha | 26.8% |
| 4 | Archaludon | 23.7% |
| 5 | Whimsicott | 21.6% |
| 6 | Pelipper | 19.3% |
| 7 | Garchomp | 18.8% |
| 8 | Farigiraf | 17.9% |
| 9 | Dragonite | 16.1% |
| 10 | Charizard | 15.3% |
| 11 | Basculegion | 15.1% |
| 12 | Tyranitar | 15.0% |
| 13 | Kingambit | 13.2% |
| 14 | Gengar | 12.0% |
| 15 | Metagross | 10.8% |
| 16 | Froslass | 10.7% |

## Important: Paradox Pokemon Caveat

**Paradox Pokemon (Flutter Mane, Iron Hands, Iron Treads, etc.) are NOT in Pikalytics' Champions Preview data.** They may not be in the legal 147-mon Champions roster at all. External meta articles (e.g. Solemn PKM's coverage) sometimes mention Fluttermane as dominant, but this cannot be verified against Pikalytics. If the user references Paradox mons, flag the uncertainty rather than pretending they exist in Champions.

## Tournament Winner Data (9 Champions tournaments, top 1 each, 2026-04-11 to 04-13)

Sniff test of 9 winners across tournaments with ≥50 players. **Critical for understanding the meta because Pikalytics ladder data and tournament top-cut data don't always agree.**

| Pokemon | % of winners | Pikalytics | Notes |
|---------|--------------|------------|-------|
| **Sneasler** | **89% (8/9)** | 29.1% | THE keystone non-mega. Massively underrepresented in Pikalytics vs tournament play. |
| **Kingambit** | **56% (5/9)** | 13.2% | Sucker Punch + Defiant. Punishes Intimidate. Underrepresented in Pikalytics. |
| Mega Floette | 33% (3/9) | n/a | Confirmed format-defining via tournament wins |
| Garchomp | 33% (3/9) | 18.8% | |
| Wash Rotom | 33% (3/9) | 9.0% | Top players use Rotom for utility instead of Incineroar |
| Basculegion | 33% (3/9) | 15.1% | Confirmed back, with rain or scarf |
| **Incineroar** | **33% (3/9)** | **48.3%** | **Surprise: less common than Pikalytics suggests.** Top players replace it with Heat/Wash Rotom. Don't assume every team has it. |
| Mega Charizard Y | 22% (2/9) | 15.3% | Sun is still winning despite "skepticism" articles |

**Megas that won at least one tournament:** Charizard Y (×2), Floette, Froslass, Gengar (Shadow Tag Perish trap!), Delphox, Meganium, Starmie (Huge Power physical), Victreebel (Innards Out + Chlorophyll).

## Current Tier List

### S Tier (format-defining)

- **Sneasler** (89% of tournament winners, 29.1% Pikalytics) — Fighting/Poison fast attacker, Unburden ability, runs Fake Out / Close Combat / Dire Claw / Protect. Effectively required on competitive teams. **The most underweighted mon in Pikalytics data.**
- **Mega Floette** — Calm Mind sweeper, Fairy Aura. Won multiple tournaments. Hard to stop without Steel coverage.
- **Mega Charizard Y** — sun setter, Heat Wave nuke, ~71% of Charizards run Charizardite Y. Multiple tournament wins confirm it's still top-tier despite "decline" articles.

### A Tier (top picks, on most teams)

- **Incineroar** (33% of winners, 48.3% Pikalytics) — Fake Out + Intimidate + Parting Shot. Pikalytics overweights this; top players sometimes swap for utility Rotom forms instead. Still strong, just not auto-include.
- **Kingambit** (56% of winners, 13.2% Pikalytics) — Sucker Punch priority, Defiant punishes Intimidate, runs Black Glasses for damage boost. **Significantly underweighted in Pikalytics.**
- **Sinistcha** (26.8% Pikalytics) — Grass/Ghost support, Rage Powder redirection, Strength Sap recovery
- **Archaludon** (23.7%) — Steel/Dragon special attacker, Stamina ability for rain teams
- **Whimsicott** (21.6%) — Prankster Tailwind, the most popular speed control in the format
- **Pelipper** (19.3%) — Drizzle setter, enables rain teams (with Basculegion, Archaludon)
- **Garchomp** (18.8%) — physical EQ + Rock Slide spread. Pairs with Levitate/Flying partners for safe EQ spam.
- **Farigiraf** (17.9%) — top Trick Room setter, Armor Tail blocks priority
- **Dragonite** (16.1%) — Multiscale + Extreme Speed priority, Choice Scarf or bulky variants
- **Chlorophyll Venusaur** — sun abuser, Sleep Powder, doubled speed in sun. 87% of Venusaurs are on Charizard teams. Do NOT Mega — Mega Venusaur loses Chlorophyll for Thick Fat (only 4.3% usage).
- **Basculegion** (15.1%) — Adaptability Wave Crash + Last Respects, rain team staple. Recently rising as Charizard Y skepticism grows.
- **Tyranitar** (15.0%) — Sand Stream, special tank
- **Kingambit** (13.2%) — Sucker Punch priority, Defiant punishes Intimidate

### Rising / Trending

- **Aerodactyl** — cemented as the dominant Tailwind setter. Dual Wingbeat breaks Sash, Rock Slide STAB pressures Charizard, Wide Guard utility. ~6% Pikalytics usage but on most top-cut teams.
- **Mega Froslass + Iron Hands balance** — emerging archetype per external meta coverage. Pairs with Fire/Water/Grass cores. *Note: Iron Hands is a Paradox and not verified in Pikalytics championspreview data.*
- **Basculegion** — back on top after period of decline, per recent meta coverage. Charizard Y skepticism freed up its full kit.
- **Aegislash** — one of the few quality Steels that walls Fairy setup sweepers. Wide Guard blocks EQ spam.
- **Rotom-Wash** (9.0%) — Will-O-Wisp, Levitate (Earthquake immune), Volt Switch pivoting.
- **Corviknight** (7.7%) — Pressure, Bulk Up, U-turn pivot, stall enabler.

### Frauds (don't be fooled by visibility)

- **Kangaskhan** — Power Up Punch was removed in Champions, gutting the standard build. The top 3 non-megas (Incineroar, Sinistcha, Sneasler) all counter it.

### Where is Trick Room?

**0 of 9 recent tournament winners ran a TR team.** The closest competitive TR finish was winton (7th place, Pokemon Champions Challenge #1) running Mimikyu / Hatterene / Torkoal / Golurk / Drampa / Farigiraf — a sun room build. Hatterene is at 10.7% Pikalytics usage but Trick Room as a move is rarely her top pick in her actual builds. Farigiraf is the highest-tracked TR setter at ~18% usage but most of those teams are running it as a defensive pivot with **Armor Tail (blocks priority moves like Fake Out)**, not a TR enabler.

**The "sun room" candidate:** Torkoal Drought + slow attackers under TR. Ferrothorn / Farigiraf / Venusaur / Incineroar are the natural pieces.

**Implication for team building:** A well-built TR team has high surprise factor in Champions right now. Opponents won't have practice playing into it. Farigiraf with Armor Tail is the most overlooked piece — it's the only Champions Pokemon that natively blocks Fake Out priority, which solves the biggest TR setup problem.

### Sneasler is the recruit-priority lesson

The single biggest takeaway from comparing Pikalytics to tournament data: **Sneasler's true tournament rate is 89%, vs 29% in ladder data.** When recommending recruit priorities, weight tournament winners over Pikalytics ladder usage — Pikalytics undercounts the meta picks because casual players don't always have access to top-tier mons. Tournament top-cut data is the better signal for "what wins."

## Dominant Strategies

### Earthquake + Flying/Levitate Partner
The single biggest pattern in the meta. One mon clicks Earthquake every turn while the partner floats above it.
- **Garchomp + Aerodactyl** (Tailwind + EQ spam)
- **Garchomp + Talonflame** (same idea)
- **Garchomp + Delphox** (Levitate, Heat Wave coverage)
- **Garchomp + Rotom-Wash/Heat** (Levitate, Discharge + EQ)

### Sun Offense
- **Mega Charizard Y + Chlorophyll Venusaur**, plus Incineroar / Whimsicott / Garchomp filler. Heat Wave spread + Sleep Powder + 1-turn Solar Beam.

### Floette Calm Mind Sweep
- Mega Floette behind Maushold (Friend Guard) sets up Calm Mind and sweeps with Moonblast. Hard to stop without dedicated Steel coverage.

### Sand (Tyranitar + Excadrill)
- Highest co-occurrence in the format (93.7%). Sand Stream + Sand Rush = ~176 effective speed Excadrill in sand. Excadrill is THE comp.

## Threats Your Team Should Have Answers For

| Threat | Why dangerous | Common counters |
|--------|--------------|-----------------|
| **Sneasler** | 89% of tournament winners run it. Fake Out + Close Combat + Dire Claw status. Unburden doubles speed after item is consumed. | Psychic types (4x Psychic on Fighting/Poison) — Hatterene, Reuniclus, Mega Floette |
| **Mega Floette** | Calm Mind sweeper, Fairy Aura, hard to OHKO | Steel types (Aegislash, Aggron, Kingambit), priority moves |
| **Kingambit Sucker Punch** | Priority Dark damage, Defiant punishes Intimidate switch-ins | Fighting moves (Conkeldurr Drain Punch 4x), don't click status the turn it's in |
| **Aerodactyl Rock Slide** | Fastest mon, spread Rock STAB with flinch | Wide Guard (Aegislash), Rock resists, Ice Punch (Conkeldurr 4x) |
| **Garchomp Earthquake** | Spread move, brutal damage | Flying/Levitate teammates, Wide Guard, Ice Punch (4x) |
| **Pelipper rain teams** | Rain doubles Water damage and Swift Swim speed | Tyranitar (Sand cancels rain), Grass types |
| **Mega Charizard Y sun** | Heat Wave + 1-turn Solar Beam in sun | Tyranitar (Sand cancels sun), Rock types, fast water |

## Notes on Pikalytics Data

Pikalytics' "championspreview" data comes from Showdown/ladder and **may include items and abilities that are NOT yet available in the actual Pokemon Champions game.** Always cross-reference recommended items against the available items list in `CLAUDE.md`. Common items that appear in Pikalytics data but DON'T exist in Champions:

- Life Orb, Choice Band, Choice Specs, Assault Vest
- Rocky Helmet, Loaded Dice, Covert Cloak, Eject Button
- Safety Goggles, Clear Amulet, Throat Spray, Air Balloon
- Flame Orb, Mirror Herb, Heavy-Duty Boots
