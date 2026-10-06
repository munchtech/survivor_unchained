"""Summarise the shipped clip libraries' sources and licences (heroine_clips.json, folk_clips.json)."""
import json, collections, sys
for p in sys.argv[1:]:
    j = json.load(open(p, encoding='utf-8'))
    items = j.items() if isinstance(j, dict) else enumerate(j)
    by = collections.defaultdict(list)
    for k, v in items:
        if not isinstance(v, dict):
            continue
        lic = v.get('licence') or v.get('license') or '?'
        src = v.get('source', '?')
        tag = src.split(' ')[0] if src else '?'
        by[(lic, tag)].append(f"{k} <{src}>" if tag not in ('keyed',) else k)
    print('=====', p)
    for (lic, tag), names in sorted(by.items()):
        print(f'  [{lic} | {tag}] {len(names)}:')
        for n in names:
            print('      ', n[:200])
