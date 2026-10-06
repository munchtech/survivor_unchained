import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
d = load('dialogue.json')
# "Your chapter is written": once the book is closed, the fortune is not read again.
for nid, c in choices(d, 'vonnra', 'Read my fortune'):
    if c.get('when') == {"fact": "chapter.ready", "eq": True}:
        c['when'] = {"all": [{"fact": "chapter.ready", "eq": True}, {"not": {"fact": "chapter.done", "eq": True}}]}
save('dialogue.json', d)
print('ok')
