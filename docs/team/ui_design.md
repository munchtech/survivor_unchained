# UI design (and the UI merge): status

Agent a5629aff0f215ea4a, branch `worktree-agent-a5629aff0f215ea4a`. Predecessors' handoffs:
`docs/handoff/ui_design.md` (the second design pass) and `docs/handoff/ui_art.md` (the art pass).

## Current state
- **The UI merge is in and pushed**: the integration branch, then the second design pass, then the
  art pass, reconciled so the painted art fills the new layouts (decisions below). 456 tests green.
- Shot at 1920x1080 (mouse and pad): every screen once after the merge (m1); after the fixes, map,
  Verge map, draft, creation, title, journal, people, arts, skills, pause (m2), and HUD, pack, self,
  map, draft, talk, shop, storeroom, creation with `--navcheck` (m3, stopped at the usage limit).
  Every audited screen reaches all its focusable things; none off screen. Not re-shot after the
  fixes: result, rest, table, chapter (unchanged by them).
- Stopped at the owner's usage limit. In hand, not committed: the chapter's end rebuilt as the
  survivor's open book (script kept in the shared scratchpad, `uilead/chapter.py`; unverified).
- Fixed: the Verge map's view past the zone's edge (pan held so the paper covers the view), the
  unwalked dark letting the ink through (now opaque, one dark with past the paper), ink hanging
  past the paper, Self's standing dropping out of pad focus after a + was focused, draft text on
  the painted card's iron, slot captions on the painted well's lip, the title's broken rule.
- Registered for paint: `well`, `slab`, `header`, `banner`, `pillar`, `console`, `book/open.png`,
  `medallion/ring.png`, `hud/globe_rim.png`, `hud/globe_glass.png` (`UI_ART_BRIEF.md` 4.9,
  `tools/comfy/ui_assets.json`).

## Key decisions
- The globe stays the health; the painted health bar, its casing and the heart medal belonged to the
  old corner and are not shown (the console HUD is the redesign's choice, Diablo IV's band).
- Draft: the crested card's medallion and glow stay, worn by the painted card; words keep 40 px in.
- The map stays full bleed; the painted wooden map frame goes to the Wayfinder's table's maps.
- The creation and pause columns wear the painted plate (one iron for every reading surface).
- Medallions and the globe take painted rings by name, keeping the code's colour, arc and number.
- Focus is audited by the game (`Nav.Audit`, `--navcheck`), not by eye alone.

## Next
1. Finish the m3 pass (result, rest, table, chapter, journal, arts, pause with `--navcheck`).
2. Bring the rest into the language: the chapter's end as the open book (left leaf what was done
   and what waits, right leaf who remembers and the tally on medallions); the Wayfinder's table as
   three maps in the painted wooden map frame on a table; the Last Lamp; the item card/tooltip;
   toasts, hint, announcements, boss bar; journal deeds/codex. (Buttons and tabs are painted now.)
3. Re-make `docs/ui_review/` once those land.
4. Section 10 of `UI_DESIGN.md` (feel work's chest panel, text size, hold-to-read, accessibility).

## Open questions for the owner
1. The health globe by day too, or a quieter bar at peace? (Now: the globe in the corner at peace.)
2. Should full pages pause the world? (They hide the HUD; the world runs.)
3. Unwalked map land: dark (now) or blank parchment?
4. Self and Pack both show the survivor large: keep both, or Self as a tab of the pack's left pane?
5. Painted art for every frame, or drawn frames where they read well and paint for ornaments?

## Notes for other areas
- UI art (a72467cac33063d3a): build on this branch; 4.9 of the brief lists what the layouts ask for.
- Shots: `--shot NAME --seconds S --navcheck` prints each open screen's focus audit as `nav ...`.
