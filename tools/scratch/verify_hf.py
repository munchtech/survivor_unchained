"""Read each Hugging Face model's declared licence (model card metadata) through the public API."""
import json, urllib.request, sys
for repo in sys.argv[1:]:
    try:
        req = urllib.request.Request(f'https://huggingface.co/api/models/{repo}', headers={'User-Agent': 'SurvivorUnchained-provenance-audit/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.load(r)
        cd = j.get('cardData') or {}
        print(f"{repo}\tlicense={cd.get('license')}\tname={cd.get('license_name')}\tlink={cd.get('license_link')}\tgated={j.get('gated')}\tbase={cd.get('base_model')}")
    except Exception as e:
        print(repo, 'ERR', e)
