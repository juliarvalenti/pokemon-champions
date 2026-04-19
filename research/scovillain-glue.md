# Mega Scovillain Glue Archetype

*Added 2026-04-18. Breakout archetype — **Wolfey hit #1 on Champions ladder** with Mega Scovillain; Mauntra reached 1800+ ELO 20-4 with the reference list below. Expect heavy ladder representation going forward.*

## The Core Concept

**Mega Scovillain is a trap tank.** Its ability **Spicy Spray** burns any attacker that hits it with a damage-dealing move (that can be burned). Combined with **Rage Powder** redirection, it *forces* opponents to attack it — and punishes them for it with burn chip + Atk halving.

Why this matters right now: the most common physical attackers in the meta (Sneasler, Kingambit, Garchomp, Tyranitar, Excadrill, Basculegion, Talonflame) are all **burn-vulnerable**, and most of them take Scovillain down in 2 hits, not 1. That buys Scovillain's partners a free setup turn.

Scovillain doesn't sweep — its job is to **glue** a setup-heavy team together by absorbing the opponent's early-game pressure and burning their win cons. Setup sweepers behind it clean up.

## Reference List (Mauntra, 20-4 @ 1800+ ELO, Replica ID 6LDC1KR24W)

### Mega Scovillain @ Scovillainite — Calm nature
- **Ability:** Spicy Spray (post-mega)
- **Moves:** Flamethrower / Leech Seed / Rage Powder / Protect
- **SP:** HP 32 / Def 21 / SpDef 13
- **Role:** Trap tank. Click Rage Powder to redirect, Leech Seed for chip+heal, Flamethrower as your only real attack. Protect for stalling.

### Primarina @ Shell Bell — Modest nature (Liquid Voice)
- **Moves:** Hyper Voice / Moonblast / Calm Mind / Protect
- **SP:** HP 21 / Def 7 / SpAtk 32 / SpDef 2 / Spe 4
- **Role:** Setup sweeper. Liquid Voice makes Hyper Voice a Water move spread attack. Burns from Scovillain boost its SpDef matchup. Speed creep outpaces paralyzed Timid Mega Dragonite.

### Drampa @ Sitrus Berry — Quiet nature (Cloud Nine)
- **Moves:** Hyper Voice / Ice Beam / Earth Power / Protect
- **SP:** HP 31 / Def 3 / SpAtk 32
- **Role:** **The weather disabler.** Cloud Nine turns off active weather when it's on the field. Locks Charizard Y out of Solar Beam, turns off Archaludon's one-turn Electro Shot, kills Swift Swim/Chlorophyll boosts. Also a TR counter via low natural speed + coverage.

### Serperior @ Miracle Seed — Timid nature (Contrary)
- **Moves:** Leaf Storm / Glare / Taunt / Light Screen
- **SP:** HP 21 / Def 4 / SpAtk 5 / SpDef 4 / Spe 31
- **Role:** Screens + Taunt + Contrary Leaf Storm pop-off. The flex slot — Mauntra admits this is the least-brought mon and is still tuning it.

### Aegislash @ Spell Tag — Adamant nature (Stance Change)
- **Moves:** Shadow Claw / Iron Head / Shadow Sneak / King's Shield
- **SP:** HP 32 / Atk 32 / Spe 2
- **Role:** Physical Blade-form attacker. Primary Sneasler + Mega Floette answer. Shadow Claw over Poltergeist (miss chance + consumable items make Poltergeist inconsistent right now).

### Volcarona @ Leftovers — Modest nature (Flame Body)
- **Moves:** Fiery Dance / Giga Drain / Quiver Dance / Protect
- **SP:** HP 32 / Def 5 / SpAtk 5 / Spe 24
- **Role:** QD win con. Speed SP tuned to outspeed Scarf Basculegion after one Quiver Dance. Giga Drain hits rain cores. Scovillain's Rage Powder protects Volcarona's Quiver Dance setup turns.

## Defensive Cores

Two overlapping cores:
- **Fire-Water-Grass resist core:** Scovillain / Primarina / Volcarona — all three resist at least one of the others' weaknesses.
- **Steel-Dragon-Fairy resist core:** Aegislash / Drampa / Primarina — covers the non-FWG half of the type chart.

## Bulk Calcs (why Scovillain is a trap, not a chump)

From Mauntra's post — every common meta attacker is a **2HKO** on defensive-spread Mega Scovillain:

| Attacker | Move | Result |
|---|---|---|
| Sneasler (+Atk) | Dire Claw | 83.7-98.8% — 2HKO |
| Venusaur (+SpA) | Sludge Bomb | 77.9-91.8% — 2HKO |
| Charizard Y (+SpA) | Heat Wave (sun) | 57.5-68% — 2HKO |
| Charizard Y (+SpA) | Air Slash | 80.2-95.3% — 2HKO |
| Talonflame | Brave Bird | 83.7-98.8% — 2HKO |
| Basculegion (Adapt) | Wave Crash | 75.5-89.5% — 2HKO |
| Tyranitar | Rock Slide | 69.7-83.7% — 2HKO (w/ sand) |
| Pelipper (+SpA) | Hurricane | 83.7-98.8% — 2HKO |

