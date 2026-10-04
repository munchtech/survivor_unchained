# UI art: status

Agent a72467cac33063d3a. Branch `worktree-agent-a72467cac33063d3a` (= predecessor's
`worktree-agent-abd496197891ea843` + this work). Handoff from before: `docs/handoff/ui_art.md`.

## State (stopped at the owner's usage limit)

- **Medallions remade as reliefs** (item 1 of the list): new `tools/uiforge/relief.py` (a piece
  modelled as a height field + PBR maps in numpy) and `blender_relief.py` (one vertex per render
  pixel, rendered in Cycles under the house light from `blender_frames`), then a light paint-over
  (`paintover.py`, 0.26-0.30) with the wire, the chain and the number's well protected.
  - `hud/medal_level.png`: the Legion's seal. Planished iron ring, forge-welded at its foot, the
    binders' twisted wire, seven notches at the inner edge (the binders' seven keys), a dark well
    for the number with the ember smouldering in the gap at its foot.
  - `hud/medal_heart.png`: a bezel with a heart-shaped hollow, an iron chain coiled round it in a
    channel, one link pried open at the head with ember at the break (each link of the chain is
    anchored in a heart: STORY_BIBLE).
  - `icons/glyph_color/heart.png`: the heart-stone the code lays over the heart medal (22 px):
    a heart-cut ruby, faceted, lit inside. Only that HUD uses the `heart` key.
  - Built by `python tools/uiforge/build.py medals` (`tools/uiforge/medals.py`).
- **Not yet seen in the running game.** Judged only in mock-ups at shown size over a game shot.
- `build.py painted` no longer runs fitall's `minimap` and `medals` groups: they would have
  overwritten the Blender minimap rim and art ring with the old AI cut-outs on a full rebuild.

## Next (in order)

0. **Merge the UI design lead's branch** `worktree-agent-a5629aff0f215ea4a@ed542b3` (pushed; not yet
   merged here). Per its message: health is now a globe, so the health bar, its casing and
   `medal_heart` are no longer shown (the heart medal and stone above are then unused; the stone
   may suit the globe). New pieces asked for by name (UI_ART_BRIEF 4.9, ui_assets.json "not yet
   made"): `frames/well`, `slab`, `header`, `banner`, `pillar` (Self), `console` (HUD band),
   `book/open.png`, `medallion/ring.png` (every design medallion, middle open from 78%),
   `hud/globe_rim.png`, `hud/globe_glass.png`. `map_frame` now frames the Wayfinder's table's maps.
   Draft cards are 320x500 now (the painted card stretches 48 px in the middle: refit).
   `relief.py` suits the globe rim and the medallion ring directly. Do these before the list below.
1. Import and screenshot the HUD at 1920x1080 (`python tools/uiforge/shots.py --prefix m1`);
   check the level number in the well, the heart's beat, both by day and night. Judge
   "do we have soul?" at shown size; iterate (the level band is dark at 58 px; the chain may want
   more contrast).
2. Skill icons that show a person (leap, smoke, mirror, echo, wraith, feint) and the soft ones at
   17 px. Seen at 40/17 px (contact sheet): many more read as smoke blobs (tether, tether2,
   tether_mark, umbral, siphon, zone_blight*, risen, herd*). Consider remaking the family as
   relief emblems + paint-over rather than text-to-image.
3. Weak item icons (pelt, hide, dust, seed, root). 4. Uncommon/rare cards louder.
5. Logo as a relief (`relief.py` suits letters). 6. Stat icons as assets in `icons/glyph/stat_*`.
7. Hover states screenshotted.

## Key decisions

- Reliefs over Blender curve specs for round, exact pieces: a height field gives any form
  (notches, links, facets, ragged edges) with real light, and stays scriptable.
- The heart's stone is the icon, the setting is the medal: the code draws the icon over it.
- Paint-over caches by the render's content hash, so a changed model is painted afresh.

## Notes for other areas

- UI design (a5629aff0f215ea4a): no UI code touched here. Its merge is pushed (ed542b3); merge it first.
- Raw renders and paintings: `tools/comfy/out/uiforge/relief/` and `.../paintover/` (ignored).
  Copied the predecessor's `tools/comfy/out/uiforge/` into this worktree (613 MB) so builds reuse it.
