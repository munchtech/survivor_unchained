"""Compare the night's arc between balance sweeps: python compare.py a.jsonl b.jsonl ...
Per stretch: the horde alive (median), and the share of runs whose health dipped under a half and a quarter."""
import json, statistics as st, sys

STRETCHES = [(0, 2), (2, 7), (7, 10), (10, 12), (12, 15), (15, 17), (17, 20), (20, 25), (25, 28), (28, 30), (30, 33)]

def load(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

for name in sys.argv[1:]:
    runs = load(name)
    won = sum(1 for r in runs if r.get("WonAt"))
    fell = sum(1 for r in runs if r["Died"] and not r.get("WonAt"))
    full = [r for r in runs if len(r["ByMinute"]) > 29]
    e30 = st.median(r["ByMinute"][29]["Ember"] for r in full) if full else float("nan")
    k30 = st.median(sum(m["Kills"] for m in r["ByMinute"][:30]) for r in full) if full else float("nan")
    print(f"{name}: n={len(runs)} won {won/len(runs):.0%}, fell before the boss {fell}, ember at 30 {e30}, kills to 30 {k30}")
    for a, b in STRETCHES:
        rs = [r for r in runs if len(r["ByMinute"]) >= b]
        if not rs:
            continue
        lows = [min(m["LowHp"] for m in r["ByMinute"][a:b]) for r in rs]
        alive = [st.median(m["Alive"] for m in r["ByMinute"][a:b]) for r in rs]
        print(f"  {a:2d}-{b:2d}: alive {st.median(alive):4.0f}  under 1/2 {sum(1 for x in lows if x < 0.5)/len(lows):4.0%}  under 1/4 {sum(1 for x in lows if x < 0.25)/len(lows):4.0%}")
