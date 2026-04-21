#!/usr/bin/env python3
"""Summarize `data/type_quiz_log.jsonl`.

Sections:
  1. Overall accuracy + recent trend (last 25 vs prior).
  2. Per-move-type accuracy (sorted worst → best, hides tiny samples).
  3. Most-missed specific matchups (move_type → defender type combo).
  4. Most common mistake patterns (user_answer vs correct_answer).

Run: python3 scripts/analyze_quiz.py
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

LOG = Path(__file__).resolve().parent.parent / "data" / "type_quiz_log.jsonl"


def fmt_mult(m: float) -> str:
    return {0: "0x", 0.25: "¼x", 0.5: "½x", 1: "1x", 2: "2x", 4: "4x"}.get(m, f"{m}x")


def pct(num: int, den: int) -> str:
    return f"{100*num/den:.0f}%" if den else "—"


def color_for_acc(acc: float) -> str:
    if acc >= 0.8: return "green"
    if acc >= 0.5: return "yellow"
    return "red"


def main() -> None:
    console = Console()
    if not LOG.exists():
        console.print(f"[red]no log at {LOG}[/red]")
        return
    rows = [json.loads(l) for l in LOG.open() if l.strip()]
    if not rows:
        console.print("[yellow]log is empty[/yellow]")
        return

    n = len(rows)
    correct = sum(r["correct"] for r in rows)
    console.rule(f"[bold]Quiz log: {n} attempts · {correct} correct ({pct(correct, n)})[/bold]")

    # 1. Trend: last 25 vs prior.
    if n >= 10:
        cutoff = max(n - 25, n // 2)
        recent = rows[cutoff:]
        prior = rows[:cutoff]
        r_acc = sum(x["correct"] for x in recent) / len(recent)
        p_acc = sum(x["correct"] for x in prior) / len(prior) if prior else 0
        arrow = "↑" if r_acc > p_acc else ("↓" if r_acc < p_acc else "→")
        console.print(
            f"  recent {len(recent)}: [{color_for_acc(r_acc)}]{r_acc*100:.0f}%[/]  "
            f"{arrow}  prior {len(prior)}: [{color_for_acc(p_acc)}]{p_acc*100:.0f}%[/]"
        )
    console.print()

    # 2. Per-move-type accuracy.
    by_type: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in rows:
        by_type[r["move_type"]][0] += int(r["correct"])
        by_type[r["move_type"]][1] += 1
    t = Table(title="Accuracy by move type (min 3 attempts)", title_style="bold")
    t.add_column("move type")
    t.add_column("correct", justify="right")
    t.add_column("%", justify="right")
    rows_sorted = sorted(by_type.items(), key=lambda kv: (kv[1][0] / kv[1][1], kv[1][1]))
    for mt, (c, tot) in rows_sorted:
        if tot < 3:
            continue
        acc = c / tot
        t.add_row(mt, f"{c}/{tot}", f"[{color_for_acc(acc)}]{pct(c, tot)}[/]")
    console.print(t)

    # 3. Most-missed matchups.
    miss_counter: Counter[tuple[str, tuple[str, ...]]] = Counter()
    total_counter: Counter[tuple[str, tuple[str, ...]]] = Counter()
    for r in rows:
        key = (r["move_type"], tuple(r["defender_types"]))
        total_counter[key] += 1
        if not r["correct"]:
            miss_counter[key] += 1
    t = Table(title="Most-missed matchups (≥2 misses)", title_style="bold")
    t.add_column("move type")
    t.add_column("defender")
    t.add_column("misses / seen", justify="right")
    shown = 0
    for (mt, dtypes), misses in miss_counter.most_common():
        if misses < 2:
            continue
        t.add_row(mt, "/".join(dtypes), f"{misses}/{total_counter[(mt, dtypes)]}")
        shown += 1
        if shown >= 10:
            break
    if shown:
        console.print(t)
    else:
        console.print("[dim]no matchup missed 2+ times yet[/dim]")

    # 4. Answer bias — what wrong answers do you give?
    bias: Counter[tuple[float, float]] = Counter()
    for r in rows:
        if not r["correct"]:
            bias[(r["correct_answer"], r["user_answer"])] += 1
    if bias:
        t = Table(title="Mistake patterns (actual → you said)", title_style="bold")
        t.add_column("actual", justify="right")
        t.add_column("you said", justify="right")
        t.add_column("count", justify="right")
        for (actual, said), cnt in bias.most_common(8):
            t.add_row(fmt_mult(actual), fmt_mult(said), str(cnt))
        console.print(t)


if __name__ == "__main__":
    main()
