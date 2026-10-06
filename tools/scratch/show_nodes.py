import json, os, sys
S = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad'
merged = json.load(open(os.path.join('godot', 'data', 'content', 'dialogue.json'), encoding='utf-8'))
ours = json.load(open(os.path.join(S, 'dlg_ours.json'), encoding='utf-8'))
theirs = json.load(open(os.path.join(S, 'dlg_theirs.json'), encoding='utf-8'))
for spec in sys.argv[1:]:
    cid, nid = spec.split('.')
    for name, d in (('ours', ours), ('theirs', theirs), ('merged', merged)):
        n = d[cid]['nodes'].get(nid)
        print(f'--- {name} {spec}')
        print(json.dumps(n, ensure_ascii=False, indent=1)[:2500])
