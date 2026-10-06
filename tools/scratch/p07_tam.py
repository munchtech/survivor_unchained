import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
d = load('dialogue.json')
# Tam warms to being believed the first time he tells it, not every time he is asked again.
story = node(d, 'tam', 'story')
fx = story['effects']
for i, e in enumerate(fx):
    if 'rel' in e and e['rel']['npc'] == 'tam':
        fx[i] = {"if": {"not": {"npcFlag": {"npc": "tam", "key": "believed", "eq": True}}},
                 "then": [e, {"npcFlag": {"npc": "tam", "key": "believed", "value": True}}]}
c = choice(d, 'tam', 'story', 'You did right')
c['once'] = 'did_right'
save('dialogue.json', d)
print('ok')
