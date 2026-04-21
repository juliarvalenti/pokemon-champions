#!/usr/bin/env python3
"""Interactive type-chart trainer.

Picks a random Champions-legal attacker + move vs a random defender, asks Julia
for the effectiveness multiplier, grades the answer, and logs every attempt to
`data/type_quiz_log.jsonl` for later analysis.

Run: python3 scripts/type_trainer.py

Keybinds (single keypress, no Enter):
  q=4x   w=2x   e=1x   r=0.5x   t=0.25x   y=0x
  x / Esc / Ctrl+C = quit
"""
from __future__ import annotations

import json
import random
import sys
import termios
import tty
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
LOG_PATH = ROOT / "data" / "type_quiz_log.jsonl"
MNEMONICS_PATH = ROOT / "data" / "type_mnemonics.json"
ASYM_MNEMONICS_PATH = ROOT / "data" / "type_mnemonics_asymmetries.json"


def _load_mnemonics(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return {k: v for k, v in json.load(path.open()).items() if not k.startswith("_")}


BASE_MNEMONICS = _load_mnemonics(MNEMONICS_PATH)
ASYM_MNEMONICS = _load_mnemonics(ASYM_MNEMONICS_PATH)
# Asymmetry callouts take precedence over the base mnemonic for the same pair.
MNEMONICS = {**BASE_MNEMONICS, **ASYM_MNEMONICS}

TYPE_COLORS = {
    "normal": "white", "fire": "red", "water": "blue", "electric": "yellow",
    "grass": "green", "ice": "cyan", "fighting": "red3", "poison": "magenta",
    "ground": "yellow3", "flying": "bright_cyan", "psychic": "bright_magenta",
    "bug": "green3", "rock": "orange3", "ghost": "purple", "dragon": "blue3",
    "dark": "grey35", "steel": "grey70", "fairy": "bright_magenta",
}

# Standard 18-type chart. TYPE_CHART[atk][def] = multiplier.
# 0 = immune, 0.5 = resist, 1 = neutral, 2 = weak.
_T = ["normal","fire","water","electric","grass","ice","fighting","poison",
      "ground","flying","psychic","bug","rock","ghost","dragon","dark","steel","fairy"]
# Rows are attacker, columns are defender (same order as _T).
_CHART_ROWS = {
    "normal":   [1,1,1,1,1,1,1,1,1,1,1,1,0.5,0,1,1,0.5,1],
    "fire":     [1,0.5,0.5,1,2,2,1,1,1,1,1,2,0.5,1,0.5,1,2,1],
    "water":    [1,2,0.5,1,0.5,1,1,1,2,1,1,1,2,1,0.5,1,1,1],
    "electric": [1,1,2,0.5,0.5,1,1,1,0,2,1,1,1,1,0.5,1,1,1],
    "grass":    [1,0.5,2,1,0.5,1,1,0.5,2,0.5,1,0.5,2,1,0.5,1,0.5,1],
    "ice":      [1,0.5,0.5,1,2,0.5,1,1,2,2,1,1,1,1,2,1,0.5,1],
    "fighting": [2,1,1,1,1,2,1,0.5,1,0.5,0.5,0.5,2,0,1,2,2,0.5],
    "poison":   [1,1,1,1,2,1,1,0.5,0.5,1,1,1,0.5,0.5,1,1,0,2],
    "ground":   [1,2,1,2,0.5,1,1,2,1,0,1,0.5,2,1,1,1,2,1],
    "flying":   [1,1,1,0.5,2,1,2,1,1,1,1,2,0.5,1,1,1,0.5,1],
    "psychic":  [1,1,1,1,1,1,2,2,1,1,0.5,1,1,1,1,0,0.5,1],
    "bug":      [1,0.5,1,1,2,1,0.5,0.5,1,0.5,2,1,1,0.5,1,2,0.5,0.5],
    "rock":     [1,2,1,1,1,2,0.5,1,0.5,2,1,2,1,1,1,1,0.5,1],
    "ghost":    [0,1,1,1,1,1,1,1,1,1,2,1,1,2,1,0.5,1,1],
    "dragon":   [1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,0.5,0],
    "dark":     [1,1,1,1,1,1,0.5,1,1,1,2,1,1,2,1,0.5,1,0.5],
    "steel":    [1,0.5,0.5,0.5,1,2,1,1,1,1,1,1,2,1,1,1,0.5,2],
    "fairy":    [1,0.5,1,1,1,1,2,0.5,1,1,1,1,1,1,2,2,0.5,1],
}
TYPE_CHART = {atk: dict(zip(_T, row)) for atk, row in _CHART_ROWS.items()}


def is_asymmetric(atk: str, defn: str) -> bool:
    """True if atk→def effectiveness differs from def→atk."""
    return TYPE_CHART[atk][defn] != TYPE_CHART[defn][atk]


def load_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def build_pool() -> tuple[list[dict], dict[str, dict]]:
    """Return (quiz_pool, moves_by_name).

    Pool = mons that exist in BOTH the Champions movepool cache and the
    stats cache (so we have both types and a legal movelist).
    """
    pokemon = {p["name"]: p for p in load_jsonl(CACHE / "pokemon.jsonl")}
    movepools = {m["name"]: m for m in load_jsonl(CACHE / "champions_movepools.jsonl")}
    moves = {m["name"]: m for m in load_jsonl(CACHE / "moves.jsonl")}

    pool = []
    for name, mp in movepools.items():
        if name not in pokemon:
            continue
        damaging = [
            mn for mn in mp["moves"]
            if (m := moves.get(mn)) and m.get("power") and m.get("damage_class") in ("physical", "special")
        ]
        if not damaging:
            continue
        pool.append({"name": name, "types": pokemon[name]["types"], "damaging_moves": damaging})
    return pool, moves


def effectiveness(move_type: str, defender_types: list[str]) -> tuple[float, list[float]]:
    per_type = [TYPE_CHART[move_type][dt] for dt in defender_types]
    mult = 1.0
    for m in per_type:
        mult *= m
    return mult, per_type


KEY_ANSWERS = {"q": 4.0, "w": 2.0, "e": 1.0, "r": 0.5, "t": 0.25, "y": 0.0}
QUIT_KEYS = {"x", "\x1b", "\x03", "\x04"}  # x, Esc, Ctrl+C, Ctrl+D


def read_key() -> str:
    """Read a single keypress from stdin in raw mode (falls back to line input)."""
    if not sys.stdin.isatty():
        line = sys.stdin.readline()
        return line[:1] if line else "\x04"
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def fmt_mult(m: float) -> str:
    if m == 0: return "0x"
    if m == 0.25: return "0.25x"
    if m == 0.5: return "0.5x"
    if m == 1: return "1x"
    if m == 2: return "2x"
    if m == 4: return "4x"
    return f"{m}x"


def color_for_mult(m: float) -> str:
    if m == 0: return "grey50"
    if m < 1: return "yellow"
    if m == 1: return "white"
    if m == 2: return "green"
    return "bright_green bold"


def type_chip(t: str) -> Text:
    return Text(f" {t.upper()} ", style=f"black on {TYPE_COLORS.get(t, 'white')}")


def titlecase_name(n: str) -> str:
    return "-".join(p.capitalize() for p in n.split("-"))


def run_round(console: Console, pool: list[dict], moves: dict[str, dict]) -> dict | None:
    attacker = random.choice(pool)
    defender = random.choice(pool)
    move_name = random.choice(attacker["damaging_moves"])
    move = moves[move_name]
    move_type = move["type"]

    # Render prompt panel.
    header = Text()
    header.append(titlecase_name(attacker["name"]), style="bold")
    header.append(" uses ")
    header.append(move_name.replace("-", " ").title(), style="bold")
    header.append(" (")
    header.append_text(type_chip(move_type))
    header.append(")  vs  ")
    header.append(titlecase_name(defender["name"]), style="bold")
    header.append("  ")
    for i, dt in enumerate(defender["types"]):
        if i: header.append(" ")
        header.append_text(type_chip(dt))
    console.print(Panel(header, border_style="cyan"))

    console.print(
        "[dim]q=4x  w=2x  e=1x  r=0.5x  t=0.25x  y=0x   ·   x/Esc=quit[/dim]"
    )
    while True:
        ch = read_key().lower()
        if ch in QUIT_KEYS:
            return None
        if ch in KEY_ANSWERS:
            user_answer = KEY_ANSWERS[ch]
            console.print(f"[bold]→ {fmt_mult(user_answer)}[/bold]")
            break
        # ignore anything else and keep waiting
    actual, per_type = effectiveness(move_type, defender["types"])
    correct = user_answer == actual

    # Verdict.
    verdict = Text()
    if correct:
        verdict.append("✓ correct", style="bold green")
    else:
        verdict.append("✗ wrong", style="bold red")
        verdict.append(f"  — you said {fmt_mult(user_answer)}, actual ")
        verdict.append(fmt_mult(actual), style=color_for_mult(actual) + " bold")
    console.print(verdict)

    # Breakdown table.
    table = Table(show_header=False, box=None, pad_edge=False)
    for dt, m in zip(defender["types"], per_type):
        table.add_row(
            type_chip(move_type),
            Text("→"),
            type_chip(dt),
            Text(f" {fmt_mult(m)}", style=color_for_mult(m)),
        )
    table.add_row(Text(""), Text(""), Text("total", style="dim"),
                  Text(f" {fmt_mult(actual)}", style=color_for_mult(actual) + " bold"))
    console.print(table)

    for dt, m in zip(defender["types"], per_type):
        if m == 1:
            continue
        note = MNEMONICS.get(f"{move_type}>{dt}")
        if note:
            tag = ""
            if is_asymmetric(move_type, dt):
                reverse = fmt_mult(TYPE_CHART[dt][move_type])
                tag = f" [yellow]⚖ asymmetric — reverse {dt}→{move_type} is {reverse}[/yellow]"
            console.print(f"  [dim]{move_type} → {dt}:[/dim] {note}{tag}")
    console.print()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attacker": attacker["name"],
        "attacker_types": attacker["types"],
        "move": move_name,
        "move_type": move_type,
        "defender": defender["name"],
        "defender_types": defender["types"],
        "user_answer": user_answer,
        "correct_answer": actual,
        "per_type_multipliers": per_type,
        "correct": correct,
    }


