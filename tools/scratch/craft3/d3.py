"""Design doc 20.6/20.7: item level, the scars' depth, the economy against fewer drops."""
import os
from ed import sub
D = os.path.join(os.path.dirname(__import__("ed").ROOT), "docs", "CRAFTING_DESIGN.md")
sub(D, [
    ("""1. Marks on the item side (built, 20.7).
2. Chart verbs at the table (built, 20.7).
3. Item level on gear and grade odds by item level (with combat's map loot).
4. Two kits (pack and table), with UI design's new pack.
5. Higher grades and remake to Legendary (Act 2's hands).""",
     """1. Marks on the item side (built, 20.7).
2. Chart verbs at the table (built, 20.7).
3. Item level on gear and grade odds by item level (built, 20.7; the loot lead now owns item level and builds on it).
4. The scars' depth and scar-glass (built, 20.7).
5. Two kits (pack and table), with UI design's new pack.
6. Higher grades and remake to Legendary (Act 2's hands)."""),
    ("""- A save from before shelves keeps its 48 places as two shelves.""",
     """- A save from before shelves keeps its 48 places as two shelves.

**Item level** (`ItemInstance.Level`, `Crafting.FinerGrade`; the loot lead `a9a9c345a35e1fcad` now owns item level):
- Gear found in a map is made at the map's level.
- Each rarity rolls one of two grades. By day and at a first map's level that is a coin flip. The finer
  grade then comes a fortieth more often each level, up to nine in ten.
- It never passes the rarity's own finer grade, so the forge's ceiling stays a lucky drop's. The loot lead's
  shift (+1 grade from level 25, +2 from 35) adds on top.

**The scars' depth** (design 20.5; `Crafting.Night`):
- Past the win, a shard every two minutes; past thirty minutes beyond it, a shard a minute, without end.
- Once the stream is cured, a scar stayed in past the hour gives **scar-glass**, one more each hour after. It
  steeps by hand as a jar did: the slurry's gamble outlives the cure, earned by staying, not bought.
- A miniboss carries out two of its people's material (at the night's end, not dropped).

**The economy against the loot lead's fewer drops** (`tests/CraftingEconomy.cs`, swept):
- Carriers drop gear 45% of the time, not 60%.
- Act 1's targets hold at every rate tried for a non-gear roll: first craft day 1, the weapon Rare by day 4
  and Epic by day 8, crafting taking 63–68% of the gold.
- What moves is what is left unspent at Act 1's end:

  | A non-gear roll gives | Iron left | People's material left |
  |---|---|---|
  | (gear at 60%, before) | 59 | 62 |
  | the people's material always, iron half the time, the boss 2 | 85 | 166 |
  | nothing | 27 | 57 |
  | **asked and built:** material 10%, iron 20%, the boss 1 | 51 | 77 |

- Those materials are counted into the night's end tally in arenas, never dropped (decision 7)."""),
])
