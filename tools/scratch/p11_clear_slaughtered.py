import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
r = load('rules.json')
rules = r['rules']
if not any(x['id'] == 'stream.clear_slaughtered' for x in rules):
    i = next(k for k, x in enumerate(rules) if x['id'] == 'stream.clear_allied')
    # The water clears whatever settled the Pack: after a slaughter there is
    # nobody left to drink it, but Wenna still goes and looks.
    rules.insert(i + 1, {
        "id": "stream.clear_slaughtered",
        "when": {"all": [{"fact": "blight.days_clean", "gte": 2}, {"fact": "beasts.outcome", "eq": "slaughtered"}]},
        "effect": [{"set": {"stream.clear": True}}, {"history": {"id": "stream_cleared", "text": "stopped the poison in the Thornhollow stream", "tags": ["deed", "beasts"], "spread": 2}}],
        "once": True,
        "report": "Wenna came in at dawn, muddy to the knees: the stream is running clear. There is nothing left in the wood to drink from it.",
    })
save('rules.json', r)
print('ok')
