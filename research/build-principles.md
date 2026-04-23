# Build Principles

*How to design SP spreads, natures, and items around named benchmarks instead of pouring everything into max/max. Source material: JLuke VGC team-building breakdowns + general VGC theory adapted to Champions math.*

The thesis: **every stat point should be justified by a benchmark.** A "max HP / max Atk Adamant" spread is almost always wasteful — you're paying for stats you don't need to win specific interactions, and giving up stats that would have won others. Good builders pick a target ("always live timid Floette Moonblast", "OHKO max-def Kingambit", "underspeed no-investment Sinistcha by 1") and spend the minimum SP required to hit it, then redirect the leftovers.

This file is the *thinking framework*. For specific damage numbers, use a calc (external for now — see `research/data-sources.md` for status).

---

## Champions math constraints

Different from mainline, so old EV intuitions don't transfer cleanly:

- **66 SP total per mon, max 32 per stat.** No IVs. So the floor is "no investment" (base stat only) and the ceiling is "32 SP" — there's no hidden +31 IV inflating things.
- **Nature is ±10% to one stat / -10% to another.** Same as mainline. Neutral natures (Hardy, Docile, etc.) are wasted unless you specifically don't want either modifier.
- **No IVs means "min speed" is just base × 0.9 (minus nature).** You can't dump speed below base. Relevant for Trick Room mons: a base 35 mon with -speed nature sits at floor 31-ish, not the mainline 0-IV floor.
- **Items are part of the spread.** Sitrus / type-resist berries / Colbur / Roseli / Eviolite-style items effectively add bulk for free — bake them into the calc, not "polish on top."

---

## Speed benchmarks

Speed is almost never about "be fast" — it's about **out-speeding or under-speeding a specific mon by exactly 1 point**, then spending the rest elsewhere.

### Common creep targets (check fresh before trusting — meta drifts)

- **Incineroar** — most run 0, some run 1–6 SP for the mirror. Hitting 82–85 puts you above "lazy" Incin without committing to the speed-tie war.
- **Sinistcha** — common at no investment. Underspeeding it by 1 lets you Sunny-Day-or-Flare-Blitz it before it Matcha-Gotchas your partner.
- **Rotom-Wash** — base 86. Common creep at 107 (out-speeds max-Spe Dragapult under Tailwind) or 108 (out-speeds Jolly Scarf Basculegion under Tailwind). 109+ is creeping the creepers.
- **Scarf Adamant Garchomp** — fastest common scarfer-ish target at 217 effective. Out-speeding it under Tailwind is a real benchmark for Tailwind sweepers.
- **Jolly Scarf Basculegion** — 214 effective. Same story.

### Trick Room speed

Goal: be **slower than your TR partner**, but **faster than enemy mons that also want to be slow**. Min-speed nature, 0 SP is the default, but sometimes you need a *little* speed:

- JLuke's Camerupt example: base 20, 10 SP → 50 speed. Underspeeds Spiritomb (49 at -nature 0 SP) by 1, so Spiritomb sets Sunny Day before Camerupt clicks Eruption.
- The pattern: **identify the slowest thing on your team that needs to move first under TR**, then SP-creep it from below by exactly 1 on the partner that comes next.

### Tailwind speed

Tailwind doubles speed. So a 109-speed mon under Tailwind = 218, which out-speeds Scarf Adamant Chomp. Build sweepers to a *Tailwind-active* benchmark, not a raw one.

### Scarf math

Scarf = ×1.5. So Scarf Palafin-Hero (base 100, max-Spe Jolly) ≈ 350-ish, which is faster than every non-scarfer in the format and most other scarfers (Garchomp Adamant edges it). Pick the fastest scarfer you need to beat, then SP-tune to *just* clear it.

---

## Bulk benchmarks

The pattern: pick the **scariest realistic hit** the mon needs to survive, calc the minimum HP/Def/SpD that guarantees it (or pushes the roll to ≥75%), then redirect the rest.

### Common "must live" hits in current meta

- **Timid Mega Floette Moonblast** — the gold standard for special bulk benchmarks. JLuke's Spiritomb is HP-invested specifically to live this.
- **Timid Mega Gengar Shadow Ball** — Sinistcha and Chandelure both want to live this; Colbur Berry helps if Gengar is paired with a Dark-type partner clicking Sucker.
- **Adamant max-Atk Sneasler Close Combat** — the "fast frail mon that one-shots backline supports" benchmark. Phys-def Incin tuned to live this is a JLuke staple.
- **Garchomp Earthquake at -1** (Intimidate active) — defines "did Intimidate save me?" calcs for your switch-ins.
- **Kingambit Sucker Punch / Iron Head** — sturdy mons want to eat one and threaten back.

