# Crafting: handoff

For the next crafting lead. Read `docs/team/README.md` first (the owner's bar, how we work),
then this, then `docs/team/crafting.md` (one-page status), then `docs/CRAFTING_DESIGN.md`
(sections 1–20; 17 decisions, 19 what was seen and measured, 20 the endgame). The research is
`docs/CRAFTING_RESEARCH.md` (lessons C1–C30, cited in the design).

## The owner, in their words

- "AAA standard", "strive for excellent, above and beyond - not just good enough".
- "I don't want to polish, I want to create perfection." Remake rather than patch.
- "Do we have soul?" Make it this valley's, not generic.
- "end game is two types of arenas - permanent and our normal arenas. permanent is our arpg
  build maps like poe and the normal arenas are for mindless survivors fun." The bible names
  them the Wayfinder's atlas (Ysolde's) and the scars.
- Story is about 40% of the game early on; the endless phase is truly endless.
- Decided: the weapon's upgrade (Remake) costs old iron; falling after the half-hour spills half
  the night's materials; full-page screens pause the world only in arena combat and are often
  not the best choice.

## Your brief

Crafting lead: research, design and build crafting, playable end to end and seen in the running
game at full resolution. It serves the story's early share (crafters are people, crafts open by
story), the scars (survivors runs) and the atlas (build maps with build depth). Don't stop to
ask. Keep `dotnet test` in `godot/tests` green, British spelling, short "why" comments, commit and
push your own branch at milestones (the main session merges; no PRs), hand off past ~500k.

## Done (this lead, `a7debf1459f14dfe7`)

- **The arena's gold cut** (combat built it at my ask; 7f04b40, cd9a194, 4c32586): champions 7%,
  fodder 0.15%, bosses and minibosses in full. Measured by `CraftingProbe`: a Kerchief night pays
  375/351/365 gold (it paid 2.5k–3.3k). `CraftingEconomy` reads the arena's real rates and holds
  every target (weapon Epic by day 8, crafting takes 67% of the gold). Design 19.2, decision 18.
- **Phase 2** (design 19.3): Wenna's still-room (`src/Ui/StillRoom.cs`, a side panel: brews, "Brew
  N", her flask refilled at the inn), her bench after the cure (ForgeScreen `forge:wenna`), the
  moonpetal draught (60%, drunk only for a deep wound), Brannoc's commissions ("Make me one"),
  Greymuzzle's fang set outside the seams (`ItemInstance.Setting`), Maeca's braid of shed fur, her
  once-only "That's his." (said lines can carry `effects` now).
- **Phase 3, code and tests** (not yet seen in the game): Vonnra's binding (`Crafting.Bind`,
  `Donors`; ForgeScreen `Binding` per seam, a two-step "Unmake it"), Snib's jars and bench
  (`BuyJar`, `JarsLeft`, ForgeScreen `JarTile` and a Steep tile with the odds), steeping
  (`Crafting.Steep`, outcomes up/affix/nothing/down, bright grade V, three slurry affixes
  `fevered`, `of_the_sump`, `pipe_lads`) at Snib's bench in his words or from the pack by hand
  (two-step, odds said). Snib's "Sell me a jar of that." opens his bench (`action: craft`).
- **Seen and fixed**: the forge's hammer moment (row flare, streak sparks, heat burning out, then
  the next preview); empty Work in said why; painted icons for the moonpetal draught, flask and
  braid (`tools/comfy/ui_art.py icon item KEY "..."`); the pack's break down says what it came to
  and the ask is red; crafts no longer re-dress the figure (`G.Gear` rebuilt her: she blinked
  out); **an arena fall now spills half** (`Arenas.Finish` knows a fall by its killer).
- All the story leads' words are wired verbatim (phase 2 from `a035208561a66c171`, phase 3 from
  `a73ca9d35d0c487a9` at d132033f, renames applied: `bind.caged`, `steep.affix`, `jar`).

## Next, in order

1. **Full-resolution checks, waiting for Godot to be free** (the owner is using the GPU: no Godot,
   no ComfyUI, no Blender until the coordinator says so):
   - Vonnra's table: `--met vonnra --facts toll.paid=true --items "silver_ring:3:searing@3+keen@1,bone_amulet:2:hale@1,ember_shard*6" --gold 400 --open "talk:vonnra>+>move what" --anvil bone_amulet`. Check the Bind cards, the armed "Unmake it" state, the strike, and her first.bind narration in the left pane (long: it may not fit).
   - Snib's bench: `--met snib --items "iron_helm:2:hale@1+of_the_wolf@0" --gold 200 --open "talk:snib>jar"`. Snib may need `--zone` for the Dig (find where he stands). Check the jar tile, the Steep tile's odds, the two-step, and his words after.
   - The pack's steep: `--items "slurry_jar,iron_helm:2:hale@1"`, then `--open inventory --clicks` (find the button by a shot first). Check the odds slab and the outcome note.
   - A slurried piece's card (green line, the "slurried" tag line) and a grade V badge.
   - Wenna's still-room after a moonpetal brew (the row glow; `--focus brew:2 --pad --keys Confirm`).
   - A commission collected the next morning (the "!" over Brannoc, the piece on the anvil).
