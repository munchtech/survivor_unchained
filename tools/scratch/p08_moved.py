import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
# The cargo sold down the south road takes the six crates with it, to whoever paid for them.
r = load('rules.json')
rule = next(x for x in r['rules'] if x['id'] == 'caravan.box_moved')
eff = rule['effect'] if isinstance(rule['effect'], list) else [rule['effect']]
if not any('if' in e and e['if'] == {"not": {"fact": "be.crates", "exists": True}} for e in eff):
    eff.append({"if": {"not": {"fact": "be.crates", "exists": True}}, "then": [{"set": {"be.crates": "dig"}}]})
rule['effect'] = eff
save('rules.json', r)
d = load('dialogue.json')
t = node(d, 'vonnra', 'f_ember')['text']
if not any(v.get('when') == {"fact": "be.crates", "eq": "dig"} for v in t):
    i = next(k for k, v in enumerate(t) if v.get('when') == {'knows': 'clue.blasting_ember'})
    t.insert(i, {"when": {"fact": "be.crates", "eq": "dig"}, "text": "And six crates gone down the south road with the rest of the cargo, sold to whoever paid for them first. I think you know who that was."})
save('dialogue.json', d)
print('ok')
