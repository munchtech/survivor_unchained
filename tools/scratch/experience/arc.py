"""The run's arc from a balance sweep: python arc.py runs.jsonl
Per minute (median over runs alive at that minute): ember, drafts, kills, alive, taken (share of max?), low HP,
fodder TTK; plus when runs end, and the endless phase's survival curve."""
import json, sys, statistics as st
from collections import defaultdict

runs = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
print(f"{len(runs)} runs")
won = [r for r in runs if r.get("WonAt")]
print(f"won {len(won)} ({len(won)/len(runs):.0%}); fell before the boss {sum(1 for r in runs if r['Died'] and not r.get('WonAt'))}")
ends = sorted(r["Minutes"] for r in runs)
print("run lengths (min):", [round(x, 1) for x in ends])
# endless survival: of runs that won, how long did they last past the win
past = sorted(r["Minutes"] - r["WonAt"] for r in won if r["Died"])
print("won then fell, minutes past the win:", [round(x, 1) for x in past])
print("won and still standing at the cap:", sum(1 for r in won if not r["Died"]))

by = defaultdict(lambda: defaultdict(list))
for r in runs:
    for i, m in enumerate(r["ByMinute"]):
        for k, v in m.items():
            if isinstance(v, (int, float)) and v == v:
                by[i][k].append(v)
keys = ["Ember", "Drafts", "Kills", "Alive", "Taken", "LowHp", "TtkFodder", "TtkElite"]
print("min  n   " + "  ".join(f"{k:>9}" for k in keys))
for i in sorted(by):
    n = len(by[i]["Ember"])
    row = []
    for k in keys:
        v = by[i].get(k, [])
        row.append(f"{st.median(v):9.2f}" if v else f"{'-':>9}")
    print(f"{i+1:3d} {n:3d} " + "  ".join(row))
