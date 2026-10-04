# Crafting: handoff

For the next crafting lead. Read `docs/team/README.md` first (the owner's bar, how we work),
then this, then `docs/team/crafting.md` (one-page status), then `docs/CRAFTING_DESIGN.md`
(sections 1–20; 19 is what was seen and measured, 20 the endgame). The research is
`docs/CRAFTING_RESEARCH.md` (lessons C1–C30, cited in the design).

## The owner, in their words

- "AAA standard", "strive for excellent, above and beyond - not just good enough".
- "I don't want to polish, I want to create perfection." Remake rather than patch.
- "Do we have soul?" Make it this valley's, not generic.
- "end game is two types of arenas - permanent and our normal arenas. permanent is our arpg
  build maps like poe and the normal arenas are for mindless survivors fun." The bible names
  them the Wayfinder's atlas (kept by Ysolde) and the scars.
- Story is about 40% of the game early on. The endless phase is truly endless.
- Approved (October 2026): the weapon's upgrade (Remake) costs old iron as well as gold;
  falling after the half-hour win spills half the night's materials.

## Your brief

Crafting lead: research, design and build crafting, playable end to end and seen in the running
game at full resolution. It must serve the story's early share (crafters are people, crafts open
by story), the scars (survivors runs) and the atlas (build maps, with build depth). Don't stop to
ask. Keep tests green (`dotnet test` in `godot/tests`), British spelling, commit and push your
branch at milestones (the main session merges), hand off past about 500k context.

## Done

