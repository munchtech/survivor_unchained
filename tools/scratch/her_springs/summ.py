"""summ.py BEFORE.jsonl [AFTER.jsonl]: per clip, the skirt's worst sample (points inside her thigh, deepest mm) and the
pauldrons' worst (% of their points inside her skin, at which time), before and after."""
import json, sys
def read(f):
    o = {}
    for line in open(f, encoding='utf-8'):
        try: r = json.loads(line)
        except Exception: continue
        if 'clip' not in r or not r.get('clip'): continue
        c = o.setdefault(r['clip'], {'sk': (0, 0, 0), 'pa': (0, 0, 0, 0)})
        s = r['slots'].get('skirt'); p = r['slots'].get('pauldrons')
        if s:
            th = s['by_region'].get('thigh', 0)
            if th > c['sk'][0]: c['sk'] = (th, r['t'], s['deep_mm'])
        if p and p['n']:
            pct = 100 * p['inside'] / p['n']
            if pct > c['pa'][0]: c['pa'] = (pct, r['t'], p['deep_mm'], p['inside'])
    return o
fs = [read(f) for f in sys.argv[1:]]
clips = list(fs[0])
print(f"{'clip':22} " + " | ".join(f"skirt thigh pts (t, deep mm)   pauldrons % (t, deep mm)" for _ in fs))
for c in clips:
    row = []
    for o in fs:
        x = o.get(c)
        if not x: row.append('-'); continue
        sk, pa = x['sk'], x['pa']
        row.append(f"{sk[0]:6d} ({sk[1]:.2f}s, {sk[2]:5.1f})          {pa[0]:5.1f}% ({pa[1]:.2f}s, {pa[2]:4.1f})")
    print(f"{c:22} " + " | ".join(row))
