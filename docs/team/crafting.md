# Crafting: status

Crafting lead, agent `af01b0d61ef656dd4`, branch `worktree-agent-af01b0d61ef656dd4` (successor to `a7debf1459f14dfe7`;
handoff from before: `docs/handoff/crafting.md`). Research: `docs/CRAFTING_RESEARCH.md` (C1–C30).
Design: `docs/CRAFTING_DESIGN.md` (19.4 is phase 3 as seen; 20.7 is the endgame as built).

## State (2026-10-04)

Phases 1–3 are built. Phase 3 has been seen at 1920×1080 and remade where it fell short (design 19.4). The endgame's
crafting is built in code and tests, but not yet seen. Tests green (671).
- **Phase 3, seen and remade:**
  - Vonnra's table: the column fits her name, and her words sit under her.
  - Bind cards give the grade and where it comes from. A binding rings its seam with lamp-light.
  - Snib's bench: Snib is drawn as his lampling. The odds are a bar showing what each outcome would mean for
    this piece, and what the jar did is said plainly.
  - A steeped piece shows its veins everywhere (a shader) and takes no more heat. The bright grade reads as light.
  - The commission's "!" stands clear of the name plate.
- **Hold to confirm** (`Style.HoldButton`, built for UI design's rule): unmake, steep and break down are held for
  0.8 s, never asked twice.
- **The slurry's "up"** always lands past the forge's cap (decision 30).
- **Endgame** (design 20.7):
  - Marks: rulers leave their people's thing; Vonnra inscribes it; three are worn in maps.
  - Chart verbs at the Wayfinder's table: ink, burn and redraw, pin, scrape, annotate; charts have heat.
  - Rook's shelves of 24: 300, 1,000 and 2,500 gold, then 5,000 each, to eight.
  - The story lead's words are wired verbatim (Ysolde, the four things, Brannoc's "Cooled overnight", Snib's bad jar).

## Next, in order

1. **When Godot and the GPU are free** (take a turn: `tools/turn.py`):
   - Paint the icons for the slurry jar and the four rulers' things. Prompts are in `tools/uiforge/items.py` T2I
     (`krea.t2i_many`, then `items.fit`). Agree them with UI art (`aa9c11f1e40170a4d`), then point the items at
     the new keys.
   - Import this worktree's new art (moon_draught, flask fail to load here), then revert stray `.import` files.
   - See the hold presses, Vonnra's marks, the chart bench and Rook's shelves at 1920×1080.
2. **Item level** on map gear, with better grade odds the higher the map (design 20.6, 3).
3. **Two kits**, with UI design's new pack.
4. When UI design's bench greybox is approved and built, fit the content to it. Agreed so far:
   - the person as a strip;
   - cards in two columns that scroll down;
   - Snib's odds inside the Steep card;
   - narration up to about seven lines for the first time each craft is done.

## Decisions (why in design 17 and 20.7)

- 1–23 as before: heat; the forge's ceiling; three coals; remake costs iron (owner); a fall spills half (owner); etc.
- 24–30, phase 3:
  - binding moves plain powers only, from the pack;
  - steeping by hand too;
  - the slurry's fourth power;
  - Vonnra after the toll;
  - a steeped piece takes no heat back;
  - "up" always past the cap.
- Marks take a seam (the support-gem trade). One to a piece, three worn. No forge tempers them.
- Charts have heat, and their materials are the two arenas' own: shards from the scars, iron and the people's
  material from the atlas.
- Endgame order: crafting's own first (marks, charts). Kits wait for UI design's pack.

## Agreed with others

- **UI design** (`aab47bfdab5955dac`):
  - hold-to-confirm, which I built;
  - the bench becomes two panels with the smith live between them (owner-approved), which they build;
  - shelves: the logic is mine, the pages theirs.
- **Story** (`a7ba8903f4c8261b1`): all five asks answered and wired.
- **Combat** (`afe45df4957917614`), told:
  - Marks.Gyre's id clashed with the of_the_gyre skill suffix (now of_the_muster), and Ravine's is now of_the_long_chase;
  - a ruler's mark drop in MapRun;
  - Chart.Pinned;
  - chart heat in GiveChart;
  - asked to check the marks' numbers at tier 1.

## Notes for other areas

- **Pictures:**
  - `--items DEF:RARITY:AFFIX@GRADE+...:MARKS` (a fourth part marks it, e.g. `:slurried`, which also sets it);
  - `--near ID` stands her by a person;
  - `--focus`, `--make`, `--pattern`, `--anvil` as before.
- **Owed by others:** Vonnra's model reads as a placeholder in the bench portrait (a lavender hood, a flat orange top).
- A bark draws over the speaker's name plate (Brannoc's "Hit a man with this..."): for UI design or the HUD.
