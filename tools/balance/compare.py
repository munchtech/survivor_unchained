#!/usr/bin/env python3
"""Two balance-lab sweeps side by side (their arena_runs.csv), as Markdown.

    python3 tools/balance/compare.py BEFORE_DIR AFTER_DIR

Win rate (the boss killed) and losses before the boss, by calling, people,
tier and people x tier. Plain Python: no packages needed."""
import csv, sys, statistics
from collections import defaultdict

def load(d):
    return list(csv.DictReader(open(f"{d}/arena_runs.csv")))

def cell(rows):
    if not rows: return "-"
    won = sum(r["won"] == "1" for r in rows)
    return f"{100 * won / len(rows):.0f}% ({len(rows)})"

def table(title, a, b, key):
    ga, gb = defaultdict(list), defaultdict(list)
    for r in a: ga[key(r)].append(r)
    for r in b: gb[key(r)].append(r)
    print(f"#### {title}\n\n| | before | after |\n|---|---|---|")
    for k in sorted(set(ga) | set(gb)):
        print(f"| {k} | {cell(ga[k])} | {cell(gb[k])} |")
    print()

a, b = load(sys.argv[1]), load(sys.argv[2])
table("All", a, b, lambda r: "all")
table("By tier", a, b, lambda r: f"tier {r['tier']}")
table("By calling", a, b, lambda r: r["calling"])
table("By people", a, b, lambda r: r["people"])
table("By people and tier", a, b, lambda r: f"{r['people']} t{r['tier']}")
