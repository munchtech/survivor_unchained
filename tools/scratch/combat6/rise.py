"""Falls at the boss and what the rise did: python rise.py FILE.jsonl
Per fight and hands: runs that reached the boss, fell there, and won after the rise; and the cards and
the build's lowest health at the boss for those who fell against those who did not."""
import json, sys, collections

rows = []
for l in open(sys.argv[1], encoding="utf-8"):
    try: rows.append(json.loads(l))
    except ValueError: pass
g = collections.defaultdict(lambda: [0, 0, 0, 0])
for r in rows:
    s = r["Spec"]
    bot = "deft" if s["Deft"] else "naive" if s["Naive"] else "plain"
    k = (s["Fight"], bot, s["Policy"])
    boss = [x for x in r["Stages"] if x["Name"] == "boss"]
    if not boss: g[k][3] += 1; continue
    g[k][0] += 1
    if boss[0]["Falls"] > 0:
        g[k][1] += 1
        if r["Won"]: g[k][2] += 1
print(f"{'fight/hands/draft':28} {'at boss':>7} {'fell':>5} {'won after':>9} {'never reached':>13}")
for k in sorted(g):
    a, f, w, n = g[k]
    print(f"{'/'.join(k):28} {a:7} {f:5} {w:9} {n:13}")
