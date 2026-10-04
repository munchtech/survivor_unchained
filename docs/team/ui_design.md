# UI design (and the UI merge): status

Agent a5629aff0f215ea4a, branch `worktree-agent-a5629aff0f215ea4a` (includes the integration branch
at faabea9). Predecessors' handoffs: `docs/handoff/ui_design.md` (second design pass), `docs/handoff/ui_art.md`.

## Current state
- **UI merge** pushed (c14b3a2, a fast-forward for the integration branch); the painted art fills the
  redesign's layouts. 462 tests green.
- **The owner's answers, acted on**:
  - Pause: screens pause the world only in a fight (`zone.Combat`: arenas, the night's road); the pause
    menu always does.
  - Page or panel decided screen by screen (UI_DESIGN 6): the **pack is a right-hand panel** with the
    world in view, the thing read closely at the left, the camera stepping the survivor into the gap
    (`FollowCamera.ScreenShift`). Self, arts, journal, map, shop, storeroom stay full pages (reasons there).
  - Unwalked map land: the same sheet left blank and older (mottled, foxed, browning away from the
    known, faint rhumb lines), an ink wash with a tide line where the known ends, the sheet on a leather
    table with its shadow.
  - Self stays its own screen.
  - Painted art wherever better: every Ornate look gives way to its painted piece by name (plate, well,
    slab, crest_card, paper, banner), plus ribbon, plaque_rule, medallion ring, globe rim and glass.
- **Rebuilt into the house's language**: the chapter's end (the survivor's open book), the Wayfinder's
  table (map sheets in the painted wooden frames on his table, oaths as wax seals), the Last Lamp
  (three crested choices).
- Focus routes: `--navcheck` audits each screen when shot; every audited screen reaches everything.

## Key decisions
- The globe is the health; the painted health bar, casing and heart medal are not shown.
- Draft: the crested card's medallion and glow kept, worn by the painted card; words 40 px inside.
- The map stays full bleed; `map_frame` frames the Wayfinder's maps.
- The code draws only what changes in play (arcs, liquid levels, numbers, accents); the rest is paint.

## Next
1. Read the full shot pass `m8` (all screens, mouse and pad, with `--navcheck`) and fix what it shows.
2. Still in the old look: announcements (bare text over the world), the item card's own layout,
   the journal's deeds and codex inside the book; the dash pips and draught box on the HUD.
3. Re-make `docs/ui_review/` (before / first / second / third pass) once the above land.
4. UI_DESIGN section 10: the feel work's chest panel, text size, hold-to-read, accessibility.

## Notes for other areas
- UI art (a72467cac33063d3a): build on this branch; brief 4.9 lists every piece the layouts ask for.
- Shots: `--shot NAME --seconds S --navcheck` prints each open screen's focus audit as `nav ...`.
- The session scratchpad is shared between agents: mine is `scratchpad/uilead/`.
