"""Each combat skill's share of a run's damage against a fair share (one over
the skills carried), over many arenas, from the harness's .jsonl files:

    python shares.py out/a.jsonl [out/b.jsonl ...]

1.00 is a fair share; a skill well above it carries the builds it is in,
one well below rides along. Rules credited to a skill (its evolution's, a
status it put there) count as its own."""
import json, sys, collections, statistics as st

runs = [json.loads(l) for f in sys.argv[1:] for l in open(f) if l.strip()]
weapons = set()
for r in runs:
    for w in r['Build'].split('|')[0].split():
        weapons.add(w.rstrip('0123456789'))
idx = collections.defaultdict(list)
for r in runs:
    tot = sum(v for k, v in r['DamageBy'].items())
    if tot <= 0:
        continue
    carried = [k for k in r['DamageBy'] if not (':' in k or k in ('other', 'art', 'dash', 'thorns', 'summon') or k.endswith('_ally') or k == 'spirit_wolf')]
    # Only what the build carried at the end (the build string names them, evolved or not).
    n = len(r['Build'].split('|')[0].split())
    if n == 0:
        continue
    for k in carried:
        idx[k].append(r['DamageBy'][k] / tot * n)
print(f'{len(runs)} runs')
for k, v in sorted(idx.items(), key=lambda kv: -st.median(kv[1])):
    print(f'{k:16} share x{st.median(v):.2f}  (mean x{st.mean(v):.2f}, {len(v)} runs)')
