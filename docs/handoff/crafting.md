# Crafting: handoff

For the next crafting lead. Read these in order:
1. `docs/team/README.md`: the owner's bar, how we work, heavy work by turns.
2. This page.
3. `docs/team/crafting.md`: the one-page status.
4. `docs/CRAFTING_DESIGN.md`: section 17 is the decisions (1–30), 19 what was seen and measured (19.4 is
   phase 3), 20 the endgame (20.7 is what was built).

The research is `docs/CRAFTING_RESEARCH.md` (C1–C30).

## The owner, in their words

- "AAA standard", "strive for excellent, above and beyond - not just good enough".
- "I don't want to polish, I want to create perfection."
- "We are striving for perfection." Before you show anything, ask whether it is the best version of this in any game. Root
  design in research on how the best games solve it, then make it ours.
- The owner rejected heavy borders on every box and "ai looking" screens: UI design is redoing the layouts from research.
- "Do we have soul?"
- "end game is two types of arenas - permanent and our normal arenas. permanent is our arpg build maps like poe
  and the normal arenas are for mindless survivors fun." These are the Wayfinder's atlas and the ember scars.
- Decided:
  - the weapon upgrade (Remake) costs old iron;
  - falling after the half-hour spills half the materials;
  - full-page screens pause only in arenas;
  - two endgame arena types;
  - Rook's storeroom grows by bought shelves of 24;
  - the bench becomes two panels with the smith live in the world between them.

## Your brief

Crafting lead: research, design and build crafting, playable end to end, and seen in the running game at
1920×1080.
- It serves the story's early share (crafters are people; crafts open by story), the scars (fire) and the atlas
  (iron, gold and gear).
- Don't stop to ask. Keep `dotnet test` in `godot/tests` green. Use British spelling and short "why" comments.
- Commit and push your own branch at milestones (the main session merges; no PRs).
- Take a turn for Godot and the GPU (`tools/turn.py`). Hand off past about 500k tokens of context.

## Done (this lead, `af01b0d61ef656dd4`)

- **Phase 3 seen and remade** (design 19.4):
  - **Vonnra's table:** the column fits her long name; her words sit under her; bind cards give the grade and its source.
  - **Snib's bench:** Snib drawn as his lampling (`Portrait.Of(Beasts.Def)`, `BeastPose`); the odds as a bar
    (`ForgeScreen.SlurryOdds`, shared with the pack); "What the jar did" said plainly.
  - **A steeped piece:** veins shown by a shader on the picture (`ItemViews.Steeped`); no heat back. The bright grade
    reads as light.
  - **Commissions:** the "!" stands clear of a two-line plate (`Voices.cs`); the hand-over rings in gold; Brannoc's
    "Cooled overnight".
  - **The moments:** lamp-light motes for a binding, green bubbles for a steep, violet for a mark, ink motes for charts.
- **Hold to confirm:** `Style.HoldButton`, built to UI design's spec (0.8 s, drains, a tap nudges). It is used for
  unmake, steep and break down, at the bench and in the pack.
- **The slurry's "up"** always lands past the cap (decision 30).
- **Endgame** (design 20.7):
  - Marks (`Crafting.Inscribe`, `RulerMark`, `Kit.Marks`).
  - Charts (`CraftingCharts.cs`; the bench page with charts; the table's "Work it first").
  - Item level (`FinerGrade`; the loot lead owns it now).
  - The scars' depth and scar-glass (`Crafting.Night`, `SteepWith`).
  - Rook's shelves (`ShelfPrice`, `BuyShelf`, `ShelfSaid`).
  - Minibosses' material.
- **Icons:** painted through UI art's pipeline (`tools/uiforge/items.py`): slurry_jar, hunt_bone, lamp_glass,
  gate_nail, red_cord. UI art wrote their imports.
- **The economy measured against the loot lead's fewer drops** (`CraftingEconomy`, swept with ECON_MAT, ECON_IRON,
  ECON_BOSS).
- **All the story lead's words wired verbatim:** Ysolde, the four things, the marks' names, scar-glass, Rook's
  shelves, Snib's bad jar, and Brannoc.

## Next, in order

1. **UI art's repaints** of red_cord and lamp_glass (plus the flask, and scar_glass if added). Take their PNGs,
   prompt lines and PICKS into `tools/uiforge/items.py` and `godot/art/ui/icons/item`.
2. **The two-panel bench and two kits**, once UI design's successor builds the greybox (owner-approved). Content
   agreed:
   - the person as a strip;
   - cards in two columns scrolling down;
   - Snib's odds inside the Steep card;
   - first-time narration up to about seven lines.
   Then the two kits (design 20.2), which wait on their new pack.
