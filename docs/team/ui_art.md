# UI art: status

Agent a72467cac33063d3a. Branch `worktree-agent-a72467cac33063d3a` (merges the integration branch and
the UI design lead's). Handoff from before: `docs/handoff/ui_art.md`. One rebuild: `python tools/uiforge/build.py`.

## State

- **Every piece the redesign asks for is made and seen in game** (shots `godot/.shots/m3_*`):
  `medallion/ring.png`, `hud/globe_rim.png` + `globe_glass.png`, `frames/console.png`, `well.png`,
  `slab.png`, `header.png`, `pillar.png`, `crest_card.png`, `crest_row.png`, `banner.png`,
  `book/open.png`, `book/ribbon.png`, `ornaments/plaque_rule.png`; draft cards lengthened to
  736x1096 (320x500 shown, one to one). The level medallion is the Legion's seal (seven notches).
- **How**: round and shaped pieces are reliefs (`relief.py`: height + PBR maps in numpy,
  `blender_relief.py` renders them under the house light), then a light Krea paint-over with
  small exact parts protected. Rectangular frames that tile use `chrome.py` (Blender curves) or
  `pieces.iron_card`. Modules: `medals.py` (round), `pieces.py` (shaped/frames), `chrome.py`.
- **The globe carries the heart's idea**: the binders' chain coiled round the vessel, the pried-open
  link with its ember held in a lamp-iron collar at its head; the glass catches a leaded window.
- `hud/medal_heart.png` and `icons/glyph_color/heart.png` (the heart-stone) are no longer shown.

## Next (in order)

1. Remake the icon family that reads as blobs or people (blink, leap, smoke, mirror, echo, wraith,
   feint, risen, herd*, pyre, nova_sun, retaura, tether*, umbral, siphon, zone_blight*, expand,
   static, triple, arcane...) as modelled emblems (relief silhouettes) painted over on the Krea, then
   judge the whole family together at 17/28/44/67 px; remake the rest if the new ones outclass them.
2. Weak item icons (pelt, hide, dust, seed, root). Uncommon/rare cards louder.
3. Portrait cards for character creation when the UI design successor (ac76f400913a109cd) registers them.
4. Logo as a relief; stat icons; hover states screenshotted.

## Key decisions

- Reliefs for exact, scriptable forms with real light; paint-over only adds the hand (0.15-0.3).
- Paint-over caches by the render's content hash; emissive and small parts are protected.
- Wear is computed from curvature in file px, so a piece wears alike at any supersampling.
- The banner's centre stone is the code's (one stone cannot sit in a tiled middle).

## Blockers / notes for other areas

- ComfyUI was found down (refused) on 2026-10-04; asked the main session before restarting.
- UI design: the mirrored plaque rule is drawn through the title (`Plaque._Draw`), reported.
- Raw renders: `tools/comfy/out/uiforge/relief/`, paintings `.../paintover/` (ignored, on this PC).
