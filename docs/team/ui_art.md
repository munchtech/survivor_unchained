# UI art: status

Agent aa9c11f1e40170a4d (successor to a1a394643aabfb169). Branch `worktree-agent-aa9c11f1e40170a4d`.
Full brief and history: `docs/handoff/ui_art.md`. One rebuild: `python tools/uiforge/build.py`.

## State (2026-10-04)

- **The owner's verdict changed the direction.** "Those borders are just ugly, adding more of them
  doesn't make them better"; the pages look "ai looking", "not rooted in ui research". The arena (draft)
  cards "look pretty cool": keep them.
- **New rule (coordinator):** at most one ornamental frame per screen, the outer window. Inside it go
  quiet tonal panels, thin rules and recessed tiles for empty slots. Rarity colour goes only on filled
  slots. Ember is the one accent, used for meaning.
- **The reduced kit is built, not applied** (`tools/uiforge/kit.py`, 5b815c9d). It holds a raised tonal
  panel, a recessed tile, a shade-only column, a thin gutter rule, and the header and foot band worn plain.
  The before/after crop of Self went to the coordinator: `godot/.shots/kit_crop_self.png` (ignored).
- **In the game now** (4d366b5a, 859d5bfc):
  - the gilt morocco header and foot band;
  - the black vellum ground;
  - the cubic-read, cool-graded backdrop shader;
  - gilt-ruled columns;
  - the hero plate and the light card;
  - the ember low at the page's foot.
  The kit replaces most of the ornament once applied. The vellum, the shader and the low ember stay.
- **The crafting lead's three icons** were refitted to the set's 0.82 fill. The flask still wants a repaint.

## Next (exact)

1. Wait for the greybox layouts. The UI design lead aab47bfdab5955dac is redoing Self, Pack, Storeroom and
   Trader from research. Art goes on them only once the coordinator and the owner approve.
2. Meanwhile, finish the kit and keep it quiet. The coordinator found the panels "plain to a fault":
   flat dark rectangles read as a generic web dark mode. Give them the world through material, not frames:
   - a faint grain of vellum or leather inside each panel, at 1:1 (tiled, not stretched);
   - worn light along the top edge;
   - a warmer, more varied tone than the page.
   Then, in the same restraint:
   - the medallion rings (`medallion/ring.png`, the attribute and level medals) pared to a plain ring;
   - tabs, buttons and keycaps as tonal plates;
   - the Pack's side panel as the screen's one outer frame (worn iron or leather, not filigree);
   - the slots: an empty slot is a recessed tile, and a filled one carries its rarity colour.
3. Then apply the kit (`python tools/uiforge/kit.py --apply`), shoot the four screens at 1080 and 1440,
   and send before/after.
4. Crashing Leap: a second concept is drafted (`emblems.d_leap2`, not painted). Its guide still fogs: cut
   the halo and the light fan and keep dark slabs against the burst.
5. The flask repaint (warm light, no stamped mark), then the legal lead's pre-launch icon check.

## Key decisions

- One frame per screen; the material carries the page, not ornament (the owner's verdict above).
- The page's ground is black vellum, the world faint through it. The blur alone was low in definition and
  brown.
- The backdrop shader reads its mips through a cubic B-spline (smooth) and grades cool iron, warm only where lit.
- Heavy jobs take a turn (`tools/turn.py take gpu|godot`), given back the moment they end.

## Notes for other areas

- UI design: the column ruling, Backdrop(page: true) and the vellum are approved and wired (a26f87c39952dcd9c).
  The kit swaps art by the same names, so applying it needs no code.
- ComfyUI is shared and memory is tight: Godot imports and Blender renders crashed when other jobs held 30+ GB.
