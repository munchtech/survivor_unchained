# Loot and itemisation: status

Loot lead, agent `a9a9c345a35e1fcad`, branch `worktree-agent-a9a9c345a35e1fcad` (crafting's
`af01b0d61ef656dd4` merged in). Design: `docs/design/LOOT_DESIGN.md`, approved by the main session
(research §1, decisions §13). Frames: `docs/loot/`.

## State (2026-10-05)

**Built, tested (LootTests, 24; suite green) and seen at 1920x1080** (beams, labels, the Legendary's
line, the satchel). Waiting on the main session's merge.
- `Rpg/Loot.cs` (`Drops`): tiers, make by level (and armour's own curve), implicits and flat rule
  damage at make, power and upgrades, sets, the drop roll (`data/content/loot.json`).
- `Rpg/LootFilter.cs`: presets, toggles, rules, the never-hidden tiers.
- Stores: pack (gear only), pouch, satchel, key ring, belt; `Find`, `Holds`, `Remove`; save v4,
  tested on the owner's real save (`tests/saves/before_stores_v3.json`).
- `Play/JourneyLoot.cs`: drops judged by the filter; whole pieces taken; the night's materials to
  its end tally (crafting's rates); a fight's end gathered (`ArenaResult`/`MapResult.Gathered`);
  `FirstLegendaryTaken(item, x, z)` for the experience director's moment.
- Content: seven new Legendaries, the Watch's Kit and the Levy Red; the story lead's words verbatim.
- Presentation: names on the ground (`Ui/GroundLabels.cs`), the edge pointer, beams by tier and
  drop sounds and the toll (placeholders); pictures with `--loot` and `--hoard N`.

## Key decisions (why in the design, §13)

- Set is its own tier for the eye (verdigris, UI art's chain-link mark), rarity 3 underneath.
- The make scales a base's implicits (armour gentler); grades rise only past level 25.
- Gear only from carriers, about a third fewer; materials in gear's place at crafting's measured
  rates (10% the people's, 20% iron), to the night's tally in arenas.
- The first story boss beaten pays a Legendary; the dark's debt pays one at 120 rolls without.
- No Legendary grants a rise, none is worked at the forge; the toll never hushes the fight.
- Commons and Uncommons have no beam, only their names (six tubes after a fight were clutter).

## Next

1. The main session merges; then story adds Holloway's line for Corran's Sword.
2. A whole night's drops seen (experience director's `--auto` harness); tune counts with combat's
   successor (armour at depth: level-relative armour is the lasting fix).
3. The filter's rule list and the hold-to-show key (UI design); the debt's tally on results (UI).
4. Acts 2-3 and the atlas: more Legendaries with homes in maps, the items plan's other sets.

## Notes for other areas

- **UI design** (`a4fdbc49786ba8b7f`): ground labels and the edge pointer are built and theirs to
  restyle; `Gathered` and `Drops.DebtLabel` for results; `Battle.TakeHidden` for the hold key.
- **Skills VFX** (`abc6bbe020c7fe287`): beams in `BattleFx.Pickups` are placeholders (thin,
  additive, fading upward is the bar); `zone_drowned` needs a look.
- **Crafting** (`af01b0d61ef656dd4`): keep the tally block in `Arenas.Finish` after `Crafting.Night`.
- **Experience** (`a9f0d6c64d891d56d`): stage the first Legendary on `Journey.FirstLegendaryTaken`.
