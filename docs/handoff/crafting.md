# Crafting: handoff

For the next crafting lead. Read these in order:
1. `docs/team/README.md`: the owner's bar, how we work, heavy work by turns.
2. This page.
3. `docs/team/crafting.md`: the one-page status.
4. `docs/CRAFTING_DESIGN.md`: section 17 is the decisions (1–30); 19 is what was seen and measured; 20 is the endgame
   (20.2 the kits as built, 20.7 the endgame as built, 20.8 seen and measured, including the bench).
5. `docs/design/LOOT_DESIGN.md`. Item level and make are loot's. Crafting's materials are what a carrier drops in
   place of gear.

The research is `docs/CRAFTING_RESEARCH.md` (C1–C30).

## The owner, in their words

- "AAA standard", "strive for excellent, above and beyond - not just good enough".
- "I don't want to polish, I want to create perfection." "We are striving for perfection."
- "item drops should *mostly* feel good": fewer drops, the rest as crafting materials.
- "end game is two types of arenas - permanent and our normal arenas. permanent is our arpg build maps like poe
  and the normal arenas are for mindless survivors fun": the Wayfinder's atlas and the ember scars.
- The latest screen rules (through UI design, for every screen):
  - no dark rounded boxes holding data ("still ai boxes" at any size);
  - no fades unless designed;
  - no dead space, and a strict grid;
  - words as type rather than buttons.
- Decided earlier:
  - remake costs old iron;
  - a fall after the half hour spills half;
  - full-page screens pause only in arenas;
  - Rook's storeroom grows by bought shelves (24, then 300, 1,000, 2,500 and 5,000 gold, up to eight);
  - the bench is two panels with the smith live in the world between them.

## Your brief

Crafting lead: research, design and build crafting, playable end to end, and seen in the running game at
1920×1080.
- Don't stop to ask. Keep `dotnet test` in `godot/tests` green before every commit.
- British spelling, and short comments that say why.
- Commit and push your own branch at milestones. The main session merges it; open no PRs.
- Take a turn for Godot (`tools/turn.py`) and give it back the moment the shots are done.
- Hand off at about 500k tokens of context.

## Done (this lead, `ab0b263c720bdbda8`)

- **Seen at 1920×1080** (design 20.8):
  - a scar left an hour past the win (50 shards, a scar-glass, the story's line), and the same night fallen;
  - a whole map's pay;
  - a ruler's Mark coming home, and Vonnra inscribing it.
  - Switches for this: `--clear T` fells a whole map, `--leave T` takes the way out of a won arena or cleared
    map, and a map's pay is logged ("map paid: ...").
- **The atlas's pay mended**, measured with the lab's `map` sweep, which now reports material, shards, iron and
  Marks:
  - the people's own now comes only from what carries it (ruler 3, keeper 2, leader 1): 15–18 a map, not 74–102;
  - the Dig's lamplings pay old iron in maps, not the scars' fire;
  - charts and Marks left lying come home at a map's end (`Journey.Gather`).
  - Loot did their half: finds sent to Rook show on the map's result, and lampling carriers drop iron in maps.
- **Two kits, in logic** (`Rpg/Kits.cs`, design 20.2 as built):
  - the night kit holds only what differs from the day's, and goes on by itself wherever the ember burns;
  - `Store.Kit` marks a piece worn in the kit that isn't on;
  - `Journey.EquipKit` and `UnequipKit`; `--nightkit DEF` for pictures.
  - UI design builds the Pack's switch.
- **The bench as two panels** (`Forge.cs`; design 20.8):
  - theirs at the left: the person as a strip, the anvil, its seams, the crafts, their terms;
  - yours at the right: worn, with the kit switch; carried, stores and purse via UI design's `PackBlock`;
  - the crafter live between, through `Overlay.CameraLook`, a world point the view looks at;
  - the crafts grouped by verb under counted tabs (Temper 1 · Work in 4 · Cage 4 · The piece 3).
  - Then remade as type to the owner's new rules:
    - the seams are ledger rows;
    - each craft's name is its act, held for what cannot be undone;
    - the heat is a chain of UI art's links (hot, warm, cold);
    - the likeness fades into the panel (`shaders/ui_likeness.gdshader`).
- **A Legendary breaks down** for 5 old iron and 3 shards wherever it's broken (`Crafting.Yield`). Brannoc's own
  lines over it (`breakDown.legendary`) are the story lead's, verbatim.
- **Hand-offs made:**
  - Vonnra's placeholder model → creatures, now on their should-make list;
  - a bark drawn over a name plate → UI design, now on their list;
  - two result-screen findings → UI design (the map result's best finds below the fold; the night result's left
    card overflowing at 1080).

## In progress, and next

1. **The bench, the last pass.** UI design will tell you when their push is up. It brings:
   - panels at an even 28 margin, see-through, no taper;
   - grids straight on the page with no well; empty worn slots as engraved shapes; soft card edges;
   - `HeldWord` (SelfScreen.cs).

   Then:
   - merge it;
   - swap the held acts in `ForgeScreen.Deed` (they use a `Style.HoldButton` stripped to a word for now) to
     `HeldWord`;
   - reshoot every bench with `scratchpad/craft4/bench_shots.py` and send UI design 1:1 shots.

   Still open from their notes: the tabs' art (the boxed look should go once UI art's kit is applied), and the
   worn row's engraved empties.
2. **Icons.** UI art (`a0bff3ffe4d3ad748`) is repainting red_cord (it read as an S), lamp_glass (it read as a
   drinking horn) and scar_glass, which is a placeholder star today. They're queued for the GPU. When their PNGs
   land, take them into `tools/uiforge/items.py` and `godot/art/ui/icons/item`. Judge them in the game: the
   night's haul (`--zone arena --minute 95 --won --facts stream.clear=true --lab --leave 2`), the satchel, and
   Vonnra's Mark card.
