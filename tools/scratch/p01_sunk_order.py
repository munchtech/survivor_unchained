import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
d = load('dialogue.json')
t = node(d, 'vonnra', 'f_ember')['text']
sunk = next(v for v in t if v.get('when') == {"fact": "be.crates", "eq": "sunk"})
t.remove(sunk)
i = next(k for k, v in enumerate(t) if v.get('when') == {'history': 'burned_roost'})
t.insert(i, sunk)
save('dialogue.json', d)
for v in t: print(v.get('when'), v['text'][:60])
