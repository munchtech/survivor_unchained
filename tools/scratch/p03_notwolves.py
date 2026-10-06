import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
d = load('dialogue.json')
NO_SURVIVORS = {"not": {"fact": "caravan.survivors", "exists": True}}
# Harlan hears "it wasn't wolves" from you only while Jory is not home to tell him himself.
for nid, c in choices(d, 'harlan', "It wasn't wolves"):
    if c.get('show') is None:
        c['show'] = NO_SURVIVORS
save('dialogue.json', d)
print('ok')
