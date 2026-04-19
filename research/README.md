# Research

*Persistent meta knowledge for Pokemon Champions VGC. Read these before answering team-building questions to avoid re-deriving context every session.*

## Files

| File | What's in it |
|------|--------------|
| [`meta-snapshot.md`](meta-snapshot.md) | **Time-sensitive** — current tier list, broken mons, rising threats, frauds, dominant strategies. Has a date — check it before trusting. |
| [`archetypes.md`](archetypes.md) | **Durable** — team archetype templates (sun, sand, rain, TR, stall, hyper offense). Who sets it up, who abuses it, key pieces, weaknesses. |
| [`core-pairs.md`](core-pairs.md) | **Durable** — high-co-occurrence teammate pairs from usage data. Helps explain *why* certain mons want certain partners. |
| [`type-traits.md`](type-traits.md) | **Durable** — intrinsic type-based traits from in-game Champions reference (Fire can't burn, Dark immune to Prankster, Grass immune to Powder moves, etc). **Check this before recommending move interactions** — several silent immunities invalidate common plays. |
| [`scovillain-glue.md`](scovillain-glue.md) | **Archetype writeup (2026-04-18)** — Mega Scovillain trap-tank glue team. Wolfey #1 on ladder with it. Includes Mauntra's reference list (Scovillain / Primarina / Drampa / Serperior / Aegislash / Volcarona), bulk calcs, what beats it, and rain-team lead guidance vs it. |
| [`data-sources.md`](data-sources.md) | **Reference** — every external data source we've evaluated, what it gives us, what doesn't work, and what's not built yet. Read before suggesting "let's try X". |

## How to use this

- **Before recommending a team** — skim `archetypes.md` to make sure the archetype is well-formed and `meta-snapshot.md` to make sure the threats are addressed.
- **Before recommending a Pokemon pull** — check `meta-snapshot.md` to see if the mon is rising, falling, or a fraud, and `core-pairs.md` to see what synergies it activates.
- **When the meta snapshot is stale** — fetch fresh data with `python3 scripts/fetch_meta.py` and update the file with a new date.
