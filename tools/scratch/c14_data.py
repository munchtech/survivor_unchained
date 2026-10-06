"""C14's voiced lines into the data. Run from the worktree root."""
import json, os
from collections import OrderedDict

P = os.path.join('godot', 'data', 'content', 'dialogue.json')
d = json.load(open(P, encoding='utf-8'), object_pairs_hook=OrderedDict)
assert 'cin_road_back' not in d
d['cin_road_back'] = {
    "npc": "cin_road_back",
    "entry": [{"node": "place"}],
    "nodes": {
        "place": {"id": "place", "speaker": "brannoc", "text": "You know the place.", "next": "wat"},
        "wat": {"id": "wat", "speaker": "brannoc", "text": "...Wat.",
                "choices": [{"text": "(Continue.)", "end": True}]},
    },
}
with open(P, 'w', encoding='utf-8', newline='\r\n') as h:
    h.write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')

N = os.path.join('godot', 'data', 'content', 'npcs.json')
n = json.load(open(N, encoding='utf-8'), object_pairs_hook=OrderedDict)


def find_speakers(x):
    if isinstance(x, dict):
        if 'cin_iron_marker' in x:
            return x
        for v in x.values():
            r = find_speakers(v)
            if r is not None:
                return r
    return None


sp = find_speakers(n)
assert sp is not None and 'cin_road_back' not in sp
# keep the cinematic entries together: insert after cin_iron_marker
items = list(sp.items())
sp.clear()
for k, v in items:
    sp[k] = v
    if k == 'cin_iron_marker':
        sp['cin_road_back'] = {"name": "The Road Back", "title": "Cinematic", "glyph": "campfire"}
with open(N, 'w', encoding='utf-8', newline='\r\n') as h:
    h.write(json.dumps(n, indent=1, ensure_ascii=False) + '\n')
print('ok')
