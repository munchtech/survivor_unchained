"""Design doc: 7.3 and 9 as built, phase 3's decisions in 17, its results in 19.4."""
import os
from ed import sub
D = os.path.join(os.path.dirname(__import__("ed").ROOT), "docs", "CRAFTING_DESIGN.md")

sub(D, [
    ("""She does it at the toll-house table, in full sentences, holding the donor
over a lamp until "it lets go". If she has been accused (`vonnra.accused`),
she uses the survivor's name and charges a tenth less (the items plan's small
true consequence).
""", """She does it at the toll-house table, in full sentences, holding the donor
over a lamp until "it lets go". If she has been accused (`vonnra.accused`),
she uses the survivor's name and charges a tenth less (the items plan's small
true consequence).

**As built** (`Crafting.Bind`, `Crafting.Donors`; the bench's page as "The Toll
Tower", from her "Can you move what's in one thing into another?"): she opens
only once the toll is paid (`toll.paid`, the story lead's condition). Only
plain powers move: a caged coal stays in Brannoc's cage (her own line,
`bind.caged`), and worn skills, trophies and the slurry's powers will not let
go. The donor must be in the pack, not worn. Each bind card names the power
and the grade it comes in at, and where it comes from ("where it is grade IV; a
rare piece holds III"); the first press asks again in red ("Your Searing Silver
Ring is unmade for it. Press again to bind."), the second binds. The seam it goes
into flares with a lamp's warmth and lights rise off it, slowly (the breath she
describes going out of the old piece), not the forge's sparks.
"""),
    ("""A steeped piece is **slurried** (green-black veins, a sick glow at night), set
(heat 0), and cannot be steeped again. The card says all of this before the
jar is opened, in Snib's voice ("It is the GOOD stuff. Snib would not drink
it. Snib would not drink the bad stuff EITHER."; `crafting.json`, `snib`). **Why**: C7; the only way past the forge's ceiling, and a moral
one: the gamble exists because the stream is poisoned, and curing the stream
closes it (the jars already bought keep).
""", """A steeped piece is **slurried** (green-black veins, a sick glow at night), set
(heat 0), and cannot be steeped again. The card says all of this before the
jar is opened, in Snib's voice ("It is the GOOD stuff. Snib would not drink
it. Snib would not drink the bad stuff EITHER."; `crafting.json`, `snib`). **Why**: C7; the only way past the forge's ceiling, and a moral
one: the gamble exists because the stream is poisoned, and curing the stream
closes it (the jars already bought keep).

**As built** (`Crafting.Steep`, `Crafting.Outcome`):
- **Where.** At Snib's bench ("Sell me a jar of that.", the page "The Dig"), where
  he sells the jars and steeps in his words; and by the survivor's own hand from
  the pack (never in an arena), so a jar kept past the cure still works.
- **"Up" is always past the forge.** One power, any that can still rise, goes
  to the grade above the piece's cap (a rare's III gives IV; an epic's IV the
  bright V), or a grade finer if it was there already. The bright V is the last
  grade. A piece with nothing left to rise comes to only the veins.
- **Seen before the jar is opened.** The odds are a bar cut by their weights.
  Under each cut is what it would mean for this piece: which powers could rise or
  fall and to what, and which slurry powers fit it. The press asks again, in red.
- **Said after.** What it came to, plainly ("Hale gave a grade: +18 maximum
  health to +10 maximum health"), coloured by how it went: green for a gain,
  red for a loss, the veins' grey for nothing. The story's narration of how it
  looked follows. The seam it touched rings.
- **Set for good.** A steeped piece takes no heat back: rekindling and remaking
  are refused (`Crafting.SetForGood`), or the forge could open it again past the
  bright grade.
- **The veins are seen everywhere.** A shader runs green-black veins through the
  piece's own picture in every slot, card and anvil (`ItemViews.Steeped`).
"""),
    ("""23. **Crafts never dress the figure again**: a craft changes what a piece does, never how it looks; rebuilding the figure made her blink out of the world (seen, 19.3).
""", """23. **Crafts never dress the figure again**: a craft changes what a piece does, never how it looks; rebuilding the figure made her blink out of the world (seen, 19.3).
24. **Binding moves plain powers only**: coals stay in Brannoc's cage, and worn skills, trophies and the slurry's powers will not let go. Each of those is somebody's work or the night's; moving them would make binding the answer to everything.
25. **The donor must be in the pack**: what is worn is in use; taking it off first is a beat of choice, not a chore.
26. **Steeping by hand from the pack as well as at Snib's**: jars bought before the cure still work after it. The cure closes the sale, not the gamble already bought.
27. **The slurry's "affix" outcome adds a fourth power past the seams**, the only thing that ever breaks the seam count (5.1).
28. **Vonnra opens only once the toll is paid** (the story lead's condition): her table is the toll-house's, and she deals with those who have paid.
29. **A steeped piece takes no heat back** (19.4): rekindling or remaking it would let the forge work past the bright grade.
30. **"Up" goes past the cap however low the power was** (19.4): it lands one grade above the piece's cap. The first build only added a grade, so on an unfinished piece it was a dud that cost all its heat. The jar's words ("a grade past what the forge can do") are now true every time, and "temper first, then steep" is still the better order.
"""),
])
