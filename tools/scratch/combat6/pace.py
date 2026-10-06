"""Does the build's pace decide falls? python pace.py FILE.jsonl fight
For each run that reached the boss: its pace (share of his health a minute, from the first life: a fall's
"left" and fight time, or the clean win's time), its reach and health; falls by pace quartile and by reach."""
import json, sys, collections, statistics as st

rows = []
for l in open(sys.argv[1], encoding="utf-8"):
    try: rows.append(json.loads(l))
    except ValueError: pass
rows = [r for r in rows if r["Spec"]["Fight"] == sys.argv[2]]
pts = []
for r in rows:
    b = [x for x in r["Stages"] if x["Name"] == "boss"]
    fa = [x for x in r.get("FellAt", []) if x.startswith("boss")]
    if fa:
        p = fa[0].split(); t = int(p[2][1:]); left = int(p[4].rstrip('%')) / 100
        pace = (1 - left) / max(1, t) * 60
        fell = True
    elif b and r["Won"]:
        pace = 60 / b[0]["Seconds"]; fell = False
    else: continue
    pts.append((pace, fell, r.get("ReachAtBoss", 0), r["MaxHpAtBoss"], r["Spec"]["Calling"], r["Won"], len(fa)))
pts.sort()
q = len(pts) // 4
print("pace quartiles (share of him a minute): first-life fall rate, won")
for i in range(4):
    part = pts[i * q:(i + 1) * q if i < 3 else len(pts)]
    print(f"  q{i+1} pace {part[0][0]:.2f}-{part[-1][0]:.2f}: fell {sum(p[1] for p in part)/len(part):.0%} won {sum(p[5] for p in part)/len(part):.0%} n {len(part)}")
print("by reach: first-life fall rate, won, second-life fall given first")
for lo, hi in [(0, 3), (3, 6), (6, 10), (10, 99)]:
    part = [p for p in pts if lo <= p[2] < hi]
    if not part: continue
    f1 = [p for p in part if p[1]]
    print(f"  reach {lo}-{hi}: n {len(part)} fell {len(f1)/len(part):.0%} won {sum(p[5] for p in part)/len(part):.0%} fell again {sum(p[6] >= 2 for p in f1)/max(1,len(f1)):.0%}")
print("by calling: median pace, fell")
for c in sorted(set(p[4] for p in pts)):
    part = [p for p in pts if p[4] == c]
    print(f"  {c}: pace {st.median(p[0] for p in part):.2f} fell {sum(p[1] for p in part)/len(part):.0%} reach {st.median(p[2] for p in part):.1f}")
