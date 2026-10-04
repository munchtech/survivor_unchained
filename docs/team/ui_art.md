# UI art: status

Agent a1a394643aabfb169 (successor to a72467cac33063d3a). Branch `worktree-agent-a1a394643aabfb169`.
Handoff from before: `docs/handoff/ui_art.md`. One rebuild: `python tools/uiforge/build.py`.

## State (paused for the owner's machine, 2026-10-04)

- **Icons: 33 remade as modelled emblems** (`emblems.py`, picks in `emblems.PICKS`, `build.py emblems`):
  the 23 from the brief plus the six arts that showed people (boot, horns, chain, shield, mark, wing).
  Each is drawn as shapes with height, material and grain, lit, set in its school's glow, then painted
  over on the Krea and cut on its own silhouette. Seen in game (arts, HUD, draft).
- **Items:** pelt, hide, root, seed, dust and the blasting ember were repainted from words (`items.T2I`, `items.PICKS`).
- **Logo** (`logo.py`, `build.py logo`): Cinzel at weight 900 (OFL, `tools/uiforge/fonts`) in forged
  steel, with the seven-link chain between the words, its middle link pried open and the ember in the
  break. Seen on the title.
- **Cards:** uncommon and rare are louder (`cardcolour.py`). The common is dressed with bramble or rime
  before the paint; the rare is laid back over its dressing.
- **Page pieces** (`pages.py`, `build.py pages`), for the UI design lead's frameless layout (merged at 0165e94):
  - built and in `godot/art/ui`: `frames/header.png` (worked leather, a forged rail, seen in game);
    `page/backdrop_grain.png` and `page/backdrop_edges.png` (previewed over a shot, not yet wired);
    `frames/column_divider.png` and `column_divider_stone.png`; `ornaments/section_mark.png`;
  - written but **not yet rendered**: `hero_plate`, `card_light`.

## Next (exact)

1. `python tools/uiforge/pages.py hero_plate card_light`, then look at both at file size and at 1080. Fix
   the corner brackets' reach and the vellum's tone if they need it.
2. Run `godot --headless --path godot --import` and restore stray imports (see Gotchas). The new PNGs have no
   `.import` yet. Commit them.
3. Send the slice margins to the UI design lead (a69858664f1d3dd29) so they can wire the pieces:
   - header: (0,0,0,12) Tile, as before.
   - column_divider: 48x1120 file, (0,24,0,24) Tile; the middle is one 512 px period.
   - column_divider_stone: 64x64 file.
   - section_mark: 24x24 file.
   - hero_plate: (56,56,56,56) Tile, Out 12.
   - card_light: (20,20,20,20) Tile.
   - backdrop_grain: tiled. backdrop_edges: stretched.
4. Show the owner before and after at full resolution. "Before" is the integration branch's page shots;
   "after" is shots once the pieces are wired.
5. Then: rethink leap's concept (weak at 90 px in the art slot); judge the crafting lead's three new
   item icons (moon_draught, flask, fur_braid at dcd68cd) against the set; portrait cards for creation;
   hover-state shots; the side-by-side legal check of the icons before launch.

## Key decisions

- Icons: the thing itself, modelled, then painted. The guide's halo never lies over the object, and every
  design sits inside the glow's circle (`frame` zoom).
- Prompts describe the look in plain words and never name a product (the legal lead's ask, c457cc9).
- Page pieces are reliefs at twice their shown size, with no paint-over on thin strips (it softens them).
  Nine-slice textures are periodic over exactly the repeat, so they need no blending.

## Notes for other areas

- UI design: the pieces above are ready to wire; margins in Next 3. crest_card stays on the choice and trait cards.
- ComfyUI is shared. Use `krea.i2i_many`, then `POST /free`. Never kill it.
