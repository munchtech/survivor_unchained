"""Design doc: 19.4 (phase 3 seen and remade), 20.6 reordered as built, 20.7 what was built."""
import os
from ed import sub
D = os.path.join(os.path.dirname(__import__("ed").ROOT), "docs", "CRAFTING_DESIGN.md")
sub(D, [
    ("""| A real arena's end after a fall past the win carried every shard | Fixed: the zone hears of a fall before the battle marks her dead; a fall is now known by its killer (`ArenaTests.A_fall_after_the_win_spills_half_of_what_the_night_gave`) |
""", """| A real arena's end after a fall past the win carried every shard | Fixed: the zone hears of a fall before the battle marks her dead; a fall is now known by its killer (`ArenaTests.A_fall_after_the_win_spills_half_of_what_the_night_gave`) |

### 19.4 Phase 3, seen at 1920×1080 and remade (October 2026)

| Seen | Done |
|---|---|
| Vonnra's long name widened her column past its rail: the rail ran through her portrait and her words | The name's plaque fits the column (shorter rules, then a smaller face); the column keeps to 360 |
| Her first binding's narration (about 490 letters) would not fit under the terms | What a crafter says sits under them, before their terms; mood and prices on one line; the portrait 330 high |
| "A tenth off every price, at after you have accused her" | A standing is reached ("at respect 20"); a deed is done ("after you have accused her") |
| Bind cards read "Searing from Searing Silver Ring", with no grade, and the grade a rare piece holds was not said | "Searing, at grade III"; "Out of your Searing Silver Ring, which is unmade (grade IV there; a rare piece holds III)" |
| A binding rang nothing: no seam lit, no moment | The seam it went into flares with lamp-light, and lights rise off it slowly: her breath going out of the old piece, not the forge's sparks |
| Snib's bench: no figure, no name, a weapon with no seams on the anvil, refusing | Snib drawn as he is (the lampling in his hat and lamp, `Portrait.Of(Beasts.Def)`), his name and calling; a piece the jar can take put down first |
| The odds a wall of blue text | A bar cut by the weights; under each cut, what it would mean for this piece ("Hale II to IV"; the slurry powers that fit it) |
| After a steep, nothing said what it came to | "What the jar did", plainly, coloured by how it went; the seam it touched rings green; the story's narration after |
| A steeped piece looked like any other; Brannoc offered to rekindle and remake it | Green-black veins run through its picture everywhere (a shader on the picture itself); rekindling and remaking it are refused |
| The pack's steep said only the narration, then cleared the card | It keeps the piece chosen, says what the jar did over its card, and shows the same odds bar under it while a jar is carried |
| The bright grade V read as any other numeral | It reads as light: a pale numeral with a green glow, on the card and the badge |
| Asked twice, in red, for what cannot be undone | Held (UI design's rule for every screen): the press fills over 0.8 s, a tap only nudges it (`Style.HoldButton`) |
| A commission's "!" fell into Brannoc's two-line name plate and read as a letter | The mark stands clear above the plate, measured in the plate's pixels; the piece handed over rings in gold, "made for you, ready this morning"; his greeting says it ("Cooled overnight. Come and look.") |
| The moonpetal brew's row glow | Seen, kept |

Owed, Godot and the GPU permitting: the painted icons for the slurry jar and the four rulers' things (prompts in
`tools/uiforge/items.py`, to agree with the UI art lead); the moonpetal draught's and flask's icons imported in this
worktree; the hold presses, marks and charts seen in the running game.
"""),
    ("""### 20.6 What to build, in order (after phases 2 and 3)

1. Two kits (pack and table).
2. Item level on gear and grade caps by item level (with combat's map loot).
3. Chart verbs at the table (when combat's chart item exists).
4. Marks (when combat agrees the skill hooks).
5. Higher grades and remake to Legendary (Act 2's hands).""",
     """### 20.6 What to build, in order (after phases 2 and 3)

Reordered (October 2026): the two pieces that are crafting's own came first. Two kits wait for UI design's
pack, which is being redone from research.

1. Marks on the item side (built, 20.7).
2. Chart verbs at the table (built, 20.7).
3. Item level on gear and grade odds by item level (with combat's map loot).
4. Two kits (pack and table), with UI design's new pack.
5. Higher grades and remake to Legendary (Act 2's hands).

### 20.7 What was built (October 2026)

**Marks** (`Crafting.Inscribe`, `RulerMark`; combat's `Sim/Marks.cs` hook):
- **Where they come from.** A map's ruler leaves its people's thing half the time. Each thing carries how
  that people fought, and the story lead named them:

  | People | Thing | Mark |
  |---|---|---|
  | The Pack | the Tally-Bone | of the Long Chase: Volley looses a second volley at the farthest foe |
  | The lamplings | the Cracked Lamp-Glass | of the Falling Star: Cinderfall leaves burning ground |
  | The Risen | the Bent Barrow-Nail | of the Open Gate: the dash leaves a ring of holy fire |
  | The Kerchiefs | the Muster-Cord | of the Muster: Axe Gyre gains axes in a crowd |

- **Grades.** A thing falls at a grade by the map's tier: a grade every three tiers, sometimes one finer, to VI.
  The grade is the Mark's strength, 0 to 1. Tier 1 gives I or II.
- **At Vonnra's table.** She writes it into a seam: open, or in place of a chosen power. The thing is used up.
  One Mark to a piece; a second goes where the first was. No forge tempers a Mark: a finer one comes from a
  harder map. It costs 2 shards, 60 gold and 30 a grade, and 5–7 heat.
- **Worn.** The kit carries three into the maps (the same Mark twice is the finer). It does nothing at night.
- **Why seams.** A Mark costs a seam, as a support gem costs a socket in Path of Exile. Without that a kit of
  three would be free power. The cost is the build choice.

**Charts at the Wayfinder's table** (`CraftingCharts.cs`; the bench page with charts on its anvil, opened from
the table's "Work it first"):
- A chart has heat: plain 4, fine 6, rare 8.
- **Ink** a side: a random mod for the foe or against you. 1 shard and gold by tier; heat 2–3.
- **Burn and redraw:** every mod but the pinned one, as many on each side as before. 2 shards; heat 2–3.
- **Pin** one mod. It holds through a burn; one pin a chart, and a new one moves it. 2 of the people's own
  material; heat 1.
- **Scrape** one mod off. 3 old iron; heat 1–2.
- **Annotate:** +5% found, to 20%, written in from another chart of the same people's ground, which is given
  up. Gold; no heat.
- A chart's rarity follows its mods: plain, fine to two, rare from three.
- Ysolde's words are the story lead's. Two carry her secret unsaid: the pin ("Everybody's got one of those")
  and the annotate (the chart given up "goes into a drawer, not the fire").

**Rook's shelves** (the owner's approval of UI design's proposal; `Crafting.ShelfPrice`, `BuyShelf`):
- The storeroom comes with one shelf of 24. More cost 300, 1,000 and 2,500 gold, then 5,000 each, to eight.
- **Why these prices.** Act 1 earns about 1,600 gold in the simulation and crafting spends two thirds of it.
  So the second shelf is about a Kerchief night's gold: a choice late in Act 1 or early in the atlas, not a
  tax on the forge. The later shelves are the atlas's sinks, and are to be re-measured when the maps' gold
  is (Last Epoch's and Grim Dawn's stash tabs also rise in price).
- A save from before shelves keeps its 48 places as two shelves."""),
])
