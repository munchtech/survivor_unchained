from ed import sub
D = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7debf1459f14dfe7\docs\CRAFTING_DESIGN.md"
sub(D, [
("""17. **Break down yields halved; a shard per 12 ember, not 8** (19.2): measured, iron and shards piled up unspent (190 iron and 100 shards by Act 1's end).
""",
"""17. **Break down yields halved; a shard per 12 ember, not 8** (19.2): measured, iron and shards piled up unspent (190 iron and 100 shards by Act 1's end).
18. **Arena gold cut, by combat** (19.2): champions 7% of the day's rate, fodder 0.15%, bosses and minibosses in full. A Kerchief night pays about 350 gold (it paid 2.5k–3.3k), still three to thirty times another people's night.
19. **Wenna brews from the start; only her tinctures wait for the cure** (a verb's gate, `crafters.wenna.gates`): brewing is the herbalist's trade and nursing the Verge is what she is doing; stitching your coat is what she has no time for.
20. **The still-room is a side panel, not a page** (the owner: full pages are often not the best choice): brewing is an errand on the way out of town; her bench, which works gear, is the forge's page in her place.
21. **The draught key drinks the moonpetal only for a deep wound** (55% of health gone; combat's rule): a rare draught spent on a scratch would feel like a theft.
22. **A trophy is set outside the seams** (`ItemInstance.Setting`): Greymuzzle's fang leads the piece's name, spends no heat and takes no seam, so the one fang in the game never competes with the forge's work.
23. **Crafts never dress the figure again**: a craft changes what a piece does, never how it looks; rebuilding the figure made her blink out of the world (seen, 19.3).
"""),
("""---

## 20. The endgame: the atlas and the scars""",
"""### 19.3 Phase 2, built and seen (October 2026)

Built: Wenna's still-room (`src/Ui/StillRoom.cs`, a side panel: health draught 2 bitterroot + 4 gold,
antidote 1 + 3, the moonpetal draught 1 moonpetal + 10, "Brew N" for as many as the pouch allows to
five; her flask, 120 gold, tops health draughts up to three at the inn, a bitterroot each, said in
the morning report); her bench (the forge's page, `forge:wenna`) once the stream is clean, her
trust or affection 30 putting what she works in a grade finer; Brannoc's commissions ("Make me
one" on the forge's bench column: a pattern, a material's answer, Uncommon at grade I, full heat,
next morning, his "!" over his head when it is ready; chain shirt and the watch shield at respect
20); Greymuzzle's fang ("Greymuzzle's fang. Will you set it?" while held; set in a weapon or amulet:
*Greymuzzle's*, +30% to wolves and beasts; Maeca's once-only "That's his." the first time she sees
it worn, -10 affection); Maeca's braid of shed fur (offered once the Pack is allied, ready the next
day, a Rare amulet, 30% less from wolves). Painted icons for the new things (the UI art pipeline).
Tests: `tests/CraftersTests.cs`.

Seen at 1920×1080, and what was done:

| Seen | Done |
|---|---|
| After a temper the anvil just changed: nothing struck | The hammer's moment: the seam's row flares and cools, streak sparks fly off its badge, the heat it took burns out of the gauge ("4 heat spent: 14 of 18"), then the next craft's preview; a count of blows on the anvil (`Sfx.Anvil`) |
| The moment fired on a page already rebuilt (a craft builds the page twice) and crashed | It plays once, a moment later, on the page as it stands |
| Work in over a seam whose answer the piece already had: a heading and nothing under it | Said why ("It has of the Wolf in it already...") and what else would give it something |
| "over of the Lantern, which is lost" | "in place of “of the Lantern”, which is lost" |
| The moonpetal draught and the flask as flat white photographs beside painted icons | Painted icons, the set's own prompt |
| Wenna's bench offered to work over the piece's affix first | Starts at the open seam |
| Pack break down: no word of what it came to (toasts are under the pack); the survivor blinked out | The ask in red; "Broken down: ... 2 old iron, into the pouch" in the reading place; crafts no longer dress the figure again |
| A real arena's end after a fall past the win carried every shard | Fixed: the zone hears of a fall before the battle marks her dead; a fall is now known by its killer (`ArenaTests.A_fall_after_the_win_spills_half_of_what_the_night_gave`) |

---

## 20. The endgame: the atlas and the scars"""),
("""| Measure | Target | Before tuning | After (today's gold) | After (champion gold at a tenth) |
|---|---|---|---|---|
| First craft | day 1–2 | 1 | 1 | 1 |
| Crafts a day (median, max) | 2–5 | 1 (23) | 2 (14) | 2 (11) |
| Weapon rare / epic | day 3–4 / 6–8 | 4 / 4 | 4 / 5 | 4 / 8 |
| Pieces the forge finished | 0–2 | 7–8 (measured loosely) | 2 | 1 |
| Gold spent on crafting | 30–60% | 17% | 19% | 67% |
| Shards a won night | 4–8 | 9 | 7 | 7 |
| Unspent at the end: iron, shards | – | 190, 100 | – | 52, 77 |""",
"""| Measure | Target | Before tuning | After (the old arena gold) | After (arena gold cut, measured) |
|---|---|---|---|---|
| First craft | day 1–2 | 1 | 1 | 1 |
| Crafts a day (median, max) | 2–5 | 1 (23) | 2 (14) | 2 (11) |
| Weapon rare / epic | day 3–4 / 6–8 | 4 / 4 | 4 / 5 | 4 / 8 |
| Pieces the forge finished | 0–2 | 7–8 (measured loosely) | 2 | 1 |
| Gold spent on crafting | 30–60% | 17% | 19% | 67% |
| Shards a won night | 4–8 | 9 | 7 | 7 |
| Unspent at the end: iron, shards | – | 190, 100 | – | 52, 77 |

**The cut, built by combat and measured** (`CraftingProbe` at 4c32586, 96 arenas): a Kerchief night
pays 375 / 351 / 365 gold at tiers 1–3 (it paid 2.5k–3.3k), the other peoples' 11–35. The first cut
(champions to a tenth) left 1.6k–2.1k: the fodder, not the champions, paid most of it, so fodder went
to 0.15% and champions to 7%. A sweep of a Kerchief night's gold in the simulation found the cliff:
above about 500 a night, gold gates nothing and the weapon is Epic on day 5 whatever. The test reads
an arena's real rates and fails if they move without a re-probe."""),
])
