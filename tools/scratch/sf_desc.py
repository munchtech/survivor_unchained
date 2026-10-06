"""Print each Sketchfab model's description (trimmed), to spot fan art, rips or third-party sources."""
import json, urllib.request, sys
for uid in sys.argv[1:]:
    req = urllib.request.Request(f'https://api.sketchfab.com/v3/models/{uid}', headers={'User-Agent': 'SurvivorUnchained-provenance-audit/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)
    d = (j.get('description') or '').replace('\n', ' ')
    print(f"== {j.get('name')}: {d[:700]}")