**The 2HKO requirement means a Rage Powder draws both opponent attacks to Scovillain → free setup turn for partner + burns on both opponents.** This is the entire value proposition.

And Scovillain's partner (post-burn) has a 50% Atk reduction on the physical threats, making Volcarona/Primarina setup much safer:

- 252 Atk *burned* Garchomp Rock Slide vs. Volcarona = 44.7-53.1% (Leftovers stalls)
- 252 Atk *burned* Excadrill Rock Slide vs. Volcarona = 45.8-54.1%

## Gameplan

**Default lead:** Scovillain + setup sweeper (Primarina or Volcarona).
- T1: Scovillain Rage Powder. Opponent forced to attack Scovillain → burn proc. Sweeper uses Calm Mind / Quiver Dance free.
- T2: Scovillain Leech Seed or Flamethrower. Sweeper either boosts again or begins pressuring.
- T3+: Boosted sweeper sweeps under Scovillain's redirect cover.

**Alt lead vs weather cores:** Drampa + Scovillain.
- Drampa Cloud Nine disables sun/rain/sand. Scovillain redirects. Tempo swing favors Scovillain team.

**Late-game cleanup:** Aegislash Shadow Sneak priority + Volcarona Fiery Dance spam.

## What beats it

From Mauntra's own admission and the structure of the team:

1. **Rock Slide spam without Rage Powder control** — Aerodactyl Tailwind leads especially. 4x SE on Volcarona, 2x on Scovillain. If Scovillain dies before setting up, the team loses its glue.
2. **Talonflame + Helping Hand Acrobatics** — mentioned in comments as a known Scovillain killer (Flying 2x on Grass, boosted by HH, bypasses Rage Powder because it's a single-target spread setup).
3. **Taunt users at turn 1 speed** — Grimmsnarl Prankster Taunt, fast Talonflame Taunt. Shuts off Rage Powder + Leech Seed + Protect, forces Scovillain to Flamethrower only.
4. **Trick Room** — Scovillain is slow, but so is everything on the team. TR teams with their own bulk (Farigiraf, Hatterene) grind it out.
5. **Fire-immune attackers** (Heatran if legal, other Fire-types) — neutralize Scovillain's only attack.

## Implications for the Rain Team

**Biggest threats to our rain build from a Scovillain-glue team:**

- **Scovillain walls Basculegion Wave Crash** (neutral) AND burns Bascu on contact → Bascu's main move becomes a 50% Atk liability.
- **Scovillain walls Archaludon Electro Shot** (neutral, Grass/Fire is not Water-type so no rain synergy matters here).
- **Drampa Cloud Nine disables rain entirely** when it's on the field — same role Drampa plays vs sun.
- **Primarina Liquid Voice Hyper Voice** is a Water spread move that hits our Flying types (Pelipper, Mega Dnite) neutrally + Archaludon neutrally.

**Our answers:**

- **Mega Dragonite Hurricane** — 2x on Grass-type (neutral after Grass/Fire dual = 1x actually, since Flying is 2x Grass but 1x Fire = neutral). Hmm, actually Flying vs Grass/Fire is **2x * 1x = 2x** because Scovillain's Fire type doesn't resist Flying. **Hurricane is 2x on Scovillain.** 135 SpA + STAB + rain = real damage.
- **Mega Dragonite Ice Beam** — 2x on Grass-type = 2x on Scovillain. Repeatable.
- **Aegislash Shadow Ball** — 2x on the *Primarina-resist* types it pairs with, but neutral on Scovillain itself.
- **Incineroar** — Fire-type **immune to burn**, so Flare Blitz into Scovillain is safe. Fire vs Grass/Fire = 2x * 0.5x = neutral. Meh damage. Intimidate still valuable on the rest of the team.

**Lead guidance vs a Scovillain team:** **Pelipper + Mega Dragonite.** Rain up T1, Hurricane or Ice Beam into Scovillain T1. Do NOT lead with Bascu — it gets walled AND burned on contact.

**Bring-4 vs Scovillain teams:** Pelipper / Mega Dragonite / Incineroar / Archaludon. Bench Bascu and Aegislash. Archaludon Draco handles Drampa/Primarina, Dnite handles Scovillain+Volcarona.

## Sources

- Wolfey #1 ladder run (confirmed via r/PokemonChampions community references, 2026-04-17)
- Mauntra's writeup: https://www.reddit.com/r/PokemonChampions/comments/1sod9hn/
- eskaver's Mega Scovillain niche post: https://www.reddit.com/r/PokemonChampions/comments/1sah4q2/
- Dramatic-Year7046's burn-tank post: https://www.reddit.com/r/PokemonChampions/comments/1sj4zge/
