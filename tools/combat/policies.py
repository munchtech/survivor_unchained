"""Won rate and falls (minutes) by drafting policy, and the boss's median time to kill.
usage: python tools/combat/policies.py godot/balance/out/RUNS.jsonl [...]"""
import json, sys, collections
for f in sys.argv[1:]:
    d = collections.defaultdict(list)
    for l in open(f):
        r = json.loads(l); s = r['Spec']
        d[s['Policy']].append(r)
    out = []
    for pol in sorted(d):
        v = d[pol]
        won = sum(r['Won'] for r in v)
        falls = sorted(round(r['Minutes'], 1) for r in v if r['Died'])
        bt = sorted(r['BossTtk'] for r in v if r['Won'] and r['BossTtk'])
        out.append(f"{pol} {won}/{len(v)} won ({100*won//len(v)}%) falls {falls} bossTTK {round(bt[len(bt)//2]) if bt else '-'}")
    print(f, ' | '.join(out))
