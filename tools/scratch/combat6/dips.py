"""The way in's dips: python dips.py FILE.jsonl fight
Per stage: share of runs under half in it, and by calling; what hurt her in the stage for runs that dipped in it
against those that did not (share of max HP per run)."""
import json, sys, collections

rows = []
for l in open(sys.argv[1], encoding="utf-8"):
    try: rows.append(json.loads(l))
    except ValueError: pass
rows = [r for r in rows if r["Spec"]["Fight"] == sys.argv[2]]
n = len(rows)
anyd = sum(any(s["LowHp"] < 0.5 for s in r["Stages"] if s["Name"] != "boss") for r in rows)
print(f"runs {n}, under half somewhere on the way in {anyd/n:.0%}")
for stg in ["stage 1", "stage 2", "stage 3"]:
    dipped = [r for r in rows if any(s["Name"] == stg and s["LowHp"] < 0.5 for s in r["Stages"])]
    clean = [r for r in rows if any(s["Name"] == stg and s["LowHp"] >= 0.5 for s in r["Stages"])]
    only = sum(1 for r in dipped if not any(s["LowHp"] < 0.5 for s in r["Stages"] if s["Name"] not in ("boss", stg)))
    byc = collections.Counter(r["Spec"]["Calling"] for r in dipped)
    tot = collections.Counter(r["Spec"]["Calling"] for r in rows)
    byt = collections.Counter(r["Spec"]["Tier"] for r in dipped)
    tott = collections.Counter(r["Spec"]["Tier"] for r in rows)
    print(f"\n{stg}: dipped {len(dipped)/n:.0%} (only here {only/n:.0%})  " + " ".join(f"{c} {byc[c]/tot[c]:.0%}" for c in sorted(tot)) + "  | " + " ".join(f"t{t} {byt[t]/tott[t]:.0%}" for t in sorted(tott)))
    def hurt(rs):
        h = collections.defaultdict(float)
        for r in rs:
            for s, v in r["HurtBy"].get(stg, {}).items(): h[s] += v / max(1, len(rs))
        return h
    hd, hc = hurt(dipped), hurt(clean)
    for s in sorted(set(hd) | set(hc), key=lambda s: -hd.get(s, 0))[:8]:
        print(f"   {s:44} {hd.get(s,0):5.2f} {hc.get(s,0):5.2f}")
