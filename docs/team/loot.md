# Loot and itemisation: status

Loot lead, agent `a9a9c345a35e1fcad`, branch `worktree-agent-a9a9c345a35e1fcad` (crafting's
`af01b0d61ef656dd4` merged in). Design: `docs/design/LOOT_DESIGN.md`, approved by the main session
(research §1, decisions §13).

## State (2026-10-05)

**The rules are built in logic and tested** (`tests/LootTests.cs`, 21 tests; suite green). Nothing is
yet seen in the running game.
- `Rpg/Loot.cs` (`Drops`): tiers (`LootTier`), make by level, implicits at make, the power score,
  upgrades, sets, and the drop roll (`Drops.Roll`, `data/content/loot.json`).
- `Rpg/LootFilter.cs`: presets, toggles, rules, the never-hidden tiers.
- `Rpg/Character.cs`: `ItemInstance.Level` on all gear; the stores (`Satchel`, `Keys`, `Belt`, with
  the pouch); `Find`, `Holds`, `Remove`, `Count`, `Take` across them; set bonuses in the kit.
- `Play/JourneyLoot.cs`: drops judged by the filter; whole pieces taken; a fight's end gathered
  (`ArenaResult.Gathered`, `MapResult.Gathered`).
- The four zones roll through `Drops` (ArenaRun, StoryNight, Verge, MapRun); `PlainGear` is gone.
- Content: seven new Legendaries (four from levels 1-3), two sets of three, stronger base implicits.
- Save version 4 moves non-gear out of the pack, tested on a real save (`tests/saves/`).
- Placeholders: beams by tier (`Fx/BattleFx.cs`), drop sounds and the toll (`Audio/Sfx.cs`), the
  stores as the Pack's filter row (`Ui/Pack.cs`, until UI design's tabs).

## Key decisions (why in the design, §13)

- Set is its own tier for the eye (verdigris, UI art's chain-link mark), rarity 3 underneath.
- The make (x1, 1.8, 2.8, 4, 5.5) scales a base's implicits; grades rise only past level 25.
- Gear only from carriers, about a third fewer; a carrier with no gear drops 1 of its people's
  material and old iron half the time (crafting's numbers).
- The first story boss beaten pays a Legendary; the dark's debt pays one at 120 rolls without.
- No Legendary grants a rise (the owner's rule); none is worked at the forge.

## Next

1. See it at 1920x1080 (needs a Godot turn): a night's drops, beams, sounds, the toll, a gathered end.
2. Tune with combat and the experience director; story's words for lore and "Something old has fallen".
3. The rule list in the filter; the legendary reveal moment (experience) and its screen-edge pointer (UI).

## Notes for other areas

- **UI design** (`a4fdbc49786ba8b7f`): API in the design §11; results' `Gathered` (Home, Stored,
  Broken, Iron, Shards, Left); Set mark files are UI art's `link_set_14` and `link_set_24`.
- **Skills VFX**: my beam heights in `BattleFx.Pickups` are placeholders for yours (§8.1-8.2), and
  the Drowned Coat's zone art is `zone_drowned`.
- **Crafting**: marked trophies and charts live in the satchel; use `Inventory.Holds` and `Remove`.
  `Crafting.Workable` now refuses rarity 4 and set pieces. FinerGrade composes with the level shift.
- **Combat**: drop counts (§5.1), the make curve and the Legendaries' numbers are yours to tune.
