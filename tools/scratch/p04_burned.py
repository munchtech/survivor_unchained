import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
d = load('dialogue.json')
# The crates that went up with the Roost, whether or not anyone was in the cages.
for v in node(d, 'vonnra', 'f_ember')['text']:
    if v.get('when') == {"history": "burned_roost"}:
        v['when'] = {"any": [{"history": "burned_roost"}, {"fact": "be.crates", "eq": "burned"}]}
# Snib's pipe goes to the sinkhole now; he does not say the pump still turns.
for v in node(d, 'snib', 'hub')['text']:
    if v.get('when') == {"fact": "dig.pump", "eq": "moved"}:
        v['text'] = "You again. Pipe goes to the sinkhole now. Deeper. Boss likes deeper. Boss has not SAID he likes it. Foreman is still foreman."
save('dialogue.json', d)
print('ok')