3. **Measure the endgame's economy**: hours of scars and maps mixed. Shards, iron and the people's own come in;
   charts, marks, cages, rekindles, tempers and remakes spend them. My rough reckoning:
   - iron and the people's own will pile up once a build is made, since few endgame sinks take them;
   - shards roughly balance against chart working.

   Measure before asking anyone for numbers (a lesson from the first lead).
4. **Kits on the Pack:** when UI design's switch lands, see it at 1920×1080 with `--nightkit`.

## Decisions (each with its why in design 17, 20.2, 20.7, 20.8)

- Decisions 1–30 stand.
- **The kit follows the place**, and the night kit holds only what differs: no swap verb, nobody dresses twice.
- **The atlas pays iron and the scars pay fire.** Map materials come from what carries them.
- **Shelf prices stand.** Maps pay about 1,000 gold an hour, nearly all of it from Kerchief maps.
- **The bench's crafts are grouped by verb under counted tabs.** A dozen cards at once ran off the screen; UI
  design agreed.
- **Heat as a chain of links.** It's the motif doing a job, not ornament.

## Failures and why

- My first two-panel left panel ran off the foot of the screen, because every craft was shown at once (about 12
  cards). Fixed by grouping the crafts.
- My first `CameraShift` with no look point left Brannoc hidden under a roof, so the gap showed nothing. The
  view now looks at the crafter, nearer.
- `--leave 4` at minute 95 without `--lab`: the horde killed her first, so the "walked out" shot was really a
  fall. Use `--lab` for the left case.
- Leaving a whole-map clear at 7 s gave 0 gold, because the pulled coins hadn't arrived yet. Use `--leave 16`.
- A Godot name clash: a method called `Look` (Game already has `Look`) and one called `Act` (the enum). Pick
  names that are clearly yours.

## Gotchas

- **Running from a worktree:**
  - `godot/assets` must be a junction to the main checkout's `public/assets` (skip-worktree). Make it with
    PowerShell `New-Item -ItemType Junction`.
  - Copy a sibling worktree's `godot/.godot` in (robocopy).
  - Then run `scratchpad/craft4/copyimports.py` and `fillimported.py`. They copy missing `.import` files and
    their imported data from the main checkout and sibling worktrees.
  - Run `dotnet build` before every run.
  - UI art's `art/ui/chain` has no imports; UiArt loads them from file, and that's fine.
- **Scripts** (in `scratchpad/craft4/`):
  - `play.py NAME --timeout S -- [game args]`; frames land in `godot/.shots`.
  - `crop.py`, `sheet.py`.
  - `ed.py`'s `sub()` keeps line endings. The worktree guard refuses complex shell, so write a Python edit
    script and run it plainly.
- **Clicks:** `--clicks X:Y` clicks, `hX:Y` hovers (UI design's), `pX:Y` presses and holds a second (mine).
  Positions move with content: shoot once, then click.
- **The bench's switches:**
  - `--open forge:ID` (brannoc, wenna, vonnra with `--facts toll.paid=true`, snib, wayfinder with `--charts N`);
  - `--anvil DEF`, `--make --pattern DEF`, `--near ID --met ID`, `--nightkit DEF`;
  - `--items DEF:RARITY:AFFIX@G+..`.
- **Turns:** `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "crafting: job" --wait 20`,
  run in the background, then `give` when done. Waiters are served in the order they first asked.
- **Data:** `crafting.json` is hand-laid; edit it as text.

## Collaborators

- **UI design** (`a4fdbc49786ba8b7f`):
  - owns the screens' rules and the Pack's kit switch;
  - judges the bench;
  - will tell you when their push is up.
- **UI art** (`a0bff3ffe4d3ad748`): the kit, the chain sprites, and the three icon repaints.
- **Loot** (`a9a9c345a35e1fcad`, handed off at e5ef6453): item level, drops, Gather, MapSpoils.
- **Combat** (`a5115633c7006e4d4`): maps (`MapRun`). They're fine with the material change, `ClearNow` and
  `--leave`.
- **Story** (`a7ba8903f4c8261b1`): all asks answered; Brannoc's Legendary lines are in WRITING_PASS §24.
- **Creatures** (`af551cacc6292152f`): Vonnra's own model comes after the boar, the Ford-Warden and the average
  man and woman. They'll tell you when it lands; judge it in her bench portrait.

## Files to read first

- Status and design: `docs/team/crafting.md`; `docs/CRAFTING_DESIGN.md` (17, 20.2, 20.7, 20.8).
- Logic:
  - `godot/logic/Rpg/Crafting.cs`, `Rpg/Kits.cs`, `Rpg/CraftingCharts.cs`;
  - `godot/logic/Play/JourneyCrafting.cs`;
  - `godot/logic/Play/Zones/MapRun.cs` (OnLoot, ClearNow);
  - `godot/data/content/crafting.json`.
- UI: `godot/src/Ui/Forge.cs` (the bench, the ledger seams, crafts as type, GradeBadge, the HeatGauge chain).
- Tests: `godot/tests/KitsTests.cs`, `AtlasPayTests.cs`, `CraftingTests.cs`, `CraftersTests.cs`, `CraftingEconomy.cs`.
- The lab: `godot/balance/Harness/MapSim.cs`; run `dotnet run -c Release -- map --tiers 1,4,7 --seeds 2
  --callings warden,arcanist --par 4` in `godot/balance`.
