import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
d = load('dialogue.json')
for v in node(d, 'vonnra', 'f_ember')['text']:
    if v.get('when') == {"fact": "be.crates", "eq": "dig"}:
        v['when'] = {"all": [{"fact": "be.crates", "eq": "dig"}, {"fact": "caravan.cargo", "eq": "with_kerchiefs"}]}
save('dialogue.json', d)
print('ok')
