"""What would each romance data draft overwrite in the live dialogue.json?
Run from the worktree root."""
import json, os

live = json.load(open(os.path.join('godot', 'data', 'content', 'dialogue.json'), encoding='utf-8'))
for who in ('sella', 'maeca', 'keegan', 'rav'):
    p = os.path.join('docs', 'romance', 'data', who + '.json')
    d = json.load(open(p, encoding='utf-8'))
    conv = d.get(who, d)
    ln = live[who]['nodes']
    dn = conv['nodes']
    removed = sorted(set(ln) - set(dn))
    added = sorted(set(dn) - set(ln))
    changed = sorted(n for n in set(ln) & set(dn) if json.dumps(ln[n], sort_keys=True) != json.dumps(dn[n], sort_keys=True))
    print(f'== {who}: live {len(ln)} nodes, draft {len(dn)}')
    print('  live nodes the draft drops:', removed)
    print('  new nodes:', len(added), added[:40])
    print('  nodes changed:', changed)
    entry_same = json.dumps(live[who].get('entry'), sort_keys=True) == json.dumps(conv.get('entry'), sort_keys=True)
    print('  entry same:', entry_same)
