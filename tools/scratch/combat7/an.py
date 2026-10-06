"""Story harness summary: python an.py FILE.jsonl [--by fight,tier,bot,policy] [--hurt] [--lost]
Per group: won, boss on its first life, under half on the way in, way in and boss minutes, falls by stage."""
import json, sys, collections, statistics as st

path = sys.argv[1]
by = "fight,tier,bot,policy"
if "--by" in sys.argv: by = sys.argv[sys.argv.index("--by") + 1]
keys = by.split(",")
rows = []
for l in open(path, encoding="utf-8"):
    try: rows.append(json.loads(l))
    except ValueError: pass

def key(r):
    s = r["Spec"]
    bot = "deft" if s["Deft"] else "naive" if s["Naive"] else "plain"
    d = {"fight": s["Fight"], "tier": f"t{s['Tier']}", "bot": bot, "policy": s["Policy"], "calling": s["Calling"]}
    return tuple(d[k] for k in keys)

g = collections.defaultdict(list)
for r in rows: g[key(r)].append(r)
print(f"{'group':34} {'n':>3} {'won':>5} {'1st':>5} {'dip':>5} {'q':>5} {'way':>5} {'boss':>5} {'night':>5}  stage falls / median s")
for k in sorted(g):
    rs = g[k]; n = len(rs)
    won = sum(r["Won"] for r in rs) / n
    first = sum(r["BossFirstLife"] for r in rs) / n
    # Under half on the way in; under a quarter.
    dip = sum(r["LowWayIn"] < 0.5 for r in rs) / n
    q = sum(r["LowWayIn"] < 0.25 for r in rs) / n
    way = st.median(r["WayIn"] for r in rs)
    bs = [r["BossSeconds"] / 60 for r in rs if r.get("BossSeconds")]
    boss = st.median(bs) if bs else float("nan")
    night = st.median(r["Minutes"] for r in rs if r["Won"]) if any(r["Won"] for r in rs) else float("nan")
    stages = collections.defaultdict(lambda: [0, []])
    for r in rs:
        for s in r["Stages"]:
            stages[s["Name"]][0] += s["Falls"]; stages[s["Name"]][1].append(s["Seconds"])
    sf = " ".join(f"{nm[-1] if nm != 'boss' else 'B'}:{v[0]}/{st.median(v[1]):.0f}" for nm, v in stages.items())
    print(f"{'/'.join(k):34} {n:3} {won:5.0%} {first:5.0%} {dip:5.0%} {q:5.0%} {way:5.1f} {boss:5.1f} {night:5.1f}  {sf}")

if "--hurt" in sys.argv:
    part = sys.argv[sys.argv.index("--hurt") + 1] if len(sys.argv) > sys.argv.index("--hurt") + 1 and not sys.argv[sys.argv.index("--hurt") + 1].startswith("--") else None
    for k in sorted(g):
        tot = collections.defaultdict(float)
        for r in g[k]:
            for p, srcs in r["HurtBy"].items():
                if part and p != part: continue
                for s, v in srcs.items(): tot[(p, s)] += v / len(g[k])
        top = sorted(tot.items(), key=lambda x: -x[1])[:8]
        print("/".join(k), " | ".join(f"{p}:{s} {v:.2f}" for (p, s), v in top))

if "--lost" in sys.argv:
    for r in rows:
        if not r["Won"]:
            print(r["Spec"]["Key"], f"{r['Minutes']:.1f}", r["KilledBy"], r["Where"][:90])
