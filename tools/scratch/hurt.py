import json, sys, collections
# What hurt her, by part and source: mean share of her health per run, top sources.
rs = [json.loads(l) for l in open(sys.argv[1])]
tier = int(sys.argv[2]) if len(sys.argv) > 2 else None
g = collections.defaultdict(list)
for r in rs:
    s = r['Spec']
    if tier and s['Tier'] != tier:
        continue
    g[(s['Fight'], s['Tier'], 'deft' if s['Deft'] else 'plain')].append(r)
for k in sorted(g):
    l = g[k]
    print(k, len(l))
    for part in ['stage 1', 'stage 2', 'stage 3', 'boss']:
        tot = collections.Counter()
        for r in l:
            for src, v in r.get('HurtBy', {}).get(part, {}).items():
                tot[src] += v / len(l)
        s = sum(tot.values())
        print(f'  {part}: {s:.2f} hp  ' + ', '.join(f'{a} {b:.2f}' for a, b in tot.most_common(7)))