3. **See:** the scars' depth and scar-glass at a night's end; Rook's line over a shelf sold.
4. **Legendary break down** (5 iron and 3 shards) once the loot lead's Legendaries land.
5. **Re-measure in the atlas:** map gold against shelf prices and chart costs, when a map probe exists.

## Decisions (each with its why in design 17 and 20.7)

- Phase 3 (24–30): binding moves plain powers only, and only from the pack; steeping by hand too; the slurry's
  fourth power; Vonnra after the toll; a steeped piece takes no heat back; "up" always past the cap.
- **Marks** take a seam, one to a piece, three worn. They come at the grade they fell at; no forge tempers them.
- **Charts** have heat (plain 4, fine 6, rare 8). Their materials are the two arenas' own.
- **Night materials** are tallied at the end, never dropped (decision 7). Loot's arena drops feed the tally.
- **Shelves:** the second costs about a Kerchief night's gold (Act 1 earns about 1,600). The later ones are the
  atlas's sinks.
- **Hold to confirm**, never a second dialog. It is UI design's rule for every screen.
- **Endgame order:** crafting's own first; kits wait for UI design's pack.

## Failures and why

- I ran ComfyUI once before the turns rule existed. Since then, take a turn first, and give it back at once.
- The first steep "up" only added a grade: on an unfinished piece it was a dud that cost all its heat. Fixed:
  decision 30.
- Vonnra's long name widened her column past its rail. Fit plaques to the column (`NamePlaque`).
- A drawn vein overlay looked stuck on (green twigs). It is now a shader on the picture's own pixels.
- The first mark ids clashed: of_the_gyre was already the Axe Gyre suffix (CraftingTests.Every_affix_id_is_its_own).
- I first asked loot for 1 material and iron at 50% per non-gear roll without measuring. The sweep showed
  materials piling up (166 unspent). Measure before asking.
- A headless `--import` in this worktree segfaulted at 1%. I reverted its strays with `scratchpad/craft3/revert_imports.py`.
  UI art writes .import files by hand when no Godot turn is free.

## Gotchas

- **Running from a worktree:**
  - `godot/assets` is a junction to the main checkout's `public/assets` (skip-worktree).
  - Copy the main `godot/.godot` in, and copy untracked `.import` files from the main `godot/art`.
  - Run `dotnet build` before every run.
- **Play script:** `scratchpad/craft3/play.py NAME --timeout S -- [game args]`, with `crop.py` and `sheet.py` beside it.
  - The game runs on a shared machine: RAM can run out and crash a capture. Retry once.
  - The worktree guard refuses heredocs and complex shell. Write Python edit scripts with the Write tool
    (`ed.py` `sub()` keeps CRLF; `cut.py`), and run them plainly.
- **Turns:** `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot|gpu "crafting: job"`.
  `--wait N` waits N minutes; run it in the background. `give` it back the moment you're done.
- **The bench's arguments:**
  - `--open forge:ID` opens any bench (`forge:wayfinder` with `--charts N`);
  - `--anvil DEF`, `--focus`, `--make`, `--pattern`;
  - `--clicks hX:Y` holds a press for a second;
  - `--near ID`;
  - `--items DEF:RARITY:AFFIX@G+..:MARK`.
  Button positions move when card text changes: shoot once, then click.
- **Data:** `crafting.json` is hand-laid; edit it as text. A `_note` key inside `crafters` breaks the parse.
- **Merging:** the loot lead's tally block in `Arenas.Finish` goes after the `Crafting.Night` call (mine passes
  minibosses and the cure).

## Collaborators (the roster in `docs/team/README.md`)

- **UI design** (`aab47bfdab5955dac`, handed off): the greybox bench and shelf pages go to their successor.
- **UI art** (`aa9c11f1e40170a4d`): icons judged; repaints pending.
- **Story** (`a7ba8903f4c8261b1`): all asks answered.
- **Combat** (`afe45df4957917614`): marks' behaviours and numbers; maps.
- **Loot** (`a9a9c345a35e1fcad`): the satchel, item level, drops (`docs/design/LOOT_DESIGN.md`).
- **Experience** (`ab406cf9ddd22b03b`): the atlas's and scars' loops.

## Files to read first

- Status and design: `docs/team/crafting.md`; `docs/CRAFTING_DESIGN.md` (17, 19.4, 20.7).
- Logic: `godot/logic/Rpg/Crafting.cs`, `godot/logic/Rpg/CraftingCharts.cs`, `godot/data/content/crafting.json`.
- UI: `godot/src/Ui/Forge.cs` (benches, marks, charts, slurry odds, moments), `godot/src/Ui/Style.cs` (HoldButton),
  `godot/src/Ui/Portrait.cs` (BeastPose).
- Tests: `godot/tests/CraftersTests.cs`, `godot/tests/CraftingEconomy.cs`.
