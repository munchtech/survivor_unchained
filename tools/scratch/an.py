import json, sys, collections
rs = [json.loads(l) for l in open(sys.argv[1])]
g = collections.defaultdict(list)
for r in rs:
    s = r['Spec']
    g[(s['Fight'], s['Tier'], s['Policy'], 'deft' if s['Deft'] else 'naive' if s.get('Naive') else 'plain')].append(r)
for k in sorted(g):
    l = g[k]
    lost = [r for r in l if not r['Won']]
    where = collections.Counter()
    for r in lost:
        st = [x for x in r['Stages'] if x['Falls'] > 0]
        where[(st[-1]['Name'] if st else '?') + ':' + r['KilledBy']] += 1
    falls = collections.Counter()
    for r in l:
        for x in r['Stages']:
            if x['Falls'] > 0:
                falls[x['Name']] += x['Falls']
    lows = {n: sum(1 for r in l for x in r['Stages'] if x['Name'] == n and x['LowHp'] < 0.5) for n in ['stage 1', 'stage 2', 'stage 3', 'boss']}
    print(k, len(l), 'won', sum(r['Won'] for r in l), 'falls', dict(falls), 'under half', lows)
    print('   lost:', dict(where))
