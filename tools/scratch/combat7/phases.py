"""The boss's phases on its last life: python phases.py FILE.jsonl [--by fight,policy,tier,calling]
Per group: median boss seconds, each phase's median length, and how often a phase turned at its ceiling
(health left above the mark when it turned)."""
import json, sys, collections, statistics as st
path = sys.argv[1]
by = sys.argv[sys.argv.index("--by") + 1].split(",") if "--by" in sys.argv else ["fight", "policy"]
MARKS = {"dig": [0.65, 0.30], "hollow": None, "roost": None}
rows = []
for l in open(path, encoding="utf-8"):
    try: rows.append(json.loads(l))
    except ValueError: pass
def key(r):
    s = r["Spec"]
    d = {"fight": s["Fight"], "tier": f"t{s['Tier']}", "policy": s["Policy"], "calling": s["Calling"], "bot": "deft" if s["Deft"] else "plain"}
    return tuple(d[k] for k in by)
g = collections.defaultdict(list)
for r in rows:
    if r["Won"] and r.get("BossSeconds"): g[key(r)].append(r)
print(f"{'group':30} {'n':>3} {'boss':>5} {'p1':>5} {'p2':>5} {'p3':>5} {'p1 hp':>6} {'p2 hp':>6} {'>240':>5} {'>300':>5}")
for k in sorted(g):
    rs = g[k]
    p1, p2, p3, h1, h2 = [], [], [], [], []
    for r in rs:
        t = r.get("BossTurns") or []
        if len(t) >= 2:
            a, b = t[0]["Item1"], t[1]["Item1"]
            p1.append(a); p2.append(b - a); p3.append(r["BossSeconds"] - b)
            h1.append(t[0]["Item2"]); h2.append(t[1]["Item2"])
    med = lambda x: st.median(x) if x else float("nan")
    bs = [r["BossSeconds"] for r in rs]
    print(f"{'/'.join(k):30} {len(rs):>3} {med(bs):>5.0f} {med(p1):>5.0f} {med(p2):>5.0f} {med(p3):>5.0f} {med(h1):>6.2f} {med(h2):>6.2f} {sum(b > 240 for b in bs) / len(bs):>5.0%} {sum(b > 300 for b in bs) / len(bs):>5.0%}")
