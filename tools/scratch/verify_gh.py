"""Read each repository's detected licence (SPDX id) from the GitHub API."""
import json, urllib.request, sys
for r in sys.argv[1:]:
    try:
        req = urllib.request.Request(f'https://api.github.com/repos/{r}/license', headers={'User-Agent': 'SurvivorUnchained-provenance-audit/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            j = json.load(resp)
        print(f"{r}\t{(j.get('license') or {}).get('spdx_id')}\t{j.get('html_url')}")
    except Exception as e:
        print(f'{r}\tERR {e}')
