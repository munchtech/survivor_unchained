import json

p = 'tools/comfy/ui_assets.json'
d = json.load(open(p, encoding='utf-8'))
for a in d['assets']:
    if a['id'] in ('banner', 'crest_card'):
        a['tile'] = True
have = {a['id'] for a in d['assets']}
if 'crest_row' not in have:
    d['assets'].append({"id": "crest_row", "file": "frames/crest_row.png", "size": [600, 184], "margins": [40, 36, 40, 28], "kind": "frame", "tile": True, "out": 8,
        "aspect": "21:9 (Ultrawide)",
        "prompt": "An empty wide low plate of blackened forged iron, a short crest strip along its top edge, lamp-iron brackets at its top corners, the face plain and dark, seamless left to right.",
        "where": "A crested card too low for crest_card's slice: creation's calling cards (470x92) and any row-shaped choice. Neutral iron, the code tints its crest strip and hairline",
        "made_by": "not yet made"})
with open(p, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(d, f, indent=1, ensure_ascii=False)
print('ok')
