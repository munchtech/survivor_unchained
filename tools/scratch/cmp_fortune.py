import json, sys, os, subprocess
S = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad'
ours = json.load(open(os.path.join(S, 'dlg_ours.json'), encoding='utf-8'))
theirs = json.load(open(os.path.join(S, 'dlg_theirs.json'), encoding='utf-8'))
base_txt = subprocess.run(['git', 'show', 'ebab8151f9ba0facfac6f0a2754f70f9116a5808:godot/data/content/dialogue.json'], capture_output=True).stdout.decode('utf-8')
base = json.loads(base_txt)


def find(d):
    out = []
    for cid, c in d.items():
        for nid, n in c['nodes'].items():
            for i, ch in enumerate(n.get('choices', [])):
                t = ch.get('text')
                if 'fortune' in json.dumps(t):
                    out.append((cid, nid, i, ch))
    return out

for name, d in (('base', base), ('ours', ours), ('theirs', theirs)):
    print('=====', name)
    for cid, nid, i, ch in find(d):
        print(cid, nid, i, json.dumps(ch, ensure_ascii=False)[:600])

# diff convo-level: which conversations differ between base and theirs
print('===== conversations changed in theirs vs base')
for cid in sorted(set(base) | set(theirs)):
    if json.dumps(base.get(cid), sort_keys=True) != json.dumps(theirs.get(cid), sort_keys=True):
        bn = base.get(cid, {}).get('nodes', {})
        tn = theirs.get(cid, {}).get('nodes', {})
        ch = [n for n in set(bn) | set(tn) if json.dumps(bn.get(n), sort_keys=True) != json.dumps(tn.get(n), sort_keys=True)]
        other = json.dumps({k: v for k, v in base.get(cid, {}).items() if k != 'nodes'}, sort_keys=True) != json.dumps({k: v for k, v in theirs.get(cid, {}).items() if k != 'nodes'}, sort_keys=True)
        print(cid, sorted(ch), 'entry/meta changed' if other else '')