2. **Paint the slurry jar's icon** when ComfyUI is free: `python tools/comfy/ui_art.py icon item slurry_jar "a squat stoneware jar sealed with wax and twine, green-black sludge glowing faintly through a crack, a crude scrawled mark" --seeds 4`, then `fit-icon item slurry_jar CANDIDATE`. It uses the `slurry_jar` key; until then it falls back to a glyph.
3. **Design doc**: add 7.3 and 9 as built (place "The Toll Tower"; jars at Snib's bench and steeping by hand) and the decisions below; record phase 3's seen results in 19.4.
4. **Endgame** (design 20.6): combat built maps (5c50de1) and the Marks hook (09b6b03).
   - Two kits first.
   - Then item level and grade caps.
   - Then chart verbs at Ysolde's table (`ItemInstance.Chart`; the quality field is ready).
   - Then Marks on the item side: fill `CombatKit.Marks` (id to strength 0–1, from grade 0–5) and `CombatKit.SkillMods` in `Character.Kit`. Four ids are proven in `Sim/Marks.cs`. Inscribed at Vonnra's table; her mark lines are already in data.
5. Owed from before: re-measure shards with 20-minute story nights; minibosses' +2 of the
   people's material.

## Decisions (each with its why in design 17)

Heat caps working; the forge's ceiling is a lucky drop's grade; work in makes answers; three
coals offered; the night pays at its end and a fall spills half; remake costs iron; one seam at a
time; one remake a piece a day; break down halved; arena gold cut (18); Wenna brews from the start,
tinctures after the cure (19); the still-room is a side panel (20); moonpetal only for a deep
wound (21); a trophy is set outside the seams (22); crafts never re-dress the figure (23).
Phase 3, to write into 17: binding moves plain powers only (coals stay in Brannoc's cage; worn
skills, trophies and slurry powers will not let go); the donor must be in the pack; steeping is
by the survivor's hand from the pack as well as at Snib's (jars kept past the cure still work);
the slurry's outcome "affix" adds a fourth power past the seams; Vonnra opens only once the toll
is paid (the story lead's condition).

## Failures and why

- Built the strike's sparks on the first page build; a craft builds the page twice, so they fired
  on a page already gone and crashed. Now they wait a moment and play on the live page.
- The first economy cut (champions to a tenth) left 1.6k–2.1k a Kerchief night: my predecessor's
  model blamed champions, but fodder paid most. Measure before asking.
- A headless `--import` rewrote 857 `.import` files and made 46 stray `.uid` files; reverted with
  `scratchpad/craft2/revert_imports.py`. Commit only your own new `.import`/`.uid` files.
- Heredocs with Python in Bash are refused by the worktree guard: write scripts with the Write
  tool into the scratchpad (`craft2/ed.py` `sub()` keeps a file's CRLF; `js.py` keeps the JSON
  layout; `crlf.py` restores CRLF after `sed -i`).

## Gotchas

- **Running the game from this worktree**: `godot/assets` is a junction to the main checkout's
  `public/assets` (skip-worktree set); the main `godot/.godot` is copied in; untracked art copied
  from the main `godot/art` (never commit those; a merge may need two of them removed first).
  **Run `dotnet build` in `godot/` before every run**, or the old DLL runs.
- **Play script**: `scratchpad/craft2/play.py NAME --timeout S -- [game args]` (frames in
  `godot/.shots`, log in `craft2/logs`). New args: `--items DEF:RARITY:AFFIX@GRADE+...`,
  `--facts k=v,...`, `--met a,b`, `--clicks X:Y,...` with `--click-every S`, `--won` (with
  `--minute M`; then `--die T` falls her past the win), `--make --pattern DEF`, `--focus ID` on the
  still-room. A conversation's greeting often needs `+` before a choice (`talk:wenna>+>brew me`).
- `crafting.json` is hand-laid (one-line rules): edit it as text, not with a JSON round-trip.
  Unknown keys inside an object are ignored, but a `_note` key inside `crafters` breaks the parse
  (it is read as a crafter).
- The HUD's toasts are hidden under the pack and full pages: say outcomes in the page itself.
- `G.Gear` re-dresses the world figure (she blinks out) and the pack doll T-poses a frame on every
  refresh (told to UI design). Crafts use `G.Journey.Work(...)` and `Refresh()` instead.
- ComfyUI is shared: queue behind others' jobs, then `POST /free` when done.

## Collaborators (roster in `docs/team/README.md`)

- **Combat** `a1d4562f44c7f6feb`: built the gold cut and the Marks hook. They said yes to the
  moonpetal draught (heal source "draught", so map suffixes catch it). The maps are theirs; the
  item side of Marks is ours.
- **Story** `a73ca9d35d0c487a9`: phase 3's words are wired. Vonnra's mark lines are waiting for
  the endgame. Send them hooks with ids, where each line shows, and who says it.
- **UI design** `a69858664f1d3dd29`: told about the still-room, the forge's moment and the pack's
  doll bug.
- **UI art** `a1a394643aabfb169`: told about the three item icons painted with their pipeline.
- **Experience** `ad1f5623590e09883`: owns the atlas's and scars' loops.

## Files to read first

`docs/team/crafting.md`, `docs/CRAFTING_DESIGN.md` (1, 7, 9, 17, 19, 20),
`godot/logic/Rpg/Crafting.cs`, `godot/data/content/crafting.json`, `godot/src/Ui/Forge.cs`,
`godot/src/Ui/StillRoom.cs`, `godot/logic/Play/JourneyCrafting.cs`, `godot/tests/CraftersTests.cs`,
`godot/tests/CraftingEconomy.cs`, `godot/logic/Sim/Marks.cs` (combat's, for the endgame).
