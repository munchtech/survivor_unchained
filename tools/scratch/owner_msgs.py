"""List the owner's own typed messages in the main transcript that match a pattern (provenance clues)."""
import json, re, sys
pat = re.compile(sys.argv[1], re.I)
p = sys.argv[2]
with open(p, encoding='utf-8', errors='replace') as f:
    for line in f:
        try:
            j = json.loads(line)
        except Exception:
            continue
        if j.get('type') != 'user':
            continue
        m = j.get('message', {})
        c = m.get('content')
        texts = []
        if isinstance(c, str):
            texts = [c]
        elif isinstance(c, list):
            texts = [x.get('text', '') for x in c if isinstance(x, dict) and x.get('type') == 'text']
        for t in texts:
            if t and pat.search(t) and not t.startswith('<'):
                print('---', j.get('timestamp'))
                print(t[:900])
