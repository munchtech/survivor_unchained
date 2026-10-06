"""The story explorer's four findings (data side). Run from the worktree root."""
import json, os

P = os.path.join('godot', 'data', 'content', 'dialogue.json')
d = json.load(open(P, encoding='utf-8'))

# (a) Wenna's mask: she gives it to whoever brought her bitterroot, or to whoever
# cleaned her stream (not sold it to Pell).
MASK_WHEN = {"any": [
    {"rel": {"npc": "wenna", "axis": "affection", "gte": 20}},
    {"all": [{"history": "stream_cleared"}, {"not": {"fact": "beasts.outcome", "eq": "exploited"}}]},
]}
n = 0
for nid in ('first', 'hub'):
    for ch in d['wenna']['nodes'][nid]['choices']:
        if ch.get('goto') == 'mask':
            assert ch['when'] == {"rel": {"npc": "wenna", "axis": "affection", "gte": 20}}, ch['when']
            ch['when'] = MASK_WHEN
            n += 1
assert n == 2
mk = d['wenna']['nodes']['mask']
old = mk['text']
if isinstance(old, list):
    old = old[-1]['text']
assert old.startswith('My blightward.'), old
mk['text'] = [
    {"when": {"history": "stream_cleared"},
     "text": "My blightward. I made it the fever year. Stuff the beak with bitterroot and you can walk through air "
             "that'd drop a horse. You cleaned my stream, child. Take it. ...Something down there's still cooking, "
             "and I'm too old to go where it's needed."},
    {"text": old},
]

# (b) Keegan's supper: earned by listening to her (the Warden, Ashe) and eating
# with her once (docs/WRITING_PASS.md names the road).
n = 0
for ch in d['keegan']['nodes']['hub']['choices']:
    if ch.get('goto') == 'supper':
        assert ch['when'] == {"all": [{"rel": {"npc": "keegan", "axis": "respect", "gte": 30}},
                                      {"rel": {"npc": "keegan", "axis": "affection", "gte": 15}}]}, ch['when']
        ch['when'] = {"all": [{"rel": {"npc": "keegan", "axis": "respect", "gte": 25}},
                              {"rel": {"npc": "keegan", "axis": "affection", "gte": 10}}]}
        n += 1
assert n == 1
with open(P, 'w', encoding='utf-8', newline='\r\n') as h:
    h.write(json.dumps(d, indent=1, ensure_ascii=False) + '\n')

# (d) dig.pump = running, written: the state the Dig is in until someone moves,
# breaks or blows the pump (Act 2 reads "still running at the act's end").
# And the burial morning, as a fact for that day only (C08's plain trigger).
R = os.path.join('godot', 'data', 'content', 'rules.json')
r = json.load(open(R, encoding='utf-8'))
rules = r['rules']
assert not any(x.get('id') == 'dig.pump.running' for x in rules)
i = next(k for k, x in enumerate(rules) if x.get('id') == 'tremor')
rules.insert(i, {"id": "dig.pump.running", "once": True,
                 "when": {"not": {"fact": "dig.pump", "exists": True}},
                 "effect": [{"set": {"dig.pump": "running"}}]})
burial = next(x for x in rules if x.get('id') == 'nell.burial')
assert burial['effect'] == {"set": {"nell.buried": True}}
burial['effect'] = [
    {"set": {"nell.buried": True, "nell.burying": True}},
    {"later": {"days": 1, "id": "nell.burying", "effect": {"set": {"nell.burying": False}}}},
]
with open(R, 'w', encoding='utf-8', newline='\r\n') as h:
    h.write(json.dumps(r, indent=1, ensure_ascii=False) + '\n')
print('ok')
