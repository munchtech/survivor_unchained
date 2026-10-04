# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `a1d4562f44c7f6feb` (successor to `ac4ec5bbd2763a0df`).
- **Branch:** `worktree-agent-a1d4562f44c7f6feb`.
- **Read first:** `docs/handoff/combat.md` (the predecessor's knowledge), then `docs/SKILLS_DESIGN.md` §16–17.

## Current state (2026-10-04)

Tests green. Everything below is pushed.

**Done this session:**
- **The boss floor** (§16.1): the Barrow Lord's laying-down, Grimtunnel's going down and Greymuzzle's going skipped the last phase's floor (a strong build: about 35 s). Every ending now waits for it. A test drives an absurd build at all six rulers through the game's wiring: 60–77 s.
- **Re-measured after the last tuning:**
  - the Pack-Mother, Barrow Lord and Red Hand still ran 78–81 s, so they were raised by about a fifth;
  - the slowest minibosses were softened: the Decurion 560 → 380, the Weed-Wife 560 → 400, the Chucker 420 → 300, the Lamplighter 480 → 380, Firepot Nan 400 → 300.
- **The tier-3 brief** (§16.9): from the third tier the night asks the draft. Dusk lasts five minutes. The crowd's easing is at two fifths. Its blows grow to twice by the half hour. Champions, heralds and minibosses are a quarter stronger from the sixth minute.
- **Dusk for the oaths' bites** (§16.7): the blight's poison and cut to mending, and the winter's crawl, come in over dusk. At tier 3 the blight alone had felled 6 of 32 runs in minutes 1–5.
- **Crafting's gold**: arena champions pay 0.07 of their gold and fodder 0.0015; bosses and minibosses pay in full (crafting's probe: a Kerchief night about 350–450).
- **Maps built** (§17.8): `MapRun`, charts and mods, packs by tier, magic and rare packs, altar keepers, the ruler on map floors, loot and charts, three falls, and the atlas's record. The harness has a `map` command. The game has `--zone map [--tier --people --mods --seed --at boss]` and `Game.EnterMap(chart)`.
- **A flaky map test** made deterministic: no wall clock.

**Measured** (deft bot, table oaths, 8 seeds a tier, 192 runs):

| | Before (`5cdc32f`) | Now |
|---|---|---|
| Won, tier 3 (greedy / random) | 69% / 75% (6 seeds); 83% / 85% overall | 87% / 71% |
| Won, tiers 1 / 2 (greedy / random) | 94% / 88% overall | 96% / 84%, 93% / 84% |
| Falls before minute 5, tier 3 | 6 of 32 | 2 of 64 |
| Boss TTK (Pack / Barrow / Gutterwick / Red Hand) | 78 / 81 / 104 / 79 s | 82 / 86 / 95 / 81 s (the slowest random runs now finish past the cap) |
| Maps, tiers 1 / 2 / 3, day build at the map's level | – | 93% / 90% / 84% cleared, 11.7–13.2 min, ruler 60–65 s |

## Next (in order)

1. **The long night's tail:** done; the square is 0.004 (median past the half hour 22 -> 26 minutes). The dark's oaths and the crowd end it, not the square.
2. **Pictures of maps** at full resolution: the start, a pack waking, an altar's event, the ruler (`--zone map --at boss`).
3. **Maps, next:**
   - agree the length and rhythm with the experience lead (they run at the top of 8–12 minutes, with a pack every 14 s against their 20–40);
   - the atlas's biases (with experience);
   - chart crafting and the Marks hook (`CombatKit.SkillMods`, Mark ids read by behaviours), with crafting `a7debf1459f14dfe7`. Their four first Marks are of the Ravine, of the Falling Star, of the Open Gate and of the Gyre.
4. **Then:**
   - oaths on bosses (iron halves `StaggerTaken`);
   - ground hazards hurting the horde at half;
   - the Kindling at minute 15;
   - the Ford-Warden echo;
   - weight as a number;
   - Signs Warded, Mending, Leader.

## Key decisions

- **From the third tier the night tests the draft;** below it, choice is expression. Stronger levers cost the planned draft as much as the careless one, so they were not used.
- **A night is lost to the draft, not to its first minutes:** the oaths' bites come in over dusk.
- **One ruler health for maps (3.5× its body):** the night's per-ruler multipliers fit the ember's builds, not a day build.
- **Maps thin MapGen's pack spots** (three in four clearings' spots, one in three of the way's) rather than changing the generator, so nights and pictures keep their ground.

## Notes for other areas

- **Experience (`a33f58e68e89e3ccf` or successor):** maps run 11.7–13.2 minutes with a pack about every 14 s; the levers are `MapRun`'s thinning and MapGen's 16 clearings. Your call on the shape.
- **Crafting (`a7debf1459f14dfe7`):**
  - maps pay gold at the day's rate: about 700 a Kerchief map, about 25 for the others;
  - charts are `wayfinder_chart` items with `ItemInstance.Chart`;
  - the moonpetal draught is agreed at 60%, drunk when 55% or more is missing.
- **UI:** a chart's name is `Charts.Title`; `MapResult` holds a map's outcome; there is no result screen yet (a cleared map travels back to the Waystation).
- **Story:** the chart item's text and the mods' names are placeholders in the house voice and want your pass: `wayfinder_chart` in items.json, and `Charts.All`.
