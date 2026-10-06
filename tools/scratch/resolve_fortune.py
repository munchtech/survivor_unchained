"""Resolve the merge in dialogue.json: the fortune is read once (theirs) and
only after dark (ours). Run from the worktree root."""
import json, os, re

p = os.path.join(os.getcwd(), 'godot', 'data', 'content', 'dialogue.json')
s = open(p, encoding='utf-8', newline='').read()
# keep our side of each conflict hunk; the choice is rebuilt below anyway
pat = re.compile(r'<<<<<<< HEAD\r?\n(.*?)=======\r?\n.*?>>>>>>> [^\r\n]*\r?\n', re.S)
s, n = pat.subn(lambda m: m.group(1), s)
assert n == 7, n
d = json.loads(s)

SHOW = {"all": [{"fact": "chapter.ready", "eq": True}, {"not": {"fact": "chapter.done", "eq": True}}]}
WHEN = {"any": [{"time": "night"}, {"time": "dusk"}]}
count = 0
for cid, c in d.items():
    for nid, node in c['nodes'].items():
        chs = node.get('choices') or []
        for i, ch in enumerate(chs):
            if ch.get('goto') == 'fortune' and cid == 'vonnra':
                new = {}
                for k, v in ch.items():
                    if k == 'when':
                        new['show'] = SHOW
                        new['when'] = WHEN
                    elif k == 'show':
                        continue
                    else:
                        new[k] = v
                assert new.get('locked') == 'She reads only after dark', (nid, new)
                chs[i] = new
                count += 1
assert count == 7, count
with open(p, 'w', encoding='utf-8', newline='\r\n') as h:
    h.write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')
print('ok', count)
