"""Adds the second pass's pieces to tools/comfy/ui_assets.json (once; ids already there are left)."""
import json

p = 'tools/comfy/ui_assets.json'
d = json.load(open(p, encoding='utf-8'))
have = {a['id'] for a in d['assets']}
new = [
    {"id": "well", "file": "frames/well.png", "size": [256, 256], "margins": [12, 12, 12, 12], "kind": "frame", "tile": True,
     "aspect": "1:1 (Square)",
     "prompt": "An empty sunken tray cut into blackened forged iron: the rim a thin lip of planished strap catching light along its foot, the floor flat and nearly black with faint hammer marks, no ornament, seen from the front.",
     "where": "Grids and lists inside a plate: the pack's and stores' slot wells, the map's list, the journal's list (Style.Well). Shown 200x120 to 1100x560; sunk below the plate, so darker than it and lit along its foot, not its top"},
    {"id": "slab", "file": "frames/slab.png", "size": [256, 256], "margins": [14, 14, 14, 14], "kind": "frame", "tile": True,
     "aspect": "1:1 (Square)",
     "prompt": "An empty flat raised plate of dark forged iron with a bevelled edge lit from the upper left, a thin dull gold hairline inset from the edge, the face plain and quiet, no corner ornament.",
     "where": "Groups inside a plate (Style.Slab): the standing's groups, the trait cards, the stores' sub-plates, the map's tools, the draft's build strip. Raised above the plate: lit top edge, no corner brackets (those belong to plates)"},
    {"id": "header", "file": "frames/header.png", "size": [512, 200], "margins": [0, 0, 0, 12], "kind": "frame", "tile": True,
     "aspect": "21:9 (Ultrawide)",
     "prompt": "A horizontal band of dark forged iron strap running edge to edge, its lower edge a hammered lip with a thin gold wire set into it, the face plain and dark, seamless left to right.",
     "where": "The band across the top of every full page (Overlay.Page): 1928x100 shown, the book's tabs at its left, the title plaque in the middle, Close at the right. Only the foot carries a border (12); it repeats along its length"},
    {"id": "banner", "file": "frames/banner.png", "size": [512, 192], "margins": [24, 14, 24, 14], "kind": "frame",
     "aspect": "21:9 (Ultrawide)",
     "prompt": "An empty horizontal nameplate of dark oxblood-stained iron hung from two lamp-iron brackets at its top corners, a gold wire border, a single small ember stone at the top centre, the face plain.",
     "where": "Verdicts and names cut in metal: the arena's end (THE ARENA IS WON, 470x100), the speaker's name in a conversation, who the survivor is becoming in creation. The words are drawn by the code: keep the face calm"},
    {"id": "pillar", "file": "frames/pillar.png", "size": [424, 728], "margins": [32, 100, 32, 36], "kind": "frame", "out": 12, "clear": 14,
     "aspect": "9:16 (Portrait)",
     "prompt": "An empty tall upright iron plaque like a narrow standing stele: a round crest socket at its head for a medallion, lamp-iron brackets at the top corners, nailed at the foot with two of the binders' square coins, the face plain dark iron.",
     "where": "Self: the four attributes (Might, Finesse, Wits, Resolve) as pillars, 188x340 shown (212x364 with the 12 they may reach past it). The code puts a 120 px medallion with the number at the head (keep a round seat for it 10-130 px down), the name, the words and a + button below"},
    {"id": "console", "file": "frames/console.png", "size": [512, 308], "margins": [48, 28, 48, 28], "kind": "frame", "tile": True, "out": 12, "clear": 0,
     "aspect": "16:9 (Widescreen)",
     "prompt": "A low wide plate of blackened forged iron like the top of a smith's anvil bench, a hammered lip with gold wire along its top edge, its ends turned down where they meet round fittings, the face plain dark, seamless left to right.",
     "where": "The HUD's console along the foot (GameHud.BuildVitals): the skills stand on it, the health globe at its left end and the art's ring at its right. 130 high, 300-720 wide with the skill count; its foot runs off the screen (only the top ~98 px show). Ends 48 wide to meet the globe and the ring"},
    {"id": "book_open", "file": "book/open.png", "size": [3400, 1704], "kind": "cut",
     "aspect": "2:1",
     "prompt": "A large leather-bound journal lying open, seen from directly above: tooled oxblood leather cover with worn gold-capped corners, two cream parchment pages curving down into the spine, the thickness of the leaves at the edges, the pages blank.",
     "where": "The Journal (OpenBook): the whole book, 1700x852 shown. The pages' words sit 78 px in from the cover's outer edge and 34 from the spine, 68 from top and foot: keep the pages blank and even there. The ribbons (sections) are drawn by the code over the top edge"},
    {"id": "medallion_ring", "file": "medallion/ring.png", "size": [440, 440], "kind": "cut",
     "aspect": "1:1 (Square)",
     "prompt": "A round ring of blackened forged iron bound with twisted gold wire, four of the binders' square coins nailed on it at the diagonals, front view, the centre empty.",
     "where": "Every medallion (Ornate Medallion, 44-220 shown): levels, attributes, the arts' grid and great medallion, facet sockets, creation's step road, the result's numbers, the draft cards' icon discs. Drawn into the medallion's box: the band from 80% to 100% of the half size, transparent inside 78% (the code's core shows there, in the school's or rarity's colour, with a hairline of it just inside the ring). A progress arc is drawn by the code at 88%"},
    {"id": "globe_rim", "file": "hud/globe_rim.png", "size": [288, 288], "kind": "cut",
     "aspect": "1:1 (Square)",
     "prompt": "A heavy round rim of forged iron like the collar of a lamp, gold wire inlaid round it, a lamp-iron bracket at its top, front view, the centre empty.",
     "where": "The health globe's rim (Ornate Globe, 144 shown, the liquid's radius 66): the band from radius 66 to 72 shown (92-100% of the half size), may reach in to 60; transparent inside so the liquid shows. A shield's arc is drawn by the code just outside it"},
    {"id": "globe_glass", "file": "hud/globe_glass.png", "size": [288, 288], "kind": "cut",
     "aspect": "1:1 (Square)",
     "prompt": "The reflections on a round glass vessel seen from the front: a soft curved highlight at the upper left, a thin bright rim of light at the lower right, everything else fully transparent.",
     "where": "Over the health globe's liquid, under its number (144 shown): highlights only, mostly transparent; the liquid's level, colour and trail are the code's"},
]
added = [a for a in new if a['id'] not in have]
for a in added:
    a['made_by'] = 'not yet made'
d['assets'].extend(added)
with open(p, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(d, f, indent=1, ensure_ascii=False)
print('added', [a['id'] for a in added])
