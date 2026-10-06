import json, os, subprocess
S = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad'
merged = json.load(open(os.path.join('godot', 'data', 'content', 'dialogue.json'), encoding='utf-8'))
ours = json.load(open(os.path.join(S, 'dlg_ours.json'), encoding='utf-8'))
theirs = json.load(open(os.path.join(S, 'dlg_theirs.json'), encoding='utf-8'))


def diff(a, b, label):
    out = []
    for cid in sorted(set(a) | set(b)):
        if json.dumps(a.get(cid), sort_keys=True) == json.dumps(b.get(cid), sort_keys=True):
            continue
        an = (a.get(cid) or {}).get('nodes', {})
        bn = (b.get(cid) or {}).get('nodes', {})
        ch = sorted(n for n in set(an) | set(bn) if json.dumps(an.get(n), sort_keys=True) != json.dumps(bn.get(n), sort_keys=True))
        out.append(f'{cid}: {ch}')
    print('=====', label, len(out))
    for o in out:
        print(' ', o[:300])

diff(theirs, merged, 'theirs -> merged (should be only ours\' cinematic work + fortune)')
diff(ours, merged, 'ours -> merged (should be only theirs\' work + fortune)')
raw = open(os.path.join('godot', 'data', 'content', 'dialogue.json'), 'rb').read()
print('CRLF lines', raw.count(b'\r\n'), 'LF-only', raw.count(b'\n') - raw.count(b'\r\n'))
