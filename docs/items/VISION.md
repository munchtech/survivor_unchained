# Vision: what items are for in Survivor Unchained

## The one-line version

**Gear is what the survivor keeps.** The ember is borrowed each night and lost
each dawn; the blade, the coat, the lamp at the hip and the ring that was taken
back from the thing that killed you are what come home. Items are the day's
memory of the night, and the night's head start from the day.

That sentence is the test for every rule in this folder.

---

## 1. What items are for here

The game has two halves (`HANDOFF.md`): by day a story walked and talked through,
with character levels, learned skills and fixed fights; by night the ember arenas,
thirty minutes of a survivors-style build that starts at nothing and stays in the
arena. Most action RPGs have one loop for gear to serve. This one has two, and
gear is the only power that crosses between them (with levels, attributes and the
art in hand). So items here have four jobs, in this order:

1. **Carry the survivor across the dawn.** Gear is persistent power in a game
   where the most dramatic power (the ember) resets nightly. It must feel like the
   thing you built, not the thing you rented.
2. **Shape the night without owning it.** Gear decides *how* the ember burns
   (which skill you walk in with, which cards come, which evolution is in reach),
   while the ember decides *how bright*. A geared survivor drafts differently and
   starts faster; they still have to build. (`SYSTEM.md` §11.5 is the contract.)
3. **Make the day's choices visible.** Items carry the world: a wolf-fang
   necklace is a statement to a wolf, a red kerchief makes you a Kerchief to the
   Kerchiefs and to the Watch. Named items come from people and places, and a few
   of them only exist because of what you chose (`ACQUISITION.md` §6).
4. **Tell the story in the margins.** Elden Ring and Dark Souls taught a
   generation of players to read a world through its item descriptions. This world
   has a deep, layered secret (`STORY_BIBLE.md`), revealed act by act. Item lore is
   one of the safest, quietest places to plant it: every Named item says one true
   thing, never the answer.

## 2. The feel we want, low to high

| Moment | What it should feel like | The design that delivers it |
|---|---|---|
| Act 1, a Fine cap off a Kerchief | "That's better than mine." A small, readable win. | Fine items with one or two plain affixes; a compare arrow that is green. |
| The first Rare | A name ("Cold Supper") and a blue beam; a choice between two good things. | Rares named in the game's voice; affixes that change a decision. |
| The first Marked item | "This changes how my art works." Planning starts. | Marks: rules, not numbers, on skills and arts the survivor uses by day. |
| The first Named drop | A pillar of amber across the whole arena, and the toll bell. A lore line that makes you sit up. | Presentation (`IMPLEMENTATION.md` phase 2); lore tied to the story. |
| A set completing | "I look like one of them now." | Sets that change the figure (`VISUALS.md` §5). |
| Taking an item back from your nemesis | Revenge with a receipt. | History lines; Storied items (`SYSTEM.md` §9). |
| Act 3, a Heartwrought base | The pale, ember-veined thing nobody living made. | A fifth base tier that looks unlike the rest. |
| Endgame, a bright roll on a Named item | The long tail. A sound you have heard four times in a hundred hours. | Bright affixes; Storied lifts; the depths. |

## 3. Principles

These are the rules the system follows. Each comes from the genre's hard lessons
(`RESEARCH.md`, numbered lessons in brackets) fitted to this game.

**1. Fewer drops, each worth looking at.** [1, 2] Arena hordes reach hundreds of
creatures; if every tenth one dropped gear the screen would be confetti and the
pack full in a minute. Gear drops come from champions, heralds, chests and the
boss, and the spoils screen gathers them (`SYSTEM.md` §12). A run should end with
a handful of items, at least one of them worth a second look.

**2. Readable in two seconds.** [2, 4] At most four affixes. No "damage while
standing still to Vulnerable enemies on Tuesdays" (Diablo IV's launch affix soup,
`RESEARCH.md` §3). Each affix changes a decision. The tooltip leads with the
power, then the numbers. Ranges and grades are there for anyone who holds Alt.

**3. Rules over numbers at the top.** [3] A Mark, a Named power or a set bonus
changes how a skill, an art or the dash works. Numbers climb too, but what a
player remembers is "my Shield Bash pulls them in now".

