import json, sys, statistics as st, collections
rs = [json.loads(l) for l in open(sys.argv[1])]
only = sys.argv[2] if len(sys.argv) > 2 else None
g = collections.defaultdict(list)
for r in rs: g[r['Spec']['Policy']].append(r)
for k, v in sorted(g.items()):
    if only and only not in k: continue
    tot = collections.Counter()
    for r in v:
        s = sum(r['DamageBy'].values()) or 1
        for a, b in r['DamageBy'].items(): tot[a] += b / s / len(v)
    btk = [r['BossTtk'] for r in v if r['BossTtk']]
    print(f"{k:12} boss TTK med {st.median(btk) if btk else 0:5.1f} p90 {sorted(btk)[int(len(btk)*0.9)-1] if btk else 0:5.1f}  " + ", ".join(f"{a} {b:.0%}" for a, b in tot.most_common(9)))
