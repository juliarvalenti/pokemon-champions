---
name: damage-calc
description: Run Pokemon Champions damage calcs via the local NCP-VGC-Damage-Calculator wrapper. Use when Julia asks "does X KO Y?", "how much does this hit for?", "/calc ...", or any question whose answer requires a damage range / KO chance / specific roll.
argument-hint: "<attacker> <move> vs <defender> [conditions]"
allowed-tools: Bash(node scripts/calc.js*) Bash(node scripts/calc_tests.js*) Read Edit
---

# Damage Calculator

Julia is asking for a damage calculation. Build a JSON input, pipe it to `node scripts/calc.js`, parse the result, and respond with the damage range + KO chance + the most relevant takeaway.

The calc wraps `sim/ncp-calc/` (NCP-VGC-Damage-Calculator, the same calc JLuke and other content creators use), runs in jsdom headless, and is verified roll-by-roll against the live web calc.

---

## When to use

- "Does Mega Camerupt OHKO Incin?"
- "How hard does Sneasler CC hit Archaludon?"
- "If I get to +1 Bulk Up, does Body Press kill Garganacl?"
- "/calc <anything>"
- Any time the answer involves a specific damage number or KO percentage.

**Do NOT use** for questions that don't need a real number ("is X strong?", "what does Y do?"). Use `scout_pokemon.py` or `fetch_pokemon.py` for those.

---

## How to invoke

```bash
echo '<JSON>' | node scripts/calc.js
```

Input JSON schema:

```json
{
  "attacker": {
    "name": "Camerupt-Mega",
    "ability": "Sheer Force",
    "item": "Cameruptite",
    "nature": "Modest",
    "sps": { "hp": 0, "at": 0, "df": 0, "sa": 32, "sd": 0, "sp": 0 },
    "boosts": { "sa": 1 },
    "status": "Healthy",
    "moves": ["Earth Power", "Heat Wave", "Eruption", "Protect"]
  },
  "defender": { ...same shape... },
  "field": {
    "format": "Doubles",
    "weather": "Sun",
    "terrain": "",
    "tailwind": [false, false]
  }
}
```

**Required fields:** `attacker.name`, `defender.name`, `attacker.moves` (≥1).
**Defaults:** ability/item from species default, nature `Hardy` (neutral), all SP 0, all boosts 0, status `Healthy`, format `Doubles`.

---

## Naming conventions (CRITICAL)

The calc accepts both Showdown and NCP-native naming for mega forms:
- `Camerupt-Mega` ✓  or  `Mega Camerupt` ✓
- `Charizard-Mega-Y` ✓  or  `Mega Charizard Y` ✓
- `Charizard-Mega-X` ✓  or  `Mega Charizard X` ✓

For regional forms / other variants, use the exact NCP name (the calc will suggest corrections via fuzzy match if you typo). Common ones:
- `Arcanine-Hisui`, `Rotom-Wash`, `Sinistcha-Masterpiece`, `Maushold-Four`, `Palafin-Hero`, `Meowstic-F`, `Ninetales-Alola`

---

## Champions-specific gotchas

1. **No Tera.** Don't include `tera_type` or set `isTerastalize` — Champions doesn't have it.
2. **SP not EVs.** Use `sps: { sa: 32 }` for max special attack investment. The calc converts internally (SP × 8 = EV equivalent at level 50, IV 31).
3. **66 SP total cap, 32 per stat.** The calc warns if you exceed.
4. **Items are restricted.** Life Orb, Choice Specs, Assault Vest, etc. are NOT in Champions — see CLAUDE.md item list. Calc warns if you use one not in the Champions list, but **doesn't fail** (the math may still apply the boost). If Julia's spread requires a missing item, suggest the closest legal alternative (Charcoal for Fire boost, etc.).
5. **Mega stones are required for mega forms.** `Camerupt-Mega` should hold `Cameruptite`, `Charizard-Mega-Y` holds `Charizardite Y`, etc.

---

## Reading the output

```json
{
  "attacker": { "name": "Mega Camerupt", "stats": {...}, "ability": "Sheer Force" },
  "defender": { "name": "Incineroar", "stats": {...}, "ability": "Intimidate" },
  "moves": [
    {
      "move": "Earth Power",
      "result": {
        "damage": [200, 204, 206, 210, 212, 212, 216, 218, 222, 224, 224, 228, 230, 234, 236],
        "description": "216+ SpA Sheer Force Mega Camerupt Earth Power vs. 202 HP / 143+ SpD Incineroar"
      }
    }
  ]
}
```

