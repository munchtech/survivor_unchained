import json

p = 'tools/comfy/ui_assets.json'
d = json.load(open(p, encoding='utf-8'))
have = {a['id'] for a in d['assets']}
new = [
    {"id": "crest_card", "file": "frames/crest_card.png", "size": [600, 700], "margins": [40, 72, 40, 40], "kind": "frame", "out": 10,
     "aspect": "3:4 (Portrait Standard)",
     "prompt": "An empty upright card of blackened forged iron hung from two lamp-iron brackets, a crest panel across its head with a round seat at its middle, a binders' square coin nailed at each foot corner, the face plain and dark, symmetrical.",
     "where": "Every crested choice (OrnateBox Card): the arts' facet cards (287x280), creation's calling cards (470x92), the Last Lamp's choices (300x330), a Self pillar until frames/pillar.png exists. Neutral iron: the code tints the crest band (top 70-120 px) and a hairline in the rarity or school, and glows it when lifted"},
    {"id": "ribbon", "file": "book/ribbon.png", "size": [264, 172], "kind": "cut",
     "aspect": "1:1 (Square)",
     "prompt": "A single silk ribbon bookmark hanging straight down, its tail cut in a V notch, pale ivory silk with a soft sheen down its middle and fine woven texture, front view, on pure black.",
     "where": "The Journal's section ribbons (RibbonBox), 132x66-86 shown, stretched to fit. Paint it pale and neutral: the code dyes it each section's colour (red, green, blue, gold) and adds its shadow"},
    {"id": "plaque_rule", "file": "ornaments/plaque_rule.png", "size": [480, 24], "kind": "cut",
     "aspect": "21:9 (Ultrawide)",
     "prompt": "A thin horizontal gold wire rule running from a small cut ember stone at its left end out to a fine point at its right end, front view, on pure black.",
     "where": "The title plaque's rules (Plaque) either side of every page's name: drawn to the right of the title as painted and mirrored to its left, the stone toward the words; stretched to 90-180 px long, so the wire must stretch cleanly"},
]
added = [a for a in new if a['id'] not in have]
for a in added:
    a['made_by'] = 'not yet made'
d['assets'].extend(added)
with open(p, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(d, f, indent=1, ensure_ascii=False)
print('added', [a['id'] for a in added])
