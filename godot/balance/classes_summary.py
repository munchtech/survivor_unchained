"""The classes acceptance numbers (docs/design/CLASSES.md section 7) from a sweep's files:
types against the median and a full board against an empty one (fe.md, fe30.md: the reports of
full+empty runs), and on-calling (off.jsonl from `arena --offcalling`, full.jsonl the greedy full-lamp runs).
usage: python godot/balance/classes_summary.py <dir>

On-calling is normalised: each calling's damage drafting a road's skills over its own greedy
damage, home against the median of the other three. Raw on/off mostly measures how strong each
calling is anyway (the types band), not what its lamps add to its own road.
The signature-skill rows count the one signature skill each road has built so far (phase 5 adds the rest)."""
import json, re, statistics as st, sys, os
D = sys.argv[1]

def types(md):
    rows = {}
    on = False
    for line in open(os.path.join(D, md), encoding='utf-8'):
        if line.startswith('### Types'): on = True; continue
        if on and line.startswith('###'): break
        m = re.match(r'\|\s*(\d+)\s*\|\s*(\w+)\s*\|\s*([\w/]+)\s*\|\s*\d+\s*\|\s*([\d.]+)k\s*\|\s*([\d.]+)', line) if on else None
        if m: rows[(int(m[1]), m[2], m[3])] = (float(m[4]), float(m[5]))
    return rows

for md, tag in (('fe.md', 'tier'), ('fe30.md', 'L30')):
    r = types(md)
    print(f'== {md}: ratio to median (full / empty), full/empty; * = out of band')
    for t in sorted({k[0] for k in r}):
        cells = []
        for ct in sorted({k[2] for k in r if k[0] == t}):
            f, e = r.get((t, 'full', ct)), r.get((t, 'empty', ct))
            if not f or not e: continue
            fe = f[0] / e[0]
            star = '*' if not (0.74 <= f[1] <= 1.35) or not (0.74 <= e[1] <= 1.35) or not (0.80 <= fe <= 1.25) else ' '
            cells.append(f'{ct.split("/")[1]} {f[1]:.2f}/{e[1]:.2f} {fe:.2f}{star}')
        print(f'T{t}: ' + ' | '.join(cells))

sig = {'bulwark': 'oathblade', 'butcher': 'axe_gyre', 'chainbound': 'iron_palms', 'kindler': 'cinderfall',
       'moonweaver': 'seeking_motes', 'roadknife': 'knifestorm', 'verge_hunter': 'volley', 'sunderer': 'dawnpulse'}
home = {'bulwark': 'warden', 'sunderer': 'warden', 'butcher': 'reaver', 'chainbound': 'reaver',
        'kindler': 'arcanist', 'moonweaver': 'arcanist', 'roadknife': 'stalker', 'verge_hunter': 'stalker'}
p = os.path.join(D, 'off.jsonl')
if os.path.exists(p):
    rs = [json.loads(l) for l in open(p) if l.strip()]
    print('== on-calling: the one built signature skill, k dmg/min (median per calling), home / median of the other three; target 1.00-1.25')
    for road, s in sig.items():
        for t in sorted({x['Spec']['Tier'] for x in rs}):
            per = {}
            for c in ('warden', 'reaver', 'arcanist', 'stalker'):
                v = [x['DamageBy'].get(s, 0) / max(1, x['Minutes']) / 1000 for x in rs
                     if x['Spec'].get('For') == road and x['Spec']['Calling'] == c and x['Spec']['Tier'] == t]
                if v: per[c] = st.median(v)
            h = per.get(home[road]); off = [v for c, v in per.items() if c != home[road]]
            if h is None or not off: continue
            ratio = h / max(1e-9, st.median(off))
            print(f'{road:12} {s:14} T{t} home {h:6.1f} off {st.median(off):6.1f} ratio {ratio:.2f}{"" if 1.0 <= ratio <= 1.25 else " *"}')

if os.path.exists(os.path.join(D, "off.jsonl")) and os.path.exists(os.path.join(D, "full.jsonl")):
    print("== on-calling, dmg/min at minute 25; target normalised <= 1.25")
    L = lambda f: [json.loads(l) for l in open(os.path.join(D, f)) if l.strip()]
    off, full = L('off.jsonl'), L('full.jsonl')
    d25 = lambda r: r['ByMinute'][24]['Damage'] if len(r['ByMinute']) >= 25 else None
    home = {'bulwark': 'warden', 'sunderer': 'warden', 'butcher': 'reaver', 'chainbound': 'reaver', 'kindler': 'arcanist', 'moonweaver': 'arcanist', 'roadknife': 'stalker', 'verge_hunter': 'stalker'}
    C = ['warden', 'reaver', 'arcanist', 'stalker']
    med = lambda xs: st.median([x for x in xs if x is not None]) if any(x is not None for x in xs) else None
    print('road         tier  raw on/off  normalised (each calling over its own greedy run)')
    for road, hc in home.items():
        for t in (1, 2, 3, 4):
            base = {c: med([d25(r) for r in full if r['Spec']['Calling'] == c and r['Spec']['Tier'] == t]) for c in C}
            val = {c: med([d25(r) for r in off if r['Spec'].get('For') == road and r['Spec']['Calling'] == c and r['Spec']['Tier'] == t]) for c in C}
            if None in val.values() or None in base.values(): continue
            raw = val[hc] / st.median([val[c] for c in C if c != hc])
            norm = (val[hc] / base[hc]) / st.median([val[c] / base[c] for c in C if c != hc])
            print(f'{road:12} T{t}   {raw:5.2f}      {norm:5.2f}{"" if norm <= 1.25 else " *"}')
