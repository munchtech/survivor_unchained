from ed import sub
import os
D = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\docs\CRAFTING_DESIGN.md"

sub(D, [
("""the night kit is coals and the people's answers; the map kit is the build.
Swapping is free and only done at the table or the Waystation. (A UI and pack
change: the UI design lead's and mine; no new item rules.)
""",
"""the night kit is coals and the people's answers; the map kit is the build.
Swapping is free and only done at the table or the Waystation. (A UI and pack
change: the UI design lead's and mine; no new item rules.)

**As built** (`Rpg/Kits.cs`, October 2026), two changes to the above, both for "no chores":
- **The kit goes on by itself with the place**: the night's wherever the ember burns (the scars, the story
  nights, a lit night on the Verge), the day's everywhere else, the maps among them. There is no swap to
  remember, and none at the table.
- **The night kit holds only what differs.** It starts empty, and a slot with nothing of its own wears the
  day's piece ("as by day"). A survivor who never thinks about it is dressed the same day and night.
- A piece in the kit not on now is set aside (`Store.Kit`): it is neither worn nor carried, the forge can
  still find it, and nothing can be pulled out from under the kits.
- The Pack's switch ("By day · By night") is UI design's. It shows once a coal or a Mark is owned.
"""),
("""- Those materials are counted into the night's end tally in arenas, never dropped (decision 7).
""",
"""- Those materials are counted into the night's end tally in arenas, never dropped (decision 7).

### 20.8 Seen and measured (October 2026)

**Seen at 1920×1080:**

| Seen | Done |
|---|---|
| A scar left after an hour and five minutes past the win, the stream cured: 50 shards and a scar-glass, with the story's line for the glass | Kept. The scar-glass icon is a placeholder star (UI art is painting it) |
| Fallen at the same depth: 25 shards kept, 25 spilled, the one scar-glass spilled. The spilled one was named "pieces of scar-glass" | One spilled thing is named as one |
| A whole map cleared: its charts and the ruler's Mark lay where the ruler fell, and were lost when the map ended unless walked over | Gathered home with the rest (`Journey.Gather`) |
| A ruler's Mark coming home ("Muster-Cord of the Muster, Rare trophy") and Vonnra inscribing a Tally-Bone into a seam: the violet grade badge, the motes, "Marked. It will do it that way now, until it breaks." | Kept. Vonnra's model reads as a placeholder, handed to the creatures lead |

**The atlas's pay, measured** (the balance lab's `map` sweep, now reporting material, shards, iron and
Marks: tiers 1, 4 and 7, warden and arcanist, the four peoples, a map about ten minutes):

| A played map paid | Before | After |
|---|---|---|
| Gear | 11–13 pieces (about 22 old iron broken down) | the same |
| Gold | about 40; a Kerchief map about 650 | the same |
| The people's own | 74–102 | 15–18 |
| Ember shards on a lamplings map | 73 | about 2 (the carriers' non-gear rolls) |
| Old iron on a lamplings map (gear broken down, and their own) | 23 | 36 |
| Charts / Marks | 2 / 0.3 | the same |

- **Why the people's own was cut**: a quarter of every kill paid it, so a ten-minute map paid ten nights'
  worth, where a pin takes two and a work-in three. It now comes from what visibly carries it: the ruler
  three, a keeper two, a pack's leader one, the rank and file none (`MapRun.OnLoot`).
- **Why the lamplings pay iron in the atlas**: their ember shards are the night's. A lamplings map paid a
  long scar's worth of fire, which undid 20.1 (fire is the scars', iron the atlas's). In the atlas the
  Dig's lamplings carry its picks and nails.
- **Gold against the shelves**: mapping pays about 1,000 gold an hour across the four peoples, nearly all
  of it from the Kerchiefs, who carry coin. The third shelf (2,500) is a few hours of maps, and each 5,000
  shelf about five. They stay as priced: the atlas's long sinks.
- **To see it**: `--zone map --tier T --people P --lab --clear 3 --leave 16` fells a whole map at once and
  logs what it paid ("map paid: ..."); `--zone arena --minute 95 --won --facts stream.clear=true --lab
  --leave 2` is a scar left an hour past the win.
"""),
])
