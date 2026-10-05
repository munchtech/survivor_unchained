# Crafting: status

Crafting lead, agent `af01b0d61ef656dd4` (handed off: `docs/handoff/crafting.md`), branch `worktree-agent-af01b0d61ef656dd4`
(successor to `a7debf1459f14dfe7`). Research: `docs/CRAFTING_RESEARCH.md` (C1–C30).
Design: `docs/CRAFTING_DESIGN.md` (19.4 is phase 3 as seen; 20.7 is the endgame as built).

## State (2026-10-05)

Phases 1–3 are built and seen at 1920×1080; phase 3 was remade where it fell short (design 19.4). The
endgame's crafting is built. Marks, the chart bench, hold presses and shelves are seen; the scars' depth is
not. Tests green (715, after merging the integration branch with the loot lead's work).

**Endgame** (design 20.7):
- **Marks:** rulers leave their people's thing (now in the loot lead's satchel); Vonnra inscribes it; three
  worn in maps.
- **Charts** (Ysolde's table): ink, burn and redraw, pin, scrape, annotate. Charts have heat.
- **Item level:** map gear rolls its finer grade more often. The loot lead owns item level now and builds on it.
- **The scars' depth:** a shard a minute past thirty minutes beyond the win; scar-glass past the hour once the
  stream is cured.
- **Rook's shelves** of 24: 300, 1,000 and 2,500 gold, then 5,000, to eight.
- **Minibosses** carry out two of their people's material.

**Also:**
- Hold to confirm (`Style.HoldButton`) for unmake, steep and break down.
- Painted icons for the slurry jar and the four rulers' things. UI art agreed three and is repainting
  red_cord and lamp_glass.

## Next, in order

1. **UI art** (`aa9c11f1e40170a4d`) is repainting red_cord and lamp_glass (and asked to add scar_glass).
   - Take their PNGs, prompt lines and PICKS into `tools/uiforge/items.py` and `godot/art/ui/icons/item`.
   - They also send the flask's prompt line and pick.
   - Then point scar_glass at its icon (it is already keyed "scar_glass").
2. **Two kits**, with UI design's new pack (their successor builds the shelf pages and the two-panel bench from
   the greybox). Fit the bench's content to the two-panel layout. Agreed so far:
   - the person as a strip;
   - cards in two columns that scroll down;
   - Snib's odds inside the Steep card;
   - narration up to about seven lines for the first time each craft is done.
3. **See in the game:** the scars' depth and scar-glass (`--zone arena --minute 95 --won` with
   `--facts stream.clear=true`), and Rook's line over a shelf sold.
4. Break down a Legendary for 5 iron and 3 shards, once the loot lead's Legendaries are in.
5. Re-measure the economy in the atlas once combat or loot has a map gold probe.

## Decisions (why in design 17, 20.7)

- 1–30 as written in design 17. They include:
  - remake costs iron, and a fall spills half (both the owner's);
  - a steeped piece takes no heat back;
  - "up" always lands past the cap.
- Marks take a seam (the support-gem trade): one to a piece, three worn, never tempered.
- Charts have heat. Their materials are the two arenas' own.
- Night materials are tallied at the end, never dropped (decision 7). The loot lead's arena drops go into the tally.
- The endgame's order: crafting's own first (marks, charts, item level, scars). Kits wait for UI design's pack.

## Agreed with others

- **UI design** (`aab47bfdab5955dac`, handed off; a successor builds the greyboxes):
  - hold-to-confirm, built by me to their spec;
  - the two-panel bench (owner-approved);
  - the shelf pages are theirs, the shelf logic mine.
- **Story** (`a7ba8903f4c8261b1`): every ask answered and wired verbatim.
- **Combat** (`afe45df4957917614`):
  - the marks' ids (of_the_long_chase, of_the_muster);
  - the ruler's mark drop and Chart.Pinned;
  - they raised the marks' floors, and the item texts match.
- **Loot** (`a9a9c345a35e1fcad`):
  - the satchel for marks and charts;
  - item level is theirs;
  - non-gear rolls give material 10% and iron 20%, and the boss 1, into the night's tally (measured,
    `CraftingEconomy`).
- **UI art** (`aa9c11f1e40170a4d`): the five icons judged; three agreed.

## Notes for other areas

- **Pictures:**
  - `--items DEF:RARITY:AFFIX@GRADE+...:MARKS` (e.g. `:slurried`);
  - `--near ID`;
  - `--clicks hX:Y` holds a press for a second;
  - `--open forge:wayfinder` with `--charts N`.
- Vonnra's model reads as a placeholder in the bench portrait.
- A bark draws over the speaker's name plate.
