import json, sys, statistics as st, collections
rs = [json.loads(l) for l in open(sys.argv[1])]
key = sys.argv[2] if len(sys.argv) > 2 else 'Policy'
g = collections.defaultdict(list)
for r in rs: g[r['Spec'][key]].append(r)
for k, v in sorted(g.items()):
    dead = [r for r in v if r['Died']]
    print(f"{k:12} runs {len(v):3} died {len(dead):2} lowHp {st.median(r['LowHp'] for r in v):.2f} taken {st.median(r['DamageTaken'] for r in v):6.0f}")
    for r in dead:
        print(f"    {r['Spec']['Calling']:8} {r['Spec']['People']:9} min {r['Minutes']:4.1f} by {r['KilledBy']:18} {r['Build'][:160]}")
