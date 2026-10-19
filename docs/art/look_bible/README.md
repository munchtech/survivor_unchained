# The look bible: the Prologue first

Written by the art direction lead (look bible 1) from 18 October 2026. It sets the look the Prologue is built to: C01-C04, the Low Ford road, the river, the town. The rest of the game is then brought to match.

## The owner's direction (18 October)
- "more realistic - but stylized enough to make sense on saving graphics lag"
- "we have a way to build our own now ... we should begin making the first bit (tutorial) launch ready first as its the part to hook people"
- "the waxy skin and plastic armor certainly needs some work - moreso the armor as it will cover most skin as we get better armor"
- The tiers: "very few things need to be as detailed as our heroine ... we will cut corners with smart clever tricks that still look good":
  1. full detail: her, her spells, her animation, later the bosses;
  2. good on a budget: the open world and the story NPCs;
  3. cheap: fodder mobs.
- The bar for tiers 2 and 3 is "looks good in the shot and runs well", not "matches her".

**No building before the bible's frames pass the owner.**

## Pages
| # | Page | State |
|---|---|---|
| 1a | [Her armor metal](01_armor_metal.md) | passed the coordinator; with the owner |
| 1b | [Her skin](02_skin.md) | board ready for the owner |
| 1c | [Light, grade and mist](03_light_grade_mist.md) | passed the lead's judge (round 2, fixes applied 29f4b2a9); with main |
| 1d | [Water and shore](04_water_shore.md) | passed the lead's judge (round 2, fixes applied 29f4b2a9); with main |
| 1e | [Foliage](05_foliage.md) | passed the lead's judge (round 2, fixes applied 29f4b2a9); with main |
| 1f | [Terrain and road](06_terrain_road.md) | passed the lead's judge (round 2, fixes applied 29f4b2a9); with main |
| 1g | [Stone and the castle](07_stone_castle.md) | passed the lead's judge (round 2, fixes applied 29f4b2a9); with main |
| 1h | [The town](08_town.md) | passed the lead's judge (round 2, fixes applied 29f4b2a9); with main |
| 1i | [NPCs and crowds](09_npcs.md) | passed the lead's judge (round 2, fixes applied 29f4b2a9); with main |
| 1j | [Story props and flames](10_props_flames.md) | passed the lead's judge (round 2, fixes applied 29f4b2a9); with main |
| 2 | [Budgets: per frame, per tier, per asset](11_budgets.md) | passed the lead's judge (round 2, fixes applied); with main |
| 3 | [The Prologue's asset inventory: keep, rework or build](12_inventory.md) ([csv](12_inventory.csv)) | 323 rows marked; passed the lead's judge (round 2, fixes applied); with main |
| 4 | [The tutorial's launch-ready checklist](13_launch_checklist.md) (the first 20-30 minutes) | passed the lead's judge (round 2, fixes applied); with main |

## Rules for the boards
- Reference pictures from other games are for reference only and never ship. They live outside the repo, in `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_refs\`; `steam\sources.csv` logs each source URL.
- The repo holds only our own frames (`frames/`, from the 18 October whole-frame audit, 1:1), links, and short notes on what each reference teaches.
- Every board says what the look IS, what ours ISN'T, the cheap trick that buys it, and what DONE means at the game's cameras at 1:1.
- `tools/lumstats.py` measures a frame's light (luma p5/p50/p95, clipping, saturation, pools) for the DONE lines on 1c and 1h.
