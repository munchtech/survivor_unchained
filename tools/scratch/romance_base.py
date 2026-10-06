"""Three-way view of the romance drafts: base (dialogue.json the drafts were
built from), draft, live. For each node: who changed it. Run from the worktree root."""
import json, os, subprocess

BASE = 'e1ff6374a2d6c396c38ed150c858cf64a4be1a7e'
base_all = json.loads(subprocess.run(['git', 'show', f'{BASE}:godot/data/content/dialogue.json'], capture_output=True).stdout.decode('utf-8'))
live_all = json.load(open(os.path.join('godot', 'data', 'content', 'dialogue.json'), encoding='utf-8'))


def J(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


for who in ('sella', 'maeca', 'keegan', 'rav'):
    d = json.load(open(os.path.join('docs', 'romance', 'data', who + '.json'), encoding='utf-8'))
    draft = d.get(who, d)
    base, live = base_all[who], live_all[who]
    print(f'== {who}')
    for k in sorted(set(base) | set(draft) | set(live)):
        if k == 'nodes':
            continue
        b, dr, l = J(base.get(k)), J(draft.get(k)), J(live.get(k))
        if b != dr or b != l:
            print(f'  [{k}] draft {"changed" if b != dr else "same"}, live {"changed" if b != l else "same"}')
    nodes = sorted(set(base['nodes']) | set(draft['nodes']) | set(live['nodes']))
    for n in nodes:
        b, dr, l = J(base['nodes'].get(n)), J(draft['nodes'].get(n)), J(live['nodes'].get(n))
        dc, lc = b != dr, b != l
        if dc and lc:
            tag = 'BOTH changed (conflict)' if dr != l else 'both, same'
        elif dc:
            tag = 'draft only'
        elif lc:
            tag = 'live only'
        else:
            continue
        print(f'  {n}: {tag}')