- **Phase 1** (by the first lead, `a7862117a0240deb5`): `Rpg/Crafting.cs` (quote, then do: heat,
  seams, grades, temper, work in, cage, remake, rekindle, break down, the night's yield, terms),
  `crafting.json` (every number), the pouch, heat on drops, save version 3, `Arenas.Finish`'s yield.
- **Seen and fixed** (me; design 19.1): the forge rebuilt to work one seam at a time
  (`src/Ui/Forge.cs`: `GradeBadge`, `HeatGauge` with a craft's cost previewed, three tiles for the
  whole piece, Brannoc's terms as a ladder, what he says); plurals (`Items.Several`); a banked
  forge quotes but refuses; the arena's end shows carried and spilled as slots
  (`ArenaResult.Haul`); old iron's icon remade (`ItemModels.OldIron`, a `Rust` texture).
- **Lines**: crafters' lines are data, `crafting.json` `crafters.<id>.lines` (greet; a verb's key;
  `first.<verb>` with `.before`/`.after` narration; `history.<verb>` with `{who}`, `{day}`,
  `{night}`). `Crafting.Speak` picks them; `Journey.CraftSaid` holds the last; the forge shows it.
  A caged coal names its night (`shards.from`, set by `Journey.Carry` from the arena's name).
  Brannoc's lines are the story lead's (they set them on their branch, merged here).
- **Phase 2's words, already in data, verbatim from the story lead** (wire them as written):
  Wenna's `greet`, `brew`, `first.brew`, `flask.sale`; Brannoc's `fang.choice`,
  `fang.give.before`, `fang.give`, `fang.set`, `history.fang`; a `maeca` crafter (no verbs yet,
  open on `pack.allied`) with `shedFur.offer`, `shedFur.braid.before`, `shedFur.braid`,
  `history.shedFur`, and `fang.seen` (a once-only bark when she first sees the fang worn).
- **The economy** (`tests/CraftingEconomy.cs`, design 19.2): Act 1 as ten won nights on combat's
  post-cut sweep, a spender crafting through the real forge. Tuned: break down yields halved,
  a shard per 12 ember, remake to Epic 18 iron and 200 gold, one remake a piece a day
  (`ItemInstance.Remade`). The targets hold on the economy where arena champions pay a tenth of
  the day's gold; the test asserts that case and logs today's.
- **The endgame designed** (design 20): the scars pay fire, the atlas pays iron and bases; two
  kits; item level and grade caps by it; Marks (skill-bending seam content, a proposal); chart
  verbs (Ink, Burn and redraw, Pin, Scrape, Annotate) at Ysolde's table with a chart's own heat.

## Next, in order

1. **Champion gold in arenas at a tenth.** A Kerchief night pays 2.5k–3.3k gold today, more than
   the rest of Act 1 together; crafting's prices cannot hold that. It is combat's one line
   (`Rules.FodderGold`'s use in `Battle.KillEnemy`); the combat lead agreed in principle that
   it's theirs to change. Ask combat's successor, or do it with their yes, then re-run
   `CraftingEconomy` and the balance probe.
2. **Phase 2** (design 7.2, 7.5, 10.1): Wenna's still-room (brew health draughts, antidotes, the
   moonpetal draught after combat's yes; her flask, 120 gold, refilled at Rook's while sleeping;
   her tinctures open on the stream's cure); commissions ("make me one", ready next morning);
   the fang set (a unique prefix *Greymuzzle's*); shed fur (a Rare amulet *of the Pack's Leave*,
   braided by Maeca). The lines are in data already.
3. **Phase 3**: Vonnra's binding at the toll-house table (her role is unchanged, confirmed by the
   story lead; write her lines without the survivor's name, as her name-takes are spliced; the
   story lead writes them); Snib's slurry while the pump runs.
4. **Endgame builds** (design 20.6). Combat has built the charts (`Maps/Charts.cs`: tier, people,
   seed, rarity, prefixes and suffixes, each paying quantity, rarity and pack size), and the
   experience director (`ad1f5623590e09883`) has set a map's shape (`docs/EXPERIENCE_AUDIT.md`,
   "A map's shape", on `worktree-agent-ad1f5623590e09883`). Design the chart verbs (20.4) against
   both. Their ask: working a chart is a choice about risk (which mod to live with for which
   pay), never a tax; check Ink and Burn against that (Pin and Scrape already are). They also note
   Kerchief maps pay about 700 gold at the day's rate: weigh it in `CraftingEconomy` once maps run.
5. **Still to see** in the game: the forge right after a craft (Brannoc's line, the gauge), the
   pack's break down by mouse, a real arena's end after a fall.

## Decisions (each with its why in design 17)

Heat caps working; the forge's ceiling is a lucky drop's grade; work in makes answers and
offensive affixes are only moved; three coals offered; the night pays at its end and a fall
spills half; remake costs iron; the anvil works one seam at a time; one remake a piece a day;
break down halved and a shard per 12 ember; the scars pay fire and the atlas iron; "Marks", not
"sigils" (the canon keeps sigils for the Legion's seven that hold the chain).

## Failures and why

- The first forge listed every craft for every seam; built from the brief without seeing it. Seen,
  it was a wall of red refusals. Always shoot a screen before calling it done.
- The economy's first run: iron 190 and shards 100 unspent, weapon Uncommon to Epic in a day,
  "fully worked" 7–8 (measured loosely: drops already roll at their cap half the time; the measure
  now counts only pieces the forge worked three times or more).

## Gotchas

- **Running the game from a worktree:** `godot/assets` is a git symlink file; replace it with a
  junction to the main checkout's `public/assets` after `git update-index --skip-worktree
  godot/assets`; copy the main `godot/.godot` in (robocopy, 1.7 GB); copy untracked art from the
  main `godot/art` with `robocopy ... /E /XC /XN /XO` (it fixed a missing outfit texture). Never
  commit those copied files: add paths explicitly.
- **Play script:** `scratchpad/crafting/play.py NAME --timeout S -- [game args]` (frames in
  `godot/.shots`). Useful args: `--quick warden --sex female --zone waystation --time day`,
  `--items "old_iron*14,wolf_pelt*5,iron_helm:3"`, `--gold 400`, `--open "talk:brannoc>work my
  gear"`, `--anvil iron_helm`, `--pad --focus temper|remake|seam:1|coal:0`, `--zone arena
  --people pack --open result [--fell]`, `--icons iron` to re-photograph one icon (lands in
  `%APPDATA%/Godot/app_userdata/Survivor Unchained/icons`).
- **PowerShell 5.1 and git:** double quotes in `-m` messages break the arguments; write the
  message to a file and `git commit -F`.
- Files written with the Write tool are LF; most of the repo is CRLF. Match the file when doing
  string replacements in PowerShell.
- `Crafting.BreakDown` takes a crafter now (for its lines); the pack passes none.

## Collaborators (roster in `docs/team/README.md`)

- **Story** `a035208561a66c171`: writes every crafter's words; approves seeds. Send hooks with ids,
  where each shows, and who says it.
- **Combat**: the lead `ac4ec5bbd2763a0df` handed off (`docs/handoff/combat.md` holds my asks:
  chart heat and a pin, item level on map drops, map materials tallied like nights, two kits;
  Marks need a per-skill modifier hook, which looks feasible on `WeaponInst`). Their successor
  builds maps.
- **UI design**: the forge brief is in `docs/handoff/ui_design.md` §4 item 7 for their successor
  (house frames for seam rows and tiles, a hammer-strike moment, a pad flow check).
- **Experience** `a33f58e68e89e3ccf`: owns the atlas's and scars' loops; agrees nights pay
  materials and kindling for maps and maps pay gear for nights.

## Files to read first

`docs/team/crafting.md`, `docs/CRAFTING_DESIGN.md` (1, 5, 7, 13, 17, 19, 20),
`godot/logic/Rpg/Crafting.cs`, `godot/data/content/crafting.json`, `godot/src/Ui/Forge.cs`,
`godot/tests/CraftingTests.cs`, `godot/tests/CraftingEconomy.cs`, `docs/SKILLS_DESIGN.md` §17
(combat's maps).
