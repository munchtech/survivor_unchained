# Crafting: status

Crafting lead, agent `a7862117a0240deb5`, branch `worktree-agent-a7862117a0240deb5`.
Research: `docs/CRAFTING_RESEARCH.md` (29 games, lessons C1–C30). Design:
`docs/CRAFTING_DESIGN.md` (numbered, sections 1–19).

## State (2026-10-04, stopped at the owner's usage limit)

**Phase 1, the forge's core loop: built, tested (492 green), and the game compiles. Not yet seen running.**
- **Data**: `data/content/crafting.json` holds every number: heat by rarity, the costs of temper, work in, cage, remake and rekindle, the materials and what each becomes, the crafters, and the night's yield. `old_iron` is in `items.json`; Brannoc sells 10 a restock; the wolfhide cloak is `workable`.
- **Logic**:
  - `Rpg/Crafting.cs`: quote, then do. Covers heat, seams, grades, every Brannoc verb, the three coals, break down, the night's yield and crafters' terms.
  - `Play/JourneyCrafting.cs`.
  - The pouch (`CharacterData.Materials`, read and written through `Inventory.Count/Take/AddToPack`, so the story's data is unchanged).
  - Heat on `Inventory.Make`, rolled ±20% on drops.
  - The pelt mark in `WorldTags`.
  - `Battle.ChampionsByFamily`.
  - The yield in `Arenas.Finish` (`ArenaResult.Carried/Spilled`).
  - Save version 3: materials move to the pouch and old gear gets heat.
  - Duplicate affix ids fixed: `of_the_root`, `of_the_brand`.
  - Brannoc's old `reforge` service is gone. His choice now reads "Can you work my gear?" and runs the `craft` action.
- **Interface** (built from my brief in the house style, for UI design to restyle):
  - `Ui/Forge.cs` (`ForgeScreen`, opened as `forge:brannoc`).
  - The item card shows grades, heat and open seams.
  - The pack's Materials filter shows the pouch, and the pack has Break down (asked twice).
  - The shop sells from the pouch.
  - The arena's end has "Carried out" and "Spilled".
  - An `iron` icon model.
- **Measured**: `tests/CraftingProbe.cs` (opt-in, `CRAFT_PROBE=1`) and its numbers are in design section 13.1.

## Next, in order

1. **See phase 1 running**, at full resolution, and shoot it:
   - `--quick warden --zone waystation --time day --open "talk:brannoc>work my gear>+"` and `--open forge:brannoc`, with `--items old_iron,wolf_pelt,...` for a stocked pouch;
   - the pack's Materials filter;
   - an arena's end (`--zone arena`), to see the carried-out line.
   Fix what looks wrong. A fresh survivor never set `met` for Brannoc until he is talked to, so test from his conversation.
2. **The economy simulation** (`CraftingEconomy` test, design 13.3–13.4): play Act 1's faucets day by day with a spender and check the targets.
3. **Phase 2**: Wenna's still-room (brewing, the flask, tinctures after the cure); commissions; the fang set and shed fur, with story's words.
4. **Phase 3**: Vonnra's binding; Snib's slurry; the seeds' lines.
5. Fill design section 19 with what was seen.

## Decisions (why in design section 17)

- **Heat** caps working one piece forever. Its cost is shown, and a craft never destroys the piece.
- **The forge's ceiling is a lucky drop's grade**: legendaries come only from drops, and the bright grade only from the slurry.
- **Work in makes answers; offensive affixes are only moved** (binding).
- **Three coals offered**, not one chosen, so the night keeps its planning.
- **The night pays at its end**, and a fall spills half. That gives the endless minutes a stake.
- **No crafting inside an arena**: the draft is the night's making.

## Agreed with others

- **Combat** (`ac4ec5bbd2763a0df`) said yes to every hook (design 12). Its fixes are built (`worktree-agent-ac4ec5bbd2763a0df@71608a4`, not yet merged here):
  - `MapRules.FodderGold = 0.02`;
  - gear only from carriers.
- **Miniboss ids** to wire into `night.peoples` (+2 material each, plus a rare drop of their own). All are `Elite`, `Miniboss`, `Loot = "miniboss"`, five a night plus two in the long push, and the harness reports `MinibossesMet` and `Minibosses`:
  - pack: `mb_old_tusk`, `mb_whitethroat`, `mb_blight_mother`, `mb_outflow_sow`, `mb_caller`;
  - dead: `mb_old_quarrel`, `mb_decurion`, `mb_the_heap`, `mb_drowned_reeve`, `mb_ford_bell`;
  - lamplings: `mb_wick_mother`, `mb_bombardier`, `mb_lamplighter`, `mb_fuse_boss`, `mb_gaffer`;
  - kerchiefs: `mb_firepot_nan`, `mb_pike_captain`, `mb_barn_door`, `mb_levy_sergeant`, `mb_drum_major`.
- **Story nights are now 20 minutes** and end at the boss. The yield already reads `spec.Minutes`; re-check the shard numbers with the new length.
- **Owed to combat: an answer on maps.** `SKILLS_DESIGN.md` §17 on its branch proposes a chart item: tier 1–16, a people, a seed, plain/fine/rare, mods that pay quantity and rarity, quality to 20. Crafting would roll, add, seal and remove mods and add quality, from the people's materials and heat; §17.5 pays materials per champion and miniboss. Read it, say what to change, and fold it into the design as a later phase. The experience lead owns the loop.
- **Story** (`a7622ae77d19e31dc`): not yet told. They need to approve or rewrite:
  - Brannoc's "Can you work my gear?";
  - his forge lines;
  - the history lines on remade and caged pieces;
  - the seeds in design 10.4;
  - Wenna's closed line in `crafting.json`.
- **UI design** (`ac76f400913a109cd`): the brief is design section 14, not yet sent.

## Notes for other areas

- `MapGenTests.A_map_can_be_walked...(seed: 7)` failed once under load and passed alone. It isn't mine; flag it if it recurs.
