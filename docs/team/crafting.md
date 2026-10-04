# Crafting: status

Crafting lead, agent `a97e32948c5bf419d`, branch `worktree-agent-a97e32948c5bf419d`
(successor to `a7862117a0240deb5`). Research: `docs/CRAFTING_RESEARCH.md` (lessons C1–C30).
Design: `docs/CRAFTING_DESIGN.md` (sections 1–20; 19 is what was seen, 20 the endgame).

## State (2026-10-04)

**Phase 1 is seen running and fixed** (design 19.1). Tests green (542).
- **The forge** (`src/Ui/Forge.cs`) works one seam at a time: grade badges, only the chosen
  seam's crafts, quiet reasons instead of red refusals, the whole piece's crafts as three tiles,
  a heat gauge that previews a craft's cost. Brannoc's terms are a ladder with the respect each
  asks; what he said over the last craft shows in his pane.
- **Lines** live in `crafting.json` (`crafters.<id>.lines`: greet, a verb's lines, `first.<verb>`
  with narration, `history.<verb>` templates). The story lead's rulings are in: "Will you work my
  gear?"; the first cage's narration and "Wants out. They all do."; a caged coal names its night
  (`shards.from`, set when an arena's shards are carried out).
- **Also fixed**: plurals for materials (`Items.Several`); a banked forge quotes but refuses; the
  arena's end shows carried and spilled materials as slots; old iron's icon remade.
- **Endgame designed** (design 20): the scars pay fire, the atlas pays iron and bases; two kits;
  item level and grade caps; marks (a proposal; not "sigils", which the canon keeps); chart verbs at Ysolde's table. Combat agreed
  chart heat and a pin, item level on map drops, map materials tallied like nights, two kits;
  marks await combat's successor's hook check.
- **The economy is simulated** (`tests/CraftingEconomy.cs`, design 19.2) on combat's post-cut
  numbers, and tuned: break down halved, a shard per 12 ember, remake to Epic 18 iron and 200
  gold, one remake a piece a day. Every target holds **if arena champions pay a tenth of the
  day's gold** (a Kerchief night still pays 2.5k–3.3k; asked of combat, not yet built).

## Next, in order

1. **Champion gold in arenas at a tenth**: combat's one line (`Rules.FodderGold`'s use in
   `Battle.KillEnemy`); combat's successor to build, or crafting with their yes.
2. **Phase 2**: Wenna's still-room (brewing, the flask, tinctures after the cure), commissions,
   the fang set and shed fur. The story lead writes the lines once told the hooks (sent).
3. **Phase 3**: Vonnra's binding, Snib's slurry. Asked the story lead whether Vonnra's role moves.
4. **Endgame builds** (design 20.6), after combat's chart item and map loot exist.
5. Still to see: the forge after a craft (Brannoc's line, the gauge after), pack break down by mouse.

## Decisions (why in design section 17)

- **Heat** caps working one piece forever; its cost is shown; a craft never destroys the piece.
- **The forge's ceiling is a lucky drop's grade**; legendaries only from drops; bright only from slurry.
- **Work in makes answers; offensive affixes are only moved** (binding).
- **Three coals offered**, not one chosen, so the night keeps its planning.
- **The night pays at its end, and a fall spills half** (owner approved).
- **Remake costs old iron as well as gold** (owner approved).
- **The anvil works one seam at a time**: all crafts at once was a wall of refusals.
- **One remake a piece a day**: iron cools overnight; spreads the weapon's climb over days.
- **The scars pay fire, the atlas pays iron**: each arena supplies the other's crafts.

## Agreed with others

- **Combat** (`ac4ec5bbd2763a0df`): every hook (design 12); fodder gold 2% and carrier-only gear
  are built. Sent: the endgame asks (chart heat and pin, item level, marks, map material tally,
  two kits) and a request for post-cut gold and gear per night.
- **Story** (`a035208561a66c171`): rulings applied; my placeholder lines for Brannoc are in
  `crafting.json` for their approval; the fang set, shed fur and Wenna's hooks are sent.
- **UI design**: the forge brief is in `docs/handoff/ui_design.md` §4 item 7 for their successor.

## Notes for other areas

- **Tools for pictures**: `--items A*N` gives a stack, `--gold N`, `--anvil DEF` puts that piece on
  the forge's anvil, `--focus ID` (with `--pad`) gives a forge control the focus (`temper`,
  `remake`, `seam:1`, `coal:0`), `--open result --fell` shows a fallen night's spill.
- **A worktree runs the game** once `godot/assets` is a junction to the main checkout's
  `public/assets` (skip-worktree set), the main `godot/.godot` is copied in, and untracked art is
  copied from the main `godot/art` (never commit those).