**4. Few multipliers, all named.** [4, 25] Gear's damage bonuses are *increased*,
so they add with the ember's passives instead of multiplying them; the "more"
multipliers are few (the weapon's Edge, one per Named power) and each is written
on its item. This keeps the arena a survivors game at every gear level, keeps the
numbers small enough to read, and leaves room for twenty years of content without
a stat squish.

**5. Sets are small and loose.** [5] Three or four pieces; they mix with uniques;
no set bonus multiplies one skill by thousands of percent (Diablo III, `RESEARCH.md`
§2). A ring that makes a set count one piece more frees a slot for a unique.

**6. A known jackpot, and a visible exception.** [6, 7] Everyone should know
what the top looks like: a Storied Heartwrought weapon with a bright Edge. Bright
affixes are marked with an ember star the moment they drop.

**7. Random drops beside certain paths.** [8, 19] Every Named item has a home
(a people, a boss, a person) that can be farmed; every Mark, once seen, is in the
binders' book forever; every Watchword is a recipe. Luck decides *when*, the
player decides *what*.

**8. Duplicates and failures become progress.** [9, 10, 11] Salvage everything to
something; a better copy of a Mark upgrades the book; a run with no Named item
moves a visible tally toward the next. A craft never destroys the item it fails on
(Lost Ark's honing is the warning, `RESEARCH.md` §7). Heat runs out; nothing breaks.

**9. Show the odds.** [12, 13] Crafting shows its cost, its chance and its range
before the click (Last Epoch's transparency). The one deliberate gamble, steeping
an item in the Dig's slurry, says so in plain words and is optional.

**10. Downsides that make items contextual.** [17] Half the Named items and most
relics have a price ("8% slower. It weighs what it weighs."). Darkest Dungeon's
trinkets and the Ashen Plate already in `items.json` are the model.

**11. Gear speaks to the world.** Kept from today's design and widened: about a
third of Named items carry a world tag. The world's reaction is part of the
item's value, and sometimes all of it.

**12. Self-found, no trade.** [21] A single-player story game: everything is
balanced for the survivor's own finds. No auction house, no trade, no gold that
buys power directly. Gold buys services (crafting, gambling at the toll, stash
space, a tailor), never a best-in-slot.

**13. Persistent unlocks widen, they don't only raise.** [28] Between nights,
gear should open builds (a worn skill, a catalyst, a Mark on an art) at least as
often as it adds power. The ember is the night's power curve; gear is its range
of possibility.

**14. No chores.** [23, 24] No identifying. No town trips from an arena.
Materials take no slots. A loot filter from the first build. Salvage from the
spoils screen. A tailor, so you never wear something ugly for its stats.

## 4. Tone

Dark fantasy, in this world's register: plain, worn, specific, and quietly sad.

- **Names are nouns people would use.** "Brannoc's Twelfth Iron", not "Blade of
  Eternal Shadowflame". Rares are named like pub signs and ballads ("Low Water",
  "Patient Wall"). Prefixes and suffixes are craft words and places
  ("Watchman's", "of the Hearth").
- **Lore lines are one image, in a person's or the narrator's voice**
  (`VOICES.md`): present tense, plain nouns, never two adjectives where one will
  do, never says what it means. "It is still warm, and it is still his, and he will
  want it back."
- **Materials tell the history of the valley.** Worn is rags and old iron; Sound is
  the Watch's stores; Wrought is the Vigil's armourers; Legion is the old empire's
  red lacquer and bronze; Heartwrought is pale bone-plate and ember veins: the
  Morrow's own. The survivor's look walks down the same stair the story does.
- **Ember glows only at night.** The highest gear's veins and runes are dark by day
  and burn in the arenas, as the survivor does (`VISUALS.md` §6). Players will
  notice before the story tells them why.

## 5. What to avoid

| Avoid | Because | Instead |
|---|---|---|
| Gear that makes the arena trivial at minute one | It kills the survivors half: the ember must still be the night's climb. | Inc-not-More; rank-4 cap on gear skills; kindled caps. |
| Gear that is irrelevant in the arena | Then the night has no reason to want the day. | Edge, kindled affixes, catalysts, Marks on tags and arts. |
| Six-piece sets, one build per calling | Diablo III. | Small sets, loose bonuses, the Ring of the Seventh. |
| A hundred affixes | Diablo IV at launch. | About sixty, in groups; four per item. |
| Magic find on gear | Diablo II's "swap to the MF kit", and a stat that makes you weaker in exchange for a spreadsheet. | Better loot comes from harder maps, oaths and target farming; Luck stays a card stat. |
| Crafting that can ruin an item | Lost Ark, Torchlight's wipes. | Heat: a craft can fail to improve, never destroy. |
| Twelve currencies | PoE2's early scarcity; screens of orbs. | Seven materials (`CRAFTING.md` §1), plus the world's own (pelts, petals). |
| Lore that spoils | `STORY_BIBLE.md`: no answer before its act. | Each lore line is tagged with the act it is safe from (`CATALOGUE.md`). |
| A best-in-slot list | The end of play. | Every slot has two or three strong options that pull different ways. |
| Gear only by stats, not by look | A survivor in a level-30 body armour that looks like level 1. | The figure follows the gear; a tailor for those who prefer otherwise. |

## 6. How this plan is organised

`SYSTEM.md` is the machine. `ACQUISITION.md` and `CRAFTING.md` are how gear comes
in and how it is changed. `PROGRESSION.md` is the curves and the balance between
gear and ember. `CATALOGUE.md` is the content. `VISUALS.md` is the look.
`IMPLEMENTATION.md` is the build order, mapped to the code. `README.md` has the
top ten recommendations.