### Item-as-bulk

These items effectively reduce damage and should be calc'd as part of the bulk:

| Item | Effect | Use case |
|------|--------|----------|
| **Sitrus Berry** | +25% HP at ≤50% | Lets a mon eat a 2nd hit. Standard on Incin. |
| **Type-resist berries** (Roseli, Colbur, Yache, Occa, etc.) | -50% damage from a super-effective hit of that type, once | Cheap way to flip a roll. Roseli on Spiritomb to live Floette Moonblast; Colbur on Sinistcha to live a Dark cleave. |
| **Focus Sash** | Survive any hit at full HP | Glass cannon insurance. Wasted if anything chips you (sand, Fake Out flinch into priority, etc). |
| **Leftovers** | +6.25% HP/turn | Bulk amortized over turns. Best on mons that pivot or stall. |

### "Roll in your favor" vs "guaranteed"

A 100% live often costs 8+ extra SP over a 75% live. Decide which interaction you actually need to lock down. JLuke's Sneasler-CC Incin spread: he could've gone 100% live vs Adamant Sneasler but it would've cost the rest of his attack stat — instead he locked in Jolly (100%) and accepted "roll slightly in your favor" vs Adamant.

---

## Damage benchmarks

Symmetric to bulk: pick the **scariest realistic mon you need to one-shot** (or 2HKO), calc the minimum offensive investment, redirect the rest into bulk/speed.

### Common "must KO" targets

- **Specially defensive Incineroar** — 87.5% chance for Mega Camerupt Earth Power per JLuke. The "special wall pivot" benchmark.
- **Max-def Kingambit** — Palafin-Hero CC OHKO is a Palance staple. Justifies fully-invested attack.
- **Milotic** — common bulky water; Wood Hammer / Solar Beam / Thunderbolt OHKO benchmarks are common.
- **Basculegion** (no bulk) — Shadow Ball OHKO from Chandelure-tier special attackers.

### Setup KOs

For setup sweepers (Bulk Up Chesnaught, Nasty Plot Farigiraf, etc.), calc at +1 not +0. JLuke's Chesnaught: +1 Body Press OHKOs Incineroar, +1 attack Wood Hammer OHKOs Milotic — those two calcs justified the entire set.

---

## Worked example: how to read a "named" spread

A spread like **Spiritomb @ Roseli Berry, Sassy, 32 HP / 0 Atk / 12 Def / 0 SpA / 22 SpD / 0 Spe** isn't arbitrary. Each number is a benchmark:

- **32 HP + 22 SpD + Roseli** → live Moonblast from Mega Floette
- **Sassy nature, 0 Spe** → speed 49 (slowest possible Spiritomb), so Camerupt at 50 moves after it under TR
- **12 Def** → leftover, dumped into the most-likely-to-matter stat

When you see a competitive set, **always ask "what does each number lock in?"** If you can't justify a stat point, it's probably wasted and could be redirected.

---

## Workflow when building a new mon

1. **Role first.** What does this mon do? (Win condition / speed control / pivot / wall.)
2. **Speed benchmark.** Pick the *one* thing it needs to out-speed or under-speed. Cost it in SP.
3. **Bulk benchmark.** Pick the *one* hit it needs to survive. Cost it in HP/Def/SpD + item.
4. **Damage benchmark.** Pick the *one* KO it needs to land. Cost it in Atk/SpA + nature.
5. **Dump leftovers** into whichever of the above is most "swingy" — usually HP (always useful) or the offensive stat (better odds on rolls).
6. **Pick item *with* bulk in mind** — Roseli, Colbur, Sitrus often replace 8–16 SP of bulk for free.

If you can't name the benchmark, the spread isn't done. Max/max is a flag that the build hasn't been thought through.

---

## What this doesn't replace

- **A damage calculator.** Until we have `scripts/calc.py`, calcs need to happen externally (JLuke uses [Trainer Tower's](https://www.trainertower.com/) or similar). The benchmarks above are *patterns*; the actual numbers need a calc.
- **Knowledge of the current meta.** "Live Floette Moonblast" only matters if Floette is a top threat. Cross-reference `research/meta-snapshot.md` before locking in benchmarks.
- **Team-level planning.** This file is per-mon. For team composition (speed control / win condition / coverage), see `research/archetypes.md`.
