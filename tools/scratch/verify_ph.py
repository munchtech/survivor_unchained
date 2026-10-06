"""Check every Poly Haven id we use against the Poly Haven API: it exists, its name, type and authors."""
import json, urllib.request, sys
TYPES = {0: 'hdri', 1: 'texture', 2: 'model'}
ids = sys.argv[1:]
out = {}
for i in ids:
    try:
        req = urllib.request.Request(f'https://api.polyhaven.com/info/{i}', headers={'User-Agent': 'SurvivorUnchained-provenance-audit/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.load(r)
        out[i] = {'name': j.get('name'), 'type': TYPES.get(j.get('type')), 'authors': list(j.get('authors', {}).keys())}
        print(f"{i}\t{TYPES.get(j.get('type'))}\t{j.get('name')}\t{', '.join(j.get('authors', {}).keys())}")
    except Exception as e:
        print(f'{i}\tMISSING\t{e}')
json.dump(out, open(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\ph.json', 'w'), indent=1)
