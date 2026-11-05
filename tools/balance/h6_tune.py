"""H6 tuning (combat-h6): a variant of teeth.json tier 1 (and its director) and telegraphs.json, run through the arena
harness with SU_TEETH/SU_TELLS, then danger.py's table and falls. Env: H6_DLL (default bin/h6c), H6_OUT (default
the scratchpad's combat_h6/v).
python h6_tune.py NAME 'json-patch' [seeds] [bots] [extra harness args] python tune.py NAME 'json-patch' [seeds] [bots] [extra harness args]
patch: {"teeth": {...into tiers.1...}, "director": {...}, "tells": {"kinds": {...}, "waves": {...}}}"""
import json, sys, os, subprocess
W = 'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/combat-h6'
V = os.environ.get('H6_OUT', 'C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/5b4265e7-36f0-4dde-bca4-5df016e5b188/scratchpad/combat_h6/v'); os.makedirs(V, exist_ok=True)
name, patch = sys.argv[1], json.loads(sys.argv[2])
seeds = sys.argv[3] if len(sys.argv) > 3 else '8'
bots = sys.argv[4] if len(sys.argv) > 4 else 'idler,human,careless,deft'
extra = sys.argv[5:]
def merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): merge(a[k], v)
        else: a[k] = v
teeth = json.load(open(W + '/godot/data/content/teeth.json', encoding='utf-8'))
merge(teeth['tiers']['1'], patch.get('teeth', {}))
merge(teeth['tiers']['1'].setdefault('director', {}), patch.get('director', {}))
tells = json.load(open(W + '/godot/data/content/telegraphs.json', encoding='utf-8'))
merge(tells, patch.get('tells', {}))
tp, lp, out = os.path.join(V, name + '_teeth.json'), os.path.join(V, name + '_tells.json'), os.path.join(V, name + '.jsonl')
json.dump(teeth, open(tp, 'w')); json.dump(tells, open(lp, 'w'))
env = dict(os.environ, SU_TEETH=tp, SU_TELLS=lp)
subprocess.run(['dotnet', os.environ.get('H6_DLL', W + '/godot/balance/bin/h6c/Balance.dll'), 'arena', '--people', 'pack', '--tier', '1', '--seeds', seeds, '--bot', bots, '--par', '11', '--out', out] + extra,
               env=env, cwd=W + '/godot/balance', stdout=open(os.path.join(V, name + '.log'), 'w'), stderr=subprocess.STDOUT)
print(name, json.dumps(patch))
subprocess.run(['python', W + '/tools/balance/danger.py', out, '--by', 'none'])
subprocess.run(['python', W + '/tools/balance/danger.py', out, '--falls'])
