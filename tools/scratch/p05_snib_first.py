import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
d = load('dialogue.json')
# Met for the first time over a pump somebody has already broken.
first = node(d, 'snib', 'first')
if isinstance(first['text'], str):
    first['text'] = [
        {"when": {"fact": "dig.pump", "eq": "broken"}, "text": "Oi! OI! Surface-meat! No surface-meat past the pump! Foreman's orders! ...Snib is the foreman. Snib. Pump is BROKEN. Somebody broke it. Snib does not know who. Snib knows exactly who. What do you want? Quick."},
        {"text": first['text']},
    ]
save('dialogue.json', d)
print('ok')
