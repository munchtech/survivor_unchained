"""Falls at the boss, in depth: python falls.py FILE.jsonl [fight]
By calling and draft: reached the boss, fell on the first life, won after the rise, lost; the phase and time of
each fall; what hurt her at the boss for those who fell against those who did not (share of max HP per run)."""
import json, sys, collections, statistics as st

rows = []
for l in open(sys.argv[1], encoding="utf-8"):
    try: rows.append(json.loads(l))
    except ValueError: pass
fight = sys.argv[2] if len(sys.argv) > 2 else None
if fight: rows = [r for r in rows if r["Spec"]["Fight"] == fight]

def boss(r):
    b = [x for x in r["Stages"] if x["Name"] == "boss"]
    return b[0] if b else None

g = collections.defaultdict(lambda: [0, 0, 0, 0])
for r in rows:
    s = r["Spec"]; b = boss(r)
    if not b: continue
    k = (s["Fight"], s["Calling"], s["Policy"])
    g[k][0] += 1
    if b["Falls"] > 0:
        g[k][1] += 1
        if r["Won"]: g[k][2] += 1
    if not r["Won"]: g[k][3] += 1
print(f"{'fight/calling/draft':28} {'boss':>5} {'fell':>5} {'saved':>5} {'lost':>5}")
for k in sorted(g):
    a, f, w, n = g[k]
    print(f"{'/'.join(k):28} {a:5} {f:5} {w:5} {n:5}  fell {f/a:.0%} saved {w/max(1,f):.0%}")

# First fall vs second fall phases and times.
print("\nfalls at the boss: (first life / after the rise) by phase")
fp = collections.Counter(); sp = collections.Counter()
for r in rows:
    fa = [x for x in r.get("FellAt", []) if x.startswith("boss")]
    for i, x in enumerate(fa):
        ph = x.split()[1]
        (fp if i == 0 else sp)[ph] += 1
print(" first:", dict(sorted(fp.items())), " second:", dict(sorted(sp.items())))
ts = collections.defaultdict(list)
for r in rows:
    for i, x in enumerate([x for x in r.get("FellAt", []) if x.startswith("boss")]):
        p = x.split(); ts[(i, p[1])].append((int(p[2][1:]), int(p[4].rstrip('%'))))
for k in sorted(ts):
    v = ts[k]
    print(f"  {'first' if k[0]==0 else 'second'} {k[1]}: n {len(v)} fight-t median {st.median(t for t,_ in v):.0f}s, boss left median {st.median(l for _,l in v):.0f}%")

# What hurt her at the boss: fell vs not.
def hurt(rs):
    tot = collections.defaultdict(float)
    for r in rs:
        for s, v in r["HurtBy"].get("boss", {}).items(): tot[s] += v / max(1, len(rs))
    return tot
fell = [r for r in rows if boss(r) and boss(r)["Falls"] > 0]
clean = [r for r in rows if boss(r) and boss(r)["Falls"] == 0]
hf, hc = hurt(fell), hurt(clean)
print(f"\nhurt at the boss per run (share of max HP): fell n={len(fell)} / clean n={len(clean)}")
for s in sorted(set(hf) | set(hc), key=lambda s: -(hf.get(s, 0)))[:14]:
    print(f"  {s:50} {hf.get(s,0):5.2f} {hc.get(s,0):5.2f}")
# Marked blows landed.
print("\nboss marked blows landed (mean): fell", round(sum(r["BossLanded"] for r in fell)/max(1,len(fell)),1), " clean", round(sum(r["BossLanded"] for r in clean)/max(1,len(clean)),1))
print("boss time when clean (median s):", st.median(boss(r)["Seconds"] for r in clean) if clean else "-")
