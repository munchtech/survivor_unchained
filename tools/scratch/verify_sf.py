"""Check each Sketchfab model's current licence, author and title through Sketchfab's public API."""
import json, urllib.request, sys
for uid in sys.argv[1:]:
    try:
        req = urllib.request.Request(f'https://api.sketchfab.com/v3/models/{uid}', headers={'User-Agent': 'SurvivorUnchained-provenance-audit/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.load(r)
        lic = j.get('license') or {}
        user = j.get('user') or {}
        print(f"{uid}\t{j.get('name')}\t{user.get('displayName')} ({user.get('username')})\t{lic.get('label')} | {lic.get('slug')} | {lic.get('requirements')}\tdownloadable={j.get('isDownloadable')}\tpublished={j.get('publishedAt')}\tnsfw={j.get('isAgeRestricted')}")
    except Exception as e:
        print(uid, 'ERR', e)