- **`damage`** is the 15-roll damage spread (NCP convention; not 16). Min/max = damage range. KO chance = (count of rolls ≥ defender HP) / 15.
- **`description`** is the calc's stat-attribution string. The format `216+ SpA` means computed stat 216 with positive nature; `32 HP / 20+ SpD` would mean SP-spread style. NCP uses the computed-stat style for description.
- **`note`** appears on results where damage is all-zero, explaining why (immunity, status move, etc.). E.g. `damage=0: Poison is 0× vs Steel/Dragon (immunity)`.

---

## Workflow

1. **Parse Julia's question** into attacker / defender / move(s) / conditions. If she gave a Showdown paste, use those exact stats. If she gave just a vibe ("max bulk Archaludon"), make reasonable assumptions and **state them** in the response.

2. **Look up team context** — if either mon is in `team/`, prefer her actual trained spread over a generic one. Read `team/roster.md` and the relevant team file.

3. **Build the JSON input** with sensible defaults. For "normal builds" of meta mons, use the canonical Pikalytics-top spread (max attacking stat + max speed + bulk dump for offensive mons; max HP + max relevant defense for walls).

4. **Run the calc:** `echo '<JSON>' | node scripts/calc.js`

5. **Translate the output** into a human answer:
   - Lead with the **damage range and KO%**.
   - Note any silent immunities or `note` fields.
   - If the result is surprising (mon walls something unexpectedly, or one-shots through bulk), flag it explicitly.
   - Include the calc description so Julia can spot-check on the live calc if she wants.

6. **Suggest alternatives if relevant.** "Doesn't OHKO at +0, but +1 Bulk Up does — want me to run that?"

---

## Output style

Be punchy. Damage calcs are usually a quick yes/no on a specific question. Lead with the answer.

> **No 1HKO** — Mega Camerupt Modest 32 SpA Earth Power vs Incineroar 32/20+ SpD Sitrus = 200-236 (99-117%), **93% chance to OHKO** but the Sitrus proc means you need rolls ≥ 152 to actually KO through it.
>
> *Calc: 216+ SpA Sheer Force Mega Camerupt Earth Power vs. 202 HP / 143+ SpD Incineroar*

If asked for multi-move comparison, table format:

> Sneasler max-Atk Jolly into max-bulk Impish Archaludon (197 HP / 200+ Def / Stamina):
>
> | Move | Damage | % HP | Notes |
> |---|---|---|---|
> | Close Combat | 128–150 | 65–76% | 2HKO; -1 def/spd self-debuff afterward |
> | Throat Chop | 29–34 | 15–17% | Dark resisted by Steel |
> | Dire Claw | 0 | 0% | Steel immune to Poison |
>
> **Bottom line:** Archaludon completely walls Sneasler. CC is a 2HKO at best, and Stamina raises Def each hit so the second CC does even less. Don't lead Sneasler into known Archaludon.

---

## Sanity-check the calc itself

If results feel off, run the test suite to verify the calc isn't broken:

```bash
node scripts/calc_tests.js
```

5/5 tests pass on a healthy install. If they don't, the NCP submodule may have changed shape — investigate before trusting calc output.

---

## Common pitfalls

- **Forgetting the mega stone item.** `Camerupt-Mega` without `Cameruptite` still computes correctly because the species data already has the mega stats — but the description won't show the item, and any item-dependent calc (e.g. Mystic Water boost) won't apply. Default to including the mega stone.
- **Confusing SP and EV.** Champions input is **SP** (0-32 per stat, 66 total). Don't accidentally pass 252.
- **Defender bulk assumptions.** "Balanced bulk" can mean different things to different builders. If Julia doesn't specify, default to max HP + invested defense matching the move category, but state the assumption.
- **Intimidate not active.** The calc applies abilities at calc-time but doesn't model "switched in last turn." If a calc should be at -1 Atk from Intimidate, set `boosts: { at: -1 }` on the attacker explicitly.
- **Sitrus / type-resist berry timing.** The calc applies these as if "active before the hit." For "does X 2HKO through Sitrus?" math, you have to compute manually: damage1 → mon at HP - damage1 → if ≤ 50%, +25% HP from Sitrus → damage2 vs new HP.
