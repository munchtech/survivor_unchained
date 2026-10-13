# Act 1 story runs against a reference on MATCHED seeds (Spec.Key): boss seconds, falls a night, nights won.
# Seed sets must match: seeds 1-32 alone run about 2% apart from 1-96, which once read as a "drift" (13 October).
#   python tools/classes/act1_match.py REF.jsonl X.jsonl [Y.jsonl ...]
# REF for Act 1 is the named baseline "pre-Flare 11 Oct" (tools/classes/out/prefl11.jsonl; CLASSES §7, "Act 1 baseline").
import json, sys
def load(p):
    return {json.loads(l)["Spec"]["Key"]: json.loads(l) for l in open(p, encoding="utf-8")}
R = load(sys.argv[1])
for p in sys.argv[2:]:
    X = load(p); ks = [k for k in R if k in X]
    if not ks: print(p, "no matched runs"); continue
    bk = [k for k in ks if R[k].get("BossSeconds") and X[k].get("BossSeconds")]
    rb = sum(R[k]["BossSeconds"] for k in bk) / len(bk); xb = sum(X[k]["BossSeconds"] for k in bk) / len(bk)
    rf = sum(R[k].get("Falls", 0) for k in ks) / len(ks); xf = sum(X[k].get("Falls", 0) for k in ks) / len(ks)
    rw = sum(bool(R[k]["Won"]) for k in ks) / len(ks); xw = sum(bool(X[k]["Won"]) for k in ks) / len(ks)
    print(f"{p.replace(chr(92), '/').split('/')[-1]:16s} n{len(ks)} boss {rb:.0f}->{xb:.0f}s ({100*(xb/rb-1):+.1f}%) "
          f"falls {rf:.3f}->{xf:.3f} won {100*rw:.1f}->{100*xw:.1f}%")
