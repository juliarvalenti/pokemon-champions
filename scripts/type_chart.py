#!/usr/bin/env python3
"""Interactive type effectiveness chart.

Move a row+column highlight around with WASD or arrow keys. The intersection
cell is the focused matchup; the status line shows ATK → DEF = multiplier.

Keys:
  w / ↑   move up (change attacker)
  s / ↓   move down
  a / ←   move left (change defender)
  d / →   move right
  q / Esc / Ctrl+C   quit

Rows are the attacker, columns the defender (pokemondb.net order).
"""
from __future__ import annotations

import select
import sys
import termios
import tty
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from type_trainer import (  # type: ignore[import-not-found]
    TYPE_CHART,
    TYPE_COLORS,
    MNEMONICS,
    fmt_mult,
    is_asymmetric,
    _T as TYPES,
)


CELL = {
    0:   ("0", "bright_red"),
    0.5: ("½", "red"),
    1:   ("·", "grey50"),
    2:   ("2", "green"),
}
LABEL = {0: "immune (0×)", 0.5: "resisted (½×)", 1: "neutral (1×)", 2: "super-effective (2×)"}
ABBR = {"fighting": "Fig", "psychic": "Psy"}

HL = "on grey19"          # row/column cross
FOCUS = "bold white on dodger_blue3"  # intersection


def abbr(t: str) -> str:
    return ABBR.get(t, t[:3].capitalize())


def read_key() -> str:
    """Single keypress; returns 'up'/'down'/'left'/'right'/'quit' or raw char."""
    if not sys.stdin.isatty():
        return "quit"
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            # Possible arrow sequence: ESC [ A/B/C/D. Peek with a tiny timeout.
            r, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not r:
                return "quit"
            seq = sys.stdin.read(2)
            return {"[A": "up", "[B": "down", "[C": "right", "[D": "left"}.get(seq, "quit")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if ch in ("\x03", "\x04", "q"):
        return "quit"
    return {"w": "up", "s": "down", "a": "left", "d": "right"}.get(ch, "")


def status_line(atk_i: int, def_i: int) -> Text:
    atk_sel, def_sel = TYPES[atk_i], TYPES[def_i]
    mult = TYPE_CHART[atk_sel][def_sel]
    t = Text(no_wrap=True, overflow="crop")
    t.append(atk_sel.capitalize(), style=f"bold {TYPE_COLORS[atk_sel]}")
    t.append(" → ")
    t.append(def_sel.capitalize(), style=f"bold {TYPE_COLORS[def_sel]}")
    t.append(f"  =  {LABEL[mult]}", style="bold")
    return t


def render(atk_i: int, def_i: int) -> Table:
    table = Table(
        show_lines=False,
        pad_edge=False,
        padding=(0, 0),
        box=None,
    )
    table.add_column("ATK\\DEF", justify="right", style="bold", no_wrap=True)
    for j, d in enumerate(TYPES):
        style = f"bold {TYPE_COLORS[d]}"
        if j == def_i:
            style += " on grey30"
        table.add_column(Text(abbr(d), style=style), justify="center", no_wrap=True, width=3)

    for i, atk in enumerate(TYPES):
        row_style = f"bold {TYPE_COLORS[atk]}"
        if i == atk_i:
            row_style += " on grey30"
        row = [Text(abbr(atk), style=row_style)]
        for j, d in enumerate(TYPES):
            glyph, color = CELL[TYPE_CHART[atk][d]]
            if i == atk_i and j == def_i:
                cell_style = FOCUS
            elif i == atk_i or j == def_i:
                cell_style = f"{color} {HL}"
            else:
                cell_style = color
            row.append(Text(f" {glyph} ", style=cell_style))
        table.add_row(*row)
    return table


FOOTER = (
    "[dim]wasd / arrows to move   q or Esc to quit   "
    "[green]2[/] super-effective  [red]½[/] resisted  "
    "[bright_red]0[/] immune  [grey50]·[/] neutral[/]"
)


def main() -> None:
    console = Console()
    atk_i = TYPES.index("fire")
    def_i = TYPES.index("water")
    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            while True:
                atk, defn = TYPES[atk_i], TYPES[def_i]
                renderable = Table.grid()
                renderable.add_row(status_line(atk_i, def_i))
                if is_asymmetric(atk, defn):
                    rev = fmt_mult(TYPE_CHART[defn][atk])
                    tag = Text.from_markup(
                        f"[yellow]⚖ asymmetric — reverse {defn}→{atk} is {rev}[/yellow]",
                        overflow="crop",
                    )
                    tag.no_wrap = True
                    renderable.add_row(tag)
                note = MNEMONICS.get(f"{atk}>{defn}", "")
                renderable.add_row(Text(note, style="italic grey70", no_wrap=True, overflow="crop"))
                renderable.add_row(Text(""))
                renderable.add_row(render(atk_i, def_i))
                renderable.add_row(Text(""))
                renderable.add_row(Text.from_markup(FOOTER))
                live.update(renderable, refresh=True)
                key = read_key()
                if key == "quit":
                    return
                elif key == "up":
                    atk_i = (atk_i - 1) % len(TYPES)
                elif key == "down":
                    atk_i = (atk_i + 1) % len(TYPES)
                elif key == "left":
                    def_i = (def_i - 1) % len(TYPES)
                elif key == "right":
                    def_i = (def_i + 1) % len(TYPES)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
