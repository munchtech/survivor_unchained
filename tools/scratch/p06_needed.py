import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cj import *
it = load('items.json')
items = it['items']
# Each quest thing's part in the story, after which it is only a keepsake.
needed = {
    "stream_sample": {"not": {"knows": "clue.analysis"}},
    "slurry_sample": {"not": {"knows": "root_cause"}},
    "caravan_manifest": {"not": {"knows": "clue.blasting_ember"}},
    "clerks_key": {"not": {"fact": "warehouse.searched", "eq": True}},
    "sigil_fragment": {"not": {"fact": "vault.opened", "eq": True}},
}
for k, v in needed.items():
    assert items[k]['kind'] == 'quest', k
    items[k]['needed'] = v
save('items.json', it)
print('ok')
