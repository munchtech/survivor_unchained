# UI design: status

Agent aa1f430bd64b8d1ce, on branch `worktree-agent-aa1f430bd64b8d1ce` (integration merged). Pictures: `docs/ui_review/build8/` (latest), build7 and earlier before it.

## Current state (built, seen at 1080; creation, pause and rest at 1440 too)
- **Creation** (build8/1 to 12): two mirrored 560 px panels, her in the middle of the screen between them, the fire at her right hand in view.
  - Left: the steps on the chain (the heated link under the step; `[` and `]` at its ends), the step's question as the title, the choices as lines of type (line glyph, name, what it is; the taken one marked with the ember diamond), the way on as words with their keys.
  - Right: what the choice means; a calling's numbers as a ledger line.
  - Her name and what she is, as lettering on the ground at her feet (hidden on the Look, which is near her face).
  - The Look's parts as the house's tabs; cameos and beads in centred rows; the face's groups, palettes, cuts and hood as words.
- **Pause** (13 to 15): a fitted panel at the left; where you stand, the menu as a centred block, the book's tabs on their chain (cold: no tab open). Settings and controls open in a panel beside it, rows as words. The HUD steps away, as the book does.
- **The Last Lamp** (16 to 18): a held moment in type, as the fall's choices are: the lamp's name and Rook's question over her head, the three choices under her feet (1, 2, 3; Esc is "not yet"), the lamp's warmth breathing behind the first; refused, the price in red and why. The morning is told the same way.
- **Chapter** (19): the 1440 book hugs its writing (measured until it holds). The past on the left (what was done, what the world says, the tally as a ledger line), what goes on on the right (who remembers you, what still waits). A name's word sits after it, never in a far column. The way on as words, mirrored about the middle.
- **Credits** (20): checked at 1:1; its slab and button and the licence's seal lost their boxes.
- **The title's panels and the adults' notice** (21 to 23): fitted panels, words for buttons.
- Earlier passes (results, the fall, the Journal, the map, notices) as build7 shows.

## Next
1. **Portraits** when the face lead messages: `python tools/assets/heroine_paint.py brows`, then `python tools/assets/creation_portraits.py` (a Godot turn), then shoot the Look (build8/2 to 6). Three faces have no cameo yet (Sunborn, Moonlit, Saffron: build8/3).
2. The male Look's portrait and cameos wait for the male hero lead (build8/10, 11: a glyph stands in).

## Key decisions
- One frame per screen; inside it only type, rules and space. Colour means tier, state or the one action.
- No boxes, no fades: panels hug their content and end cleanly; the ground is slightly see-through.
- Creation is symmetric: two panels of one width, the figure in the middle (`GameFront.DressFigure` stands her where the camera looks).
- The chain is the book's tabs wherever they are (the book's panel, the pause, creation's steps); a title beside a chain has none of its own.
- A held moment (the fall, the lamp, the morning) is type on the world over and under her, never a plate.
- A row of drawn glyphs is drawn in one hand (`Glyphs.Icon(..., line: true)`): the painted set mixes full colour and line.
- Before sending anything: a strict self-critique at 1:1 (dead space, grid, symmetry, boxes, fades, type, placeholders).

## Notes for other areas
- **UI art (paused):** `book/ribbon.png` is no longer used (the Journal's sections are type). The map's drawing is soft at the zoom it now opens at (the roads' checker shows); the houses are flat hexagons. The calling and art glyphs' painted set is a mix of full colour (shield, moon, hourglass) and white line; creation now draws them as lines.
- **The face lead:** `CreateLook.cs` changed in presentation only (the frame, heads, tabs, words for segments, centred rows); what is offered is untouched. The property `Kit` is now `Hero`.
- **Developer switches added:** `--sex male` (creation on a man), `--panel load|settings|controls` (the title on a panel), `--adults` (the notice; never written back). `--keys` stops after its first press while the world is paused: use `--clicks` (one) there.
