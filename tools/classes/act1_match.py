# Act 1 story runs against a reference on MATCHED seeds (Spec.Key): boss seconds, falls a night, nights won.
# Seed sets must match: seeds 1-32 alone run about 2% apart from 1-96, which once read as a "drift" (13 October).
#   python tools/classes/act1_match.py REF.jsonl X.jsonl [Y.jsonl ...] [--cells]
# REF for Act 1 is the named baseline "pre-Flare 11 Oct" (tools/classes/out/prefl11.jsonl; CLASSES §7, "Act 1 baseline").
# A run made with --type <road> matches the baseline's run of its calling (the baseline has no types: the pre-Flare game
# with an empty board), so a type's Act 1 is read against its calling's. --cells adds each fight x hands cell.
import json, sys
ROADS = {"sunderer", "bulwark", "butcher", "chainbound", "kindler", "moonweaver", "roadknife", "verge_hunter"}
def key(r):
    return "/".join(x for x in r["Spec"]["Key"].split("/") if x not in ROADS)
def load(p):
    return {key(r): r for r in (json.loads(l) for l in open(p, encoding="utf-8"))}
args = [a for a in sys.argv[1:] if not a.startswith("--")]
cells = "--cells" in sys.argv
R = load(args[0])
def mean(xs): return sum(xs) / len(xs) if xs else float("nan")
for p in args[1:]:
    X = load(p); ks = [k for k in R if k in X]
    if not ks: print(p, "no matched runs"); continue
    bk = [k for k in ks if R[k].get("BossSeconds") and X[k].get("BossSeconds")]
    rb = mean([R[k]["BossSeconds"] for k in bk]); xb = mean([X[k]["BossSeconds"] for k in bk])
    rf = mean([R[k].get("Falls", 0) for k in ks]); xf = mean([X[k].get("Falls", 0) for k in ks])
    rw = mean([bool(R[k]["Won"]) for k in ks]); xw = mean([bool(X[k]["Won"]) for k in ks])
    print(f"{p.replace(chr(92), '/').split('/')[-1]:16s} n{len(ks)} boss {rb:.0f}->{xb:.0f}s ({100*(xb/rb-1):+.1f}%) "
          f"falls {rf:.3f}->{xf:.3f} won {100*rw:.1f}->{100*xw:.1f}%")
    if cells:
        out = []
        for fight in sorted({R[k]["Spec"]["Fight"] for k in bk}):
            for deft in (False, True):
                ck = [k for k in bk if R[k]["Spec"]["Fight"] == fight and R[k]["Spec"]["Deft"] == deft]
                if ck:
                    out.append(f"{fight}/{'deft' if deft else 'plain'} {100*(mean([X[k]['BossSeconds'] for k in ck])/mean([R[k]['BossSeconds'] for k in ck])-1):+.1f}%")
        print("   cells: " + ", ".join(out))