def main() -> int:
    console = Console()
    pool, moves = build_pool()
    LOG_PATH.parent.mkdir(exist_ok=True)

    console.print(Panel.fit(
        Text.from_markup(
            "[bold]Type Chart Trainer[/bold]\n"
            f"[dim]{len(pool)} Champions-legal mons in pool · logging to {LOG_PATH.relative_to(ROOT)}[/dim]\n"
            "[bold]q[/]=0x  [bold]w[/]=0.25x  [bold]e[/]=0.5x  [bold]r[/]=1x  [bold]t[/]=2x  [bold]y[/]=4x   ·   [bold]x[/]/Esc to quit"
        ),
        border_style="magenta",
    ))

    session_correct = 0
    session_total = 0
    try:
        with LOG_PATH.open("a") as log:
            while True:
                entry = run_round(console, pool, moves)
                if entry is None:
                    break
                if entry:
                    log.write(json.dumps(entry) + "\n")
                    log.flush()
                    session_total += 1
                    session_correct += int(entry["correct"])
    except (KeyboardInterrupt, EOFError):
        console.print()

    if session_total:
        pct = 100 * session_correct / session_total
        console.print(
            f"[bold]Session:[/bold] {session_correct}/{session_total} "
            f"([{'green' if pct >= 80 else 'yellow' if pct >= 60 else 'red'}]{pct:.0f}%[/])"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
