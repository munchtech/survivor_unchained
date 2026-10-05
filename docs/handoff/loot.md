# Handoff: loot and itemisation

For the next loot lead. Read this, then `docs/team/README.md`, then `docs/team/loot.md` (one-page
status), then `docs/design/LOOT_DESIGN.md` (the approved design). Branch
`worktree-agent-a9a9c345a35e1fcad`; merge `origin/claude/vigilant-galileo-l6jqyx` first.

## The owner's words (5 October 2026)

- "a very intuitive inventory management is smart. things that can be tucked away like spellbooks
  or stuff is useful, inventory management is a very real concern in these games so we need it, but
  we also don't want to feel cheated with things that should stack, or should not even take up
  inventory spots directly either."
- "we also need to make an item filter and more poe/diablo style drops that can be seen or hidden
  better with better sounds on quality items and we don't have any legendaries (extremely rare) yet
  do we? or sets. ... should have some legendaries even at low lvls for huge dopamine spike."
- "theres far too many common items that we don't need. common items in higher zones can be better
  than greens or even blues (or way later commons even better than early purples) but in general
  items can drop a little less, their drops replaced maybe with crafting stuff."
- "item drops should *mostly* feel good." The bar: "we are striving for perfection".

## The brief

Loot and itemisation lead. Design first (`docs/design/LOOT_DESIGN.md`: research, tiers with
legendaries and sets, item level and zone scaling, drop rates, stacking and slotless stores, the
filter, presentation, loot across story arenas, maps, survivors arenas and crafting), then the rules
in logic with tests, then content (first Legendaries, some early; one or two sets; trimmed commons).
Each Legendary must change how you play and fit the world (`docs/STORY_BIBLE.md`). Legal: our own
art and sound only. Heavy work takes turns (`tools/turn.py take godot "loot: ..."`). British
spelling; comments short prose saying why; `dotnet test` in `godot/tests` before every commit.

## Done (all on the branch, last db75a39f, 699 tests green)

- **Design**, approved by the main session; every later change recorded in it.
- **Logic**: `Rpg/Loot.cs` (`Drops`: tiers, make, implicits, power, upgrades, sets, the drop roll),
  `Rpg/LootFilter.cs`, stores in `Rpg/Character.cs` (`Inventory.Find/Holds/Remove/Count/Take`,
  `CharacterData.Satchel/Keys/Belt/Filter/Seen`), `Play/JourneyLoot.cs` (`Drops`, `Judge`, `Take`,
  `Gather`, `NightTally`), `Journey.FirstLegendaryTaken`, save v4. Data: `data/content/loot.json`.
- **Zones**: ArenaRun, StoryNight, Verge and MapRun roll through `G.Journey.Drops(new DropCtx{...})`;
  hoards and strongboxes spill through `Battle.Spill`.
- **Content** (`items.json`): Drowned Coat, Nan's Cleaver, Corran's Sword, Ditchwater, Fever-Year
  Staff, Slurry Wheel, Kell's Lamp, Pelt of the Pack (story-gated); the Watch's Kit and the Levy Red
  (`loot.json` sets); stronger base implicits. Lore is the story lead's, verbatim (WRITING_PASS §25).
- **Presentation (placeholders where noted)**: ground labels (`Ui/GroundLabels.cs`, built and
  seen), the edge pointer (`Game.Offscreen`), beams (`Fx/BattleFx.cs`, placeholder), drop sounds and
  the toll (`Audio/Sfx.cs`, `Synth.DuckBeds`, placeholder), the Pack's store row (`Ui/Pack.cs`,
  stop-gap). Pictures: `--loot [legendary]`, `--hoard N`.

## In progress, and next

1. The main session merges db75a39f. Then story adds Holloway's line for Corran's Sword.
2. See a whole night's drops from play: the experience director's `play.py --auto` gets past the
   great blessing's draft (my `--keys` could not). Judge whether drops mostly feel good.
3. Combat's successor tunes `loot.json` (counts, curves) and the Legendaries' numbers. Open: full
   Heartwrought armour is still about 70% reduction; the lasting fix is level-relative armour.
4. UI design builds the tabs, the filter screen (rules later), the hold-to-show key
   (`Battle.TakeHidden`), the debt's tally ("What the dark owes you", `Drops.DebtLabel`) and the
   results' `Gathered` line.
5. Later acts and the atlas: Legendaries with homes in maps (the chase there), the items plan's
   other sets (`docs/items/CATALOGUE.md` §7), Storied items.

## Decisions (why in the design, §13)

Set is a tier for the eye, rarity 3 underneath. Make scales a base's implicits (armour gentler;
flat rule damage too); grades rise only past level 25. Gear only from carriers, about a third
fewer; materials in gear's place at crafting's measured rates, to the night's tally in arenas. A
certain first Legendary from the first story boss; the dark's debt at 120. The pack holds gear
only. No Legendary grants a rise; none is worked at the forge. The toll hushes the music, never the
fight. Commons and Uncommons have no beam.

## Failures and why

- Make ×4.6 on armour gave ~75% reduction (combat): armour got its own curve.
- "At full health" as a price never applies in a horde (combat): `ModWhen.Healthy` (>80%).
- Ducking the sfx under the toll hides telegraphs (combat): `DuckBeds` (music and ambience).
- Materials at 1 + 50% iron piled up (crafting's CraftingEconomy): 10% and 20%.
- "Ashford Levy Colours", "Forty-One Mouths" and some lore broke canon (story): renamed, rewritten.
- Six beams after a fight read as clutter by day: no beams below Rare.

## Gotchas

- The static class is `Drops` (Sim already has a `Loot` record). `Make` (enum) clashes with test
  helpers named `Make`: name them otherwise.
- The worktree guard refuses Python heredocs and complex `cd ... && git` lines: write scripts to the
  scratchpad (`scratchpad/loot/`) and run git from the worktree root.
- `items.json` is `json.dumps(indent=1, ensure_ascii=False)`; crafting's four mark entries keep
  `"tags": ["mark"]` inline (the scripts re-collapse them).
- Running the game from a worktree: junction `godot/assets` to `public/assets` (skip-worktree), copy
  the main `godot/.godot`, copy untracked art from the main `godot/art` (never commit those `.import`
  files), `dotnet build` in `godot/` before every run. Harness: `scratchpad/loot/play.py NAME
  --fixed-fps 60 -- --zone verge --time night --loot --hoard 1`.
- Arenas open on a great blessing draft; shoot loot in the Verge (`--zone verge`), by night for beams.

## Collaborators

UI design `a4fdbc49786ba8b7f`; UI art `a0bff3ffe4d3ad748` (Set mark `link_set_14/24`); Skills VFX
`abc6bbe020c7fe287`; crafting `af01b0d61ef656dd4`; combat (handed off; successor via the main
session); experience director `a9f0d6c64d891d56d`; story `a7ba8903f4c8261b1`.

## Files to read first

`docs/design/LOOT_DESIGN.md`, `godot/logic/Rpg/Loot.cs`, `godot/logic/Rpg/LootFilter.cs`,
`godot/logic/Play/JourneyLoot.cs`, `godot/data/content/loot.json`, `godot/tests/LootTests.cs`,
`docs/CRAFTING_DESIGN.md` §5, 6, 13, 17.
