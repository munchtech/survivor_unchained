# UI design: status

Agent aab47bfdab5955dac (handing off), on branch `worktree-agent-aab47bfdab5955dac`, which has the integration branch merged. The full brief for a successor is in `docs/handoff/ui_design.md`.

## Current state
- **Layouts approved by the owner** ("the ui layouts look better"). They were revised for no dead space.
  - Research: `docs/design/UI_RESEARCH.md`.
  - Greyboxes: `docs/ui_review/greybox/`, drawn by `python tools/uigreybox/screens.py OUTDIR`.
  - Nothing is built in the game yet. That's next.
- **Seen in the game at 1920x1080 and fixed:**
  - the Look's face light (portrait rig, `GameFront.PortraitLight`);
  - the pack's swap flash;
  - the arena cards' centring;
  - the licences index (legal passed the screen);
  - the day clock's words, its key and the dawn fade;
  - a slim scroll bar on every screen (`Style.PageTheme`), and `FadeEnds` for long readings.
- **Seen and still poor** (fold into the build):
  - the map result: two big half-empty boxes, and its telling runs past 9 s;
  - the Wayfinder's table and atlas: an old iron plate with the HUD showing round it, and the atlas page's "used up" line clipped;
  - Self, Pack, Forge: dead space, which the approved layouts answer.

## Next
1. Build the approved layouts in the game with plain tonal styles, calling UI art's frame names: Self, Pack (with the stores tabs), Storeroom (shelves: crafting's logic is at af01b0d61ef656dd4@012403dd), Trader, and the bench (two panels, smith in the world).
2. Experience's asks (ab406cf9ddd22b03b): the day dial by the zone name, and the fall's two choices as a held moment, not the use-key prompt.
3. The map result and the table/atlas, in the same restraint.
4. Heroine portraits after her new head (`heroine_paint.py`, `creation_portraits.py`); the male hero's Look with ab82cbe99e2937ddd.

## Key decisions
- **One frame per screen.** Inside it: tone, spacing, type and rules. Colour is rarity, state, or the one primary action.
- **Panels hug their contents.** A surface that must run on tapers into the world behind it.
- **Counters are two fitted panels**, theirs left and yours right, with the keeper live in the world between them.
- **No inspect panels.** A hover or focus card opens on the world side, with the worn piece beside it.
- **Irreversible acts are held.** Crafting built `Style.HoldButton`.
- **Portrait light only at head and shoulders and nearer.** The fire reaches her through a stand-in light, so the camp keeps its light.

## Notes for other areas
- **Everyone:** the game's Alegreya Sans has no →, ←, ▲ or ● glyphs. Use Alegreya (serif) or draw them.
- **Loot lead (a9a9c345a35e1fcad):** the stores (pouch, satchel, key ring) are tabs over one row in the Pack and at every counter. The filter sits beside Sort.
- **UI art (a0bff3ffe4d3ad748):** needs a taper (the side panel and page ground fading at the foot), tab_hover and tab_pressed, and chains used with purpose.
