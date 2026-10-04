"""Nudge each combat skill's base damage by two signals at once: how it does
alone (the probe, `weapons --json`) and what share it takes inside real
mixed builds in whole arenas (the .jsonl runs), each against the median.
Neither is the truth alone: the probe flatters a skill whose range sets
how the bot fights, the arena under-rates one its build-mates outrange.

    python tune_blend.py out/w.json out/a.jsonl [out/b.jsonl ...] [--apply] [--damp 0.6]"""
import json, math, re, sys, collections, statistics as st

WEAPONS = '../logic/Content/Weapons.cs'
UTILITY = {'grave_tether': 0.85, 'gravecall': 0.9, 'hoarfrost': 0.9, 'thornbloom': 0.95}

args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith('--') and sys.argv[i - 1] != '--damp']
apply = '--apply' in sys.argv
damp = float(sys.argv[sys.argv.index('--damp') + 1]) if '--damp' in sys.argv else 0.6
probe = json.load(open(args[0]))
runs = [json.loads(l) for f in args[1:] for l in open(f) if l.strip() and not f.endswith('.json')]
pidx = {(d['weapon'], d['evo'], d['stage']): d for d in probe}

share = collections.defaultdict(list)
for r in runs:
    tot = sum(r['DamageBy'].values())
    n = len(r['Build'].split('|')[0].split())
    if tot <= 0 or n == 0:
        continue
    for k, v in r['DamageBy'].items():
        if (k, None, 'r8') in pidx:
            share[k].append(v / tot * n)
med = st.median([st.median(v) for v in share.values()])

src = open(WEAPONS, encoding='utf-8').read()
out = src
for w in sorted({d['weapon'] for d in probe}):
    r1, r4, r8 = pidx.get((w, None, 'r1')), pidx.get((w, None, 'r4')), pidx.get((w, None, 'r8'))
    if not (r1 and r4 and r8) or len(share.get(w, [])) < 8:
        continue
    g = math.exp(0.2 * math.log(max(.05, r1['index'])) + 0.4 * math.log(max(.05, r4['index'])) + 0.4 * math.log(max(.05, r8['index'])))
    a = st.median(share[w]) / med
    both = math.sqrt(g * a)
    target = UTILITY.get(w, 1.0)
    f = max(0.6, min(1.8, (target / both) ** damp))
    m = re.search(r'Id = "%s", Name = .*?(?=\n        new\(\)\n|\n    \}\.ToDictionary)' % w, out, re.S)
    block = m.group(0)
    nb = re.sub(r'(Base = new\(\) \{ Cooldown = [\d.]+, Damage = )([\d.]+)', lambda mm: mm.group(1) + ('%.2f' % (float(mm.group(2)) * f)).rstrip('0').rstrip('.'), block, count=1)
    out = out.replace(block, nb)
    print(f'{w:16} probe {g:.2f} arena {a:.2f} ({len(share[w])} runs) both {both:.2f} -> base x{f:.2f}')
if apply:
    open(WEAPONS, 'w', encoding='utf-8').write(out)
    print('applied')
