# Crafting: the design

How the survivor makes and remakes what they keep, in this valley and no
other: what the night yields, what the Waystation's hands make of it between
nights, the numbers that hold it, and the order it is built in. The research
behind it is `CRAFTING_RESEARCH.md` (its lessons are cited as C1 to C30).
It builds on what the game already has (`godot/logic/Rpg/Items.cs`,
`Rpg/Character.cs`, `Play/Journey.cs`, `Arena/Arena.cs`, `Play/Zones/*`,
`data/content/*.json`) and on two plans that came before it: the items plan
(`docs/items/`, a design with nothing built; this design takes its heat,
its crafters and its rules, and cuts or changes the rest, section 18) and the
skills design (`SKILLS_DESIGN.md`, built; this design feeds its evolutions
and never owns them, section 12).

Every number here is a proposal held by a test or a simulation (section 14)
and is the balance lab's to move.

---

## 1. The idea in one page

**Gear is what the survivor keeps; the ember is what the night lends.**
Crafting is how the day turns what the night left behind into something kept,
by the hands of the people who live here.

- **Three things go into anything made here: iron, the world's own, and
  fire.** *Iron* (old iron, from breaking down what you don't keep) gives a
  piece its body: grades and a better make. *The world's own* (wolf pelts,
  boar hide, red cloth, barrow dust, ember shards, bitterroot, moonpetal)
  gives it its kind: each material becomes the answer to the danger it came
  from. *Fire* (ember shards, carried out of the night) gives it the ember's
  shape: a coal caged in the piece that bends the night's draft, and the heat
  to work it again. Brannoc says it in six words: "Iron for the shape. Fur for
  the kind." The fire he doesn't name.
- **Every piece has a life: its heat.** A hot piece can be worked; each craft
  spends heat; at none the piece is set, for good. Heat is shown, its cost is
  shown before the hammer falls, and running out never breaks anything. A
  great find is a great base *with heat in it* (C5, C6).
- **Choose what; luck decides how good; heat decides how often** (C3). The
  survivor chooses the affix to raise, the material to work in, which of
  three coals to cage. Luck lives in the drops (the base, its rarity, its
  heat), in a small range on each heat cost, and in the three coals offered.
  The best of everything still comes from the world, not the forge (C8).
- **Each craft is done by someone, in their place, in their voice** (C17).
  Brannoc at the forge works iron, hide and coal. Wenna in her still-room
  brews and works the herbs. Vonnra at the toll binds one piece's power into
  another. Snib, while the Dig still pumps, sells the one gamble. How they
  feel about you sets their terms (C18); the story opens their crafts and can
  take a crafter away, moving the work to a worse pair of hands rather than
  deleting it (C19).
- **The night pays in what it is.** A won arena sends the survivor out with
  ember shards (more the longer they stayed past the half hour, half of them
  spilled if they fall: the run's last decision, C21) and with the people's
  own materials: the Pack's pelts and hides, the Risen's barrow dust, the
  Lamplings' shards, the Kerchiefs' red cloth. Choosing a map at the
  Wayfinder's table is choosing what to make (C14).
- **The danger answers itself** (C13). Wolf pelt makes a piece *of the Wolf*
  or a blade *Wolfbane*; barrow dust makes it *of the Grave* or *Gravebane*;
  boar hide keeps out the cold and steadies the feet; ember shards turn fire
  and light. The oaths and peoples the table offers are answered by what
  their own fights yield.
- **Crafting feeds the night's evolutions without owning them** (section 12).
  A caged coal is a kindled affix: it may stand in for a passive in an
  evolution's recipe, and the forge offers three, leaning toward what your
  carried skills evolve with. The ember still has to climb to rank 8; gear
  still never brings an evolution, a blessing or a rank past four.
- **No chores** (C24, C25, C27). Materials go in a pouch, not the pack. Every
  unwanted piece breaks down to old iron (C9). No crafting junk to level a
  skill; no recipes on a wiki (C15, C16); a draught brewed once is refilled at
  the inn (phase 2).
- **What lies under it.** Ember is the held dead, leaking up (`STORY_BIBLE.md`
  section 1, said in Act 3). Every coal the survivor carries out and has caged
  in their gear is somebody's light. Act 1 never says it; the crafts carry its
  seeds (section 11.4). By Act 3 the survivor's best gear has names in it.

**Soul test.** Could this crafting belong to another game? Its three
ingredients are this valley's (the Watch's old iron, the Verge's beasts, the
night's ember); its smith forged the irons that drowned his daughter and
cages coals in your sword the way he caged them in the ford's lamps; its
binder holds one thing's power in another the way her family held the chain;
its gamble is the Dig's poison, sold by the one person who survives
everything, and exists only while the stream is poisoned. The mechanics are
the story's facts.

---

## 2. What exists today, and what is wrong with it

Read from the code (October 2026, `claude/vigilant-galileo-l6jqyx`).

| Thing | Today | Problem |
|---|---|---|
| Materials | Seven: wolf pelt, boar hide, red cloth, barrow dust, ember shard, bitterroot, moonpetal (`items.json`, stack 20 or 10, in the 24-place pack) | Their only uses: sell, Holloway's bounty, five pelts for the wolfhide cloak, quest checks. They clog the pack (C27). |
| Where they come from | By day in the Verge (`Verge.OnLoot`: pelts 55% of wolves, hides 50% of boars, cloth 30% of Kerchiefs, shards 18% of lamplings, dust 25% of the dead; bitterroot and moonpetal gathered) and the prologue's shards | The arena, half the game, yields none (C1, C14). |
| Gear | Rarity 0 to 5 (Common to Storied); plain bases roll `min(3, rarity)` affixes at grades 0 to 3 (`Inventory.Make`); named things never roll; the weapon is a skill brought in at a rank (rarity raises it, capped at 4) | Two drops of a rarity differ only in which affixes; a beloved piece can never improve (C12). |
| Kindled affixes | Built (`AffixDef.Kindled`): spark, reroll, refusal, roads, omens, and twelve stand-ins for passives in evolution recipes; one an item, two a survivor; a stand-in rolls twice as often when the carried skills evolve with it | Only luck finds them. **Bug**: two stand-ins share ids with plain affixes (`of_mending`, `of_embers`), so a rolled stand-in for Bitterroot or Emberblood reads back as the plain one and never stands in (fixed in phase 1, section 12.2). |
| Brannoc | Sells; buys pelts at 8 and hides at 6 (`sellpelts`); makes the wolfhide cloak (5 pelts, 30 gold, in dialogue); "reforges" the weapon (`Journey.Service("reforge")`: rarity +1 for 40 × (rarity + 1) gold, to rarity 4) | The reforge is the only gear improvement in the game: a flat gold-for-rank trade with no choice in it. |
| Gold | In: Kerchief fodder and every champion and boss drop it in arenas; quests (about 800 across Act 1's branches); selling. Out: shops, rest (5), bribes and the story's prices (about 500), the reforge | Few sinks after the first days (measured in section 13). |
| The arena's spoils | Experience by time, gold picked up, gear from champions and the boss's chest, a manual, a tome, skills discovered (`Arenas.Finish`) | Nothing from the night is made into anything (C21). |

---

## 3. Principles

Each is a lesson from the research, fitted to this game.

1. **Gather from what you already do** (C1). No gathering job: materials
   come from fights by day and night, from breaking down what you don't
   keep, and from a few herbs on the walk.
2. **Choose what, let luck decide how good, show the budget** (C3, C4).
3. **Every piece has a life; failure spends it, never the piece** (C5, C6).
4. **The forge's ceiling sits below the world's** (C8): crafting raises a
   piece to what the best drop of its rarity could have been, and no further;
   Legendary pieces come only from the world in Act 1; the bright grade only
   from the one gamble.
5. **No dead drops** (C9): everything breaks down to something.
6. **The danger answers itself; where you go is what you make** (C13, C14).
7. **Done by someone, on their terms** (C17, C18, C19).
8. **Discovery by touch and by people** (C15, C16): a craft shows when you
   carry what it needs and know who does it.
9. **The night stays the night's** (`SKILLS_DESIGN.md` section 10): crafting
   shapes the draft, never the ember's power.
10. **No chores, no bloat** (C24, C25, C27): a pouch; one press for every
    repeat; no levelling a craft.
11. **Self-found** (C29): gold buys work, never a best piece.

---

## 4. Materials: iron, the world's own, and fire

### 4.1 The list

Ten materials in Act 1, three of them new. All go in **the pouch** (4.3).

| Material | Id | Kind | From | Used for |
|---|---|---|---|---|
| **Old iron** | `old_iron` (new) | iron | breaking down gear (5.2); Brannoc sells 10 a restock at 6 gold each | tempering, remaking |
| **Wolf pelt** | `wolf_pelt` | the world's own | wolves by day (55%) and the Pack's arenas | *of the Wolf*, *Wolfbane*; the wolfhide cloak |
| **Boar hide** | `boar_hide` | the world's own | boars by day (50%) and the Pack's arenas | *Sturdy*, *of the Hearth*, *Surefooted* |
| **Red cloth** | `kerchief_cloth` | the world's own | Kerchiefs by day (30%) and their arenas | *Watchman's* |
| **Barrow dust** | `bone_dust` | the world's own | the dead by day (25%) and the Risen's arenas | *of the Grave*, *Gravebane* |
| **Ember shard** | `ember_shard` | the world's own and fire | lamplings by day (18%), the prologue, every arena's end (6.1), the Lamplings' arenas | *of the Salamander*, *Lampsnuffer's*, *of the Lantern*; caging a coal; rekindling |
| **Bitterroot** | `bitterroot` | the world's own (Wenna) | the green stretch while the stream is poisoned | *of the Physician*; draughts (phase 2) |
| **Moonpetal** | `moonpetal` | the world's own (Wenna) | the moon grove | *of Mending*; a stronger draught (phase 2) |
| **Slurry jar** | `slurry_jar` (new, phase 3) | the gamble | Snib, while the Dig pumps | steeping (section 9) |
| **Shed fur** | `shed_fur` (new, phase 3, story's call) | the world's own | the Pack, when allied | a charm Maeca braids (section 10.3) |

**Why so few.** Hades II's dozen currencies and Grim Dawn's fragments are the
bloat warnings (C27). Each material here has one source people and one job,
and the people are the Wayfinder's four plus the Verge's beasts, so the list
is the world's list. New acts add their own few (section 16).

### 4.2 Why ember shards are the fire

The ember is the night's power and goes out at dawn; the shards are what it
leaves in the survivor's fist, cooled. Making them the fire (the coal caged
in a piece, the heat that lets it be worked again) ties the night to the day
in one object the game already has, and plants the reveal: the thing that
makes your best gear better is the light of the valley's dead (11.4).

### 4.3 The pouch

Materials never take a place in the pack. `CharacterData.Materials`
(material id to count, no limit) holds them; the pack's **Materials** filter
shows the pouch; shops buy from it; quests that ask for or take a material
(`hasItem`, `take`, `give`) read and write it through `Inventory.Count`,
`Inventory.Take` and `Inventory.AddToPack`, so the story's data does not
change. A save from before is migrated: materials in the pack move to the
pouch (save version 3).

**Why**: the pack is 24 places; seven stacks of materials were a third of it.
Every ARPG that kept materials in the pack moved them out (Diablo IV, Last
Epoch, Path of Exile's stash tabs). The pouch also makes the forge's
question ("do I have enough?") answerable at a glance.

---

## 5. Heat, grades and seams: what a piece is made of

### 5.1 The numbers on a piece

| Rarity | Seams (affix places) | Grade cap at the forge | Heat at drop (±20%) | Break down yields |
|---|---|---|---|---|
| Common (0) | 0 | – | 6 | 1 old iron |
| Uncommon (1) | 1 | II | 10 | 1 |
| Rare (2) | 2 | III | 14 | 2 |
| Epic (3) | 3 | IV | 18 | 3 |
| Legendary (4) | 3 | IV | 22 | 5 |
| Storied (5) | 3 | IV | 22 | cannot be broken down |

- **Grades** are the affix tiers the game already has (0 to 3), shown as I to
  IV. Each grade's value is fixed (`AffixDef.Mods(tier)`): the grade *is* the
  roll, readable in two seconds. A **bright** grade V exists only through the
  slurry (section 9).
- **Seams**: a piece has `min(3, rarity)` places for affixes, as drops have
  always rolled. A place with nothing in it is an **open seam**, shown on the
  card; remaking a piece opens one.
- **Heat** is rolled when a piece drops (the rarity's figure, 80% to 120%,
  whole numbers) and is full on anything made or bought. The starting kit
  has its rarity's figure exactly. Heat never rises except by remaking (5.3)
  and rekindling (5.4). At 0 the piece is **set**: it can be worn, broken
  down, bound *from* (section 8) and tailored (later), never worked again.
- **Which pieces can be worked**: every piece that rolls affixes (plain
  bases), and **every weapon** (the weapon is a skill, and Brannoc is a
  smith). Named non-weapons (the wolf-fang necklace, the Ashen Plate, relics,
  trophies) are somebody's work: Brannoc won't touch them ("That's somebody's
  work. Leave it be."). They can still be broken down. **Why**: their fixed
  powers are their identity; the items plan's Storied lifts are their road
  (Act 2).
- **Weapons**: weapons have no affixes today. Remaking one opens seams for
  the weapon's affixes (*Wolfbane*, *Gravebane*, *Lampsnuffer's*,
  *Watchman's*, *Cruel*), so the smith is how a weapon gets a kind. Its rank
  still rises with rarity, capped at four (`Inventory.GearRankCap`).

### 5.2 Breaking down

Anywhere safe (by day, not in a fight's reach; never in an arena), from the
pack, and at the forge. Yields the old iron above, **plus one ember shard
for a caged coal** (kindled affix) in it. Not for quest things, trophies,
draughts, anything worn, or Storied pieces. It asks once ("Break it down for
4 old iron?") and cannot be undone.

**Why**: Risk of Rain's scrap and Last Epoch's shattering (C9, C10). It is
also a choice against selling: Brannoc pays 40% of value in gold; breaking
gives iron, which gold can only buy in small amounts.

### 5.3 Heat and remaking

Remaking a piece on a better pattern (5.4) raises its rarity and adds the
difference in heat between the two rarities' figures (+4 a step), so a hot
Uncommon stays hot as it climbs, and a cold one stays cold. **Why**: heat is
"how much more it can take"; a better pattern can take more. It also makes a
starting weapon (Common, 6) workable all the way to Epic (18) if the
survivor pays for every step, which is the "beloved item made better" the
research asks for (C12), while a dropped Epic (14 to 22, three affixes
already) stays the better bargain (C8).

---

## 6. What the night yields

### 6.1 What comes out of an arena

At the arena's end (`Arenas.Finish`), beside the experience, gold, gear and
skills it already gives:

**Ember shards, carried out.**

```
shards = floor(max(0, ember - 10) / 12) + (tier - 1) + floor(minutesPast / 2) + (won story fight ? 2 : 0)
```

`ember` is the ember level at the end; `minutesPast` the minutes stayed after
the half-hour win. **Walked out** by the way out: all of them. **Fell**
(before or after the win): half, rounded down. Measured outcomes are in
section 13.

**The people's own**, from what was slain:

| People | Material | Amount |
|---|---|---|
| the Pack | wolf pelts (wolves), boar hides (boars) | 1 per champion of the kind, + 1 per 150 of the kind slain |
| the Risen | barrow dust | 1 per champion, + 1 per 150 slain |
| the Lamplings | ember shards | 1 per champion, + 1 per 200 slain |
| the Kerchiefs | red cloth | 1 per champion, + 1 per 150 slain |

Each kind capped at 8 a night. Fell: half, rounded down, like the shards.

**Why at the end and not as pickups**: hundreds of creatures dropping pelts
is confetti and a chore of vacuuming (VISION principle 1); a tally on the
arena's end is the Halls of Torment well's moment without the walk (C21).
Champions already drop gear as pickups; that stays.

### 6.2 The run's last decision

Past the half hour the arena goes on, harder by the minute, until the
survivor leaves by the way out or falls (fallen after the win, it is still
won). With shards rising one every two minutes past the win, and half of
everything spilled on a fall, **staying is a wager**: another two minutes for
another shard, against losing half of what is already in the fist. This is
the survivors-like's own crafting decision (Halls of Torment's well, Dead
Cells' Collector), and it uses a part of the arena that already exists.

### 6.3 What is made or improvised mid-run

**Nothing, on purpose.** The night's making is the ember draft (skills,
ranks, evolutions, unions): it is already a choice of three every level, and
it belongs to the combat lead. A crafting menu inside a thirty-minute horde
would break the genre's rhythm (research 2.7: the survivors-likes do no item
crafting mid-run) and the rule that the night stays the night's. What the
run decides is what comes home (6.2). By day, the walk's gathering and the
beasts' drops stay as they are.

---

## 7. The Waystation's hands

### 7.1 Brannoc's forge (phase 1)

The heart of crafting. Opened from his conversation ("Will you work my gear?" in
place of "Can you improve my weapon?") and at the anvil in the smithy
(an interactable that opens it directly once he has worked for you once).
By night: "Forge is banked." Nothing is worked after dark (the story's own
line; the forge is the day's).

Every verb shows, before the press: what it takes (each material with
have and need, the gold), the heat range it will cost, and **what the piece
will be after** (the affix line before and after, the grade's number).

| Verb | What it does | Takes | Heat |
|---|---|---|---|
| **Temper** | one affix up one grade, to the piece's cap (5.1) | to II: 2 old iron, 10 gold · to III: 4 iron, 25 gold · to IV: 7 iron, 50 gold | to II: 2–4 · III: 3–5 · IV: 4–6 |
| **Work in** | a material becomes its answer (table below) in an open seam, or in place of an affix the survivor chooses (that affix is lost); it enters at grade I (II on an Epic, III on a Legendary) | the material (table) + 15 gold + 10 a rarity step | 4–6 |
| **Cage a coal** | a kindled affix: **three are offered** from those that fit the piece, leaning toward the stand-ins the survivor's skills evolve with; the one taken goes in the seam its old coal held, or an open seam, or in place of a chosen affix. Rare and up. | 4 ember shards + 30 gold; another three: 1 ember shard | 5–7 |
| **Remake** | the piece made again on a better pattern: rarity +1, a seam opens, +4 heat; a weapon's rank +1 (to four). To Epic at most in Act 1. One remake a piece a day: "Iron wants a night to cool." | to Uncommon: 4 old iron, 30 gold · Rare: 8, 75 · Epic: 18, 200 | none |
| **Rekindle** | heat + half the piece's starting heat (rounded up) | 3 ember shards and 20 gold the first time; each time after, the shards double and the gold rises by 20 (3, 6, 12, 24...) | – |
| **Break down** | section 5.2 | – | – |

**What each material is worked into** (where more than one fits the piece,
the survivor chooses):

| Material | Takes | Into (the slots it fits) |
|---|---|---|
| Wolf pelt | 3 | *of the Wolf* (cloak, body, head, amulet) · *Wolfbane* (weapon, ring, amulet, off-hand) |
| Boar hide | 3 | *Sturdy* (head, body, cloak, off-hand) · *of the Hearth* (cloak, body, head, amulet) · *Surefooted* (cloak, body, ring) |
| Red cloth | 4 | *Watchman's* (weapon, ring, amulet, off-hand) |
| Barrow dust | 3 | *of the Grave* (cloak, body, amulet) · *Gravebane* (weapon, ring, amulet, off-hand) |
| Ember shard | 2 | *of the Salamander* (cloak, body, head, ring) · *Lampsnuffer's* (weapon, ring, amulet, off-hand) · *of the Lantern* (head, amulet, relic) |
| Bitterroot (Wenna) | 3 | *of the Physician* (body, amulet, ring) |
| Moonpetal (Wenna) | 1 | *of Mending* (body, amulet, ring) |

A pelt worked into a piece **marks it**: the piece carries the `wolf_pelts`
tag the wolfhide cloak carries, and the Verge's wolves smell it ("They smell
the cloak before they see you"). Working the Pack's skins into your gear is
a thing the world reacts to (C19). No other material marks.

**Why these verbs and no others.**
- Temper is Last Epoch's forge in a smith's word, with the target chosen and
  the cost shown (C3, C4). Its caps are what the best drop of the rarity
  rolls, so a crafted piece equals a lucky drop and never beats it (C8).
- Work in is Path of Exile's essence and Valheim's biome armour together:
  a certain affix of a known kind, from the place that needs it (C13). It
  enters low, so the certainty costs tempers to grow.
- Cage a coal is the draft's own shape (three, take one) brought to the
  forge, and the only place crafting meets the night (section 12). Three
  offered, not one chosen from all, keeps the luck in what you are shown and
  makes a redraw a real spend (C4, C22).
- Remake replaces today's reforge (which raised a weapon's rarity for gold
  alone) with the same promise ("a grade truer, by day and by night") and a
  real cost in iron; it is how a weapon gets its kind.
- Rekindle is the only way back, and its doubling cost is Minecraft's anvil
  turned kind: it never says "Too Expensive", it gets dearer (C26).
- Not built, and why: **hone** (rerolling a value within its grade; our
  grades have one value each, which is clearer), **reforge to a random
  affix** (Work in and the coal cover the targeted cases; random reforging is
  what the drops are for), **add an affix past the seams** (only the slurry
  breaks the limit).

**Brannoc's terms** (C18). His respect (the story already tracks it) sets
them:
- respect 20 or more: every heat range's top falls by one ("He takes his
  time over it.");
- respect 40 or more: tempering costs one old iron less.
- Each craft he does for you raises his respect by 1, to +15 from crafting
  in all ("He likes work.").
- His prices follow the shop's (`Journey.PriceMod`): a smith who distrusts
  you charges more.

### 7.2 Wenna's still-room (phase 2)

| Verb | What | Takes |
|---|---|---|
| **Brew** a health draught | one draught | 2 bitterroot + 4 gold (Harlan sells one for 15) |
| **Brew** an antidote | one antidote | 1 bitterroot + 3 gold |
| **Brew** a moonpetal draught (new) | heals 60% (the health draught heals 40%) | 1 moonpetal + 10 gold |
| **Work in** *of the Physician*, *of Mending* | as at the forge | bitterroot 3 / moonpetal 1 + gold; heat 4–6 |
| **Her flask** (phase 2b) | once bought (120 gold), the survivor's draughts refill at the inn while they sleep, one bitterroot a draught, up to three | – |

She brews from the start; she **won't work gear while the stream is still
green** ("I've half the Verge coughing, child. Bring me a clean stream and
I'll stitch your coat."), so her tinctures open with `StreamClean()`. Her
standing sets the grade a tincture enters at (II at trust or affection 30).
**Why**: The Witcher's refill (C25) ends the draught chore; the stream gate
is the story's own and gives the cure one more reward.

### 7.3 Vonnra's binding (phase 3)

**Bind**: one affix lifted out of a donor piece and set in the chosen piece,
at the donor's grade (to the piece's cap), in an open seam or in place of a
chosen affix. **The donor is unmade.** Takes 1 ember shard and 40 gold a
grade; costs the receiving piece 5–7 heat. A set piece (no heat) can be a
donor and never a receiver.

She does it at the toll-house table, in full sentences, holding the donor
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

**Why**: Last Epoch's legendary potential and Kanai's Cube (C11): two finds
become one keeper, every drop is a possible ingredient, and the offensive
affixes (fire, crit, haste, reach), which the forge never makes, can still be
moved onto the piece you love. It is also exactly what the binders do: keep a
power from leaving by holding it in a new vessel. Act 3 says what she meant
to do with the survivor; Act 1's player has already watched her do it to a
ring.

### 7.4 Snib's slurry (phase 3)

Section 9.

### 7.5 Commissions (phase 2)

"Make me one": the survivor chooses a base Brannoc knows (leather cap, iron
helm, padded jerkin, chain shirt, the old watch shield, and the weapons of
their calling) and a material; next morning (C20) it is ready, Uncommon,
the material's affix at grade I, full heat. Takes the material, 2 old iron
and the base's value in gold. His known bases grow with his respect (the
Ashen Plate's pattern at 40). The wolfhide cloak (5 pelts, 30 gold) is his
first commission and stays in his conversation as it is.

---

## 8. Discovery: how a craft is learned

- **By touch** (C15). A verb or material shows at the forge once the survivor
  has carried what it needs: Work in shows each material's line the first
  time one is in the pouch; Cage a coal shows once an ember shard has been.
  The first time each is offered, Brannoc says one line about it (11.2).
- **By people** (C16). Each crafter's work opens with them (meeting Brannoc;
  Wenna's stream; Vonnra's toll; Snib's pump) and their standing deepens it
  (7.1).
- **By the story** (10).
- **Nothing on a wiki**: every craft says what it takes, what it costs and
  what it will make before the press.

---

## 9. The one gamble: steeping in slurry (phase 3)

The Dig cooks ember into slurry; slurry is in the stream, sickening the
wolves. While the pump runs (`dig.pump` is running) and Snib has been met,
he sells **slurry jars** (30 gold, three a day). Steeping a piece:

| Result | Chance |
|---|---|
| one affix up a grade past its cap (to the **bright** grade V if it was IV) | 25% |
| a slurry affix in a fourth place, past the seams: strong, with a price ("+20% damage; you mend 15% less") | 25% |
| nothing changes but the veins | 30% |
| one affix down a grade | 20% |

A steeped piece is **slurried** (green-black veins, a sick glow at night), set
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

---

## 10. Story: crafts the story opens, and crafters it can take

### 10.1 Act 1's gates (each needs the story lead's words)

| Craft | Opens when | Why it is the story's |
|---|---|---|
| Brannoc's forge | met | the town's smith |
| Cage a coal | an ember shard carried to him | the man who forged cages for the ford's ember |
| Wenna's tinctures | `StreamClean()` | she is nursing the Verge until then |
| Vonnra's binding | met at the toll | the binders keep what would leave |
| Snib's jars | the Dig met, the pump running | the gamble is the stream's poison |
| **The fang set** | Greymuzzle killed (`greymuzzle_fang` held) | Brannoc sets the old alpha's fang into a weapon or amulet: a unique prefix, *Greymuzzle's* (+30% damage to wolves and beasts, and the Pack knows it by sight); Maeca's regard falls when she sees it |
| **Shed fur** | the Pack allied (`pack.allied`) | Maeca braids a charm from fur the Pack sheds: the only wolf-craft that kills no wolf (a Rare amulet, *of the Pack's Leave*: wolves give way). The pelts' route and the fur's route are the Beast Problem's two answers in the hand. |

### 10.2 Losing a crafter (later acts; the design now so Act 1 builds for it)

When the story takes someone, their work moves to worse hands; it never
vanishes (the items plan's rule, kept):
- **Brannoc**, if lied to about Nell (Act 2, `nell.told` = lie): "never works
  for the survivor again". Snib's bodgery at the Dig takes every forge verb,
  each heat range one higher, and its lines are Snib's.
- **Wenna**, if she dies in the breakthrough (Act 2): Rook brews the draughts
  in her kitchen (a fixed point that survives everything); the tinctures are
  lost with her.
- **Vonnra**, at the bottom of the stair (Act 3): the binding passes to the
  survivor, at her table, with her book.
- **Snib**: never (the bible's fixed point).

The code keeps each verb's **crafter** as data, so moving a verb is a data
change.

### 10.3 Crafters' voices (from `VOICES.md`; the story lead writes the lines)

- **Brannoc**: fragments, the hammer under everything; iron talked about like
  weather; no thanks. Tempering: no words, a count of blows. Caging a coal: the
  one place he says more than he means to (11.4).
- **Wenna**: brisk lists, "child", interrupting herself when interested.
- **Vonnra**: no contractions, long pauses, payment and arrangement; "traveller"
  until the fortune.
- **Snib**: third person, capitals, contradicting himself.

### 10.4 The seeds (ember is the dead; never said in Act 1)

Proposals for the story lead, each a plain image, never an answer:
- A caged coal "takes a long time to go dark. When it does, it is the shape of
  a thumbprint." (narration, the first cage).
- Brannoc, the first cage: something about cages and what ember wants, near
  the lamp-irons on his rack, never saying the irons' story twice.
- The history line on a caged piece names the night it came from ("A coal from
  the Weeping Fen, day 4").
- Act 3 (design note): every piece with caged coals gains a line per coal, a
  name, when the survivor understands what ember is.

---

## 11. Crafters as people: what the code needs

- Each verb belongs to a **crafter** (`brannoc`, `wenna`, `vonnra`, `snib`) in
  data, with the condition it opens on (`Cond`, the story's own condition
  language) and the place it is done.
- Each craft writes a short **history line** on the piece for the memorable
  ones (remade, a coal caged, bound, steeped), not for every temper.
- Each craft can carry **world effects** (respect, a history event) through
  the story's own `Change` list, so the story lead can attach consequences in
  data without code.

---

## 12. Evolutions and skill synergies (the combat lead's; agreed hooks)

### 12.1 The hooks

| Hook | Rule | File |
|---|---|---|
| Cage a coal | offers three kindled affixes that fit the piece; stand-ins for a passive that the survivor's carried skills **or gear weapons** evolve with weigh ×2 (the drops' own rule, `Inventory.Make`) | `Rpg/Crafting.cs` |
| One coal a piece, two a survivor | unchanged (`Inventory.MaxKindled`): caging replaces the piece's coal, and the forge warns when a third would do nothing | – |
| Remake | a weapon's rank rises with rarity, capped at four (`GearRankCap`), as the reforge did | `Character.Kit` (unchanged) |
| The night's yield | shards and the people's materials at `Arenas.Finish`; nothing changes inside the fight | `Arena/Arena.cs` |
| Draughts (phase 2) | brewing makes them cheaper, not stronger; the moonpetal draught (60%) needs the combat lead's yes | – |

**Never**: crafting grants no evolution, blessing, union, rank past four or
passive; it never changes a card's odds except through the existing kindled
rules; nothing is crafted inside an arena.

### 12.2 The duplicate-id bug (fixed in phase 1, told to combat)

`Items.Affixes` holds `of_mending` and `of_embers` twice (a plain affix and a
kindled stand-in of the same id). `Items.Affix(id)` finds the first, so a
stand-in for Bitterroot or Emberblood, once rolled, reads back as the plain
affix and never stands in. The stand-ins become `of_the_root` ("of the Root",
for Bitterroot) and `of_the_brand` ("of the Brand", for Emberblood); a save
that rolled one already holds the plain affix and is unchanged. A test holds
every affix id unique.

---

## 13. The economy

### 13.1 What the night and the day pay (measured)

`CraftingProbe`, 48 arenas (four callings × tiers 1–3 × four peoples), deft
hands, greedy drafts, 35 minutes (five past the half hour), before the combat
lead's fixes below:

| Tier | Won | Ember at the end (median) | Slain | Champions | Gold: Kerchiefs / others |
|---|---|---|---|---|---|
| 1 | 100% | 57 | 20k–47k | 690–1600 | 52k–63k / 0–40 |
| 2 | 94% | 62 | 17k–61k | 450–2100 | 64k–69k / 0–43 |
| 3 | 100% | 67 | 21k–62k | 800–2200 | 80k–109k / 0–32 |

Two problems, both the combat lead's and both being fixed there: Kerchief
fodder paid tens of thousands of gold a night (fodder gold drops to 2%), and
champions dropped about 300 pieces of gear a night (gear will drop only from
the minute's champion events, heralds, minibosses and the boss). Crafting was
designed not to lean on gold: old iron, ember shards, materials and heat
gate it. The night's yield (6.1) uses champions: about 1 per 150 is 5 to 8 of
the people's material a won night, and the shard formula gives 5 to 11.

### 13.2 Faucets and sinks

| | Faucets (in) | Sinks (out) |
|---|---|---|
| **Gold** | Kerchief fodder, champions and bosses in arenas; quests; selling | crafting fees; old iron from Brannoc; rest; draughts; the story's prices |
| **Old iron** | breaking down; Brannoc's 10 a restock | tempering; remaking; commissions |
| **The world's own** | the Verge by day; the night's people | working in; commissions; brewing; Holloway's bounty and Brannoc's pelt price (they compete) |
| **Ember shards** | every arena's end; lamplings; the prologue; breaking down a caged piece | caging; redraws; rekindling (doubling); working in |
| **Heat** | drop; remake (+4); rekindle | every craft |

What stops inflation: heat (a piece can only take so much), the forge's
ceiling (a piece maxes at what a lucky drop of its rarity would be, and its
seams are its rarity's), rekindling's doubling, and the competing uses of
each material (a pelt sold, a pelt to the bounty, a pelt worked in).

### 13.3 Targets

| Measure | Target |
|---|---|
| First craft | day 1 or 2, by the second visit to the smithy |
| Crafts a day (Act 1, a player who crafts) | 2 to 5 |
| A starting weapon remade to Rare | by day 3 to 4; to Epic by day 6 to 8 |
| Pieces fully worked (every seam at its cap) by Act 1's end | 0 to 2: the forge never finishes the survivor's gear in an act |
| Gold spent on crafting | 30% to 60% of gold earned in Act 1 |
| A night's shards | enough for one cage or one rekindle (4 to 8) when won and walked out |
| Staying five minutes past the win | +2 to 3 shards; falling there loses more than staying gains |

### 13.4 The simulation

`CraftingEconomy` (a test) plays Act 1's economy forward day by day with the
measured faucets and a spender that crafts on what it wears, and checks the
targets above; `CraftingProbe` (opt-in) re-measures the faucets from real
arenas. Results in section 19.

---

## 14. UI needs (a brief for the UI design lead)

The UI design lead owns screens; phase 1 builds the forge in the house's
frame language from this brief so it can be played and seen, and the lead
restyles or rebuilds it.

1. **The forge** (`ForgeScreen`, a full page like the shop's counter). Left:
   Brannoc as a person (portrait, how he feels about you, his terms, a line).
   Middle: **the anvil**: the chosen piece large; its seams as rows (affix,
   grade as I to IV with its cap, open seams shown as open); its **heat** as a
   bar with the number; under it **the verbs** as cards, only those that
   apply, each with what it takes (have and need, red when short), the heat
   range, and **before and after** in words. Right: what can be worked (worn
   first, then the pack) and the pouch.
2. **Cage a coal**: three crested cards like the draft's, each saying what
   the coal does in the ember ("Kindled: counts as the Ford's Cold in the
   ember's evolutions") and which of your skills it serves.
3. **The pack**: the Materials filter shows the pouch; the item card shows
   heat ("Heat 9 of 14", or "Set") and each affix's grade; open seams; Break
   down beside Leave behind.
4. **The arena's end**: a "Carried out" line (ember shards, the people's
   materials, and on a fall, what was spilled).
5. **The shop**: the pouch beside the pack, so materials sell.

---

## 15. What is in Act 1, and what waits

| | Act 1 | Act 2 | Act 3 |
|---|---|---|---|
| Brannoc | temper, work in, cage, remake to Epic, rekindle, break down; commissions | his fate (lie: Snib's bodgery); the last two irons; remake to Legendary at respect 40 | the heart's cage (story) |
| Wenna | brewing; tinctures after the cure; the flask | the breakthrough (she may die: Rook brews) | – |
| Vonnra | binding | marks and the binders' book (items plan) | the book passes to the survivor |
| Snib | slurry jars while the pump runs | the bodgery | – |
| New hands | – | the Vigil's armourers at Silverstair (Wrought bases); Rav the tailor (looks, items plan) | Heartwrought (the Morrow's own, pale and ember-veined) |
| Materials | ten | the north road's few (Vigil silver, north-wood) | the Morrow's |
| Ceilings | grade IV, Epic by craft | Legendary by craft | Heartwrought |

---

## 16. Build phases

Each phase is playable end to end and seen in the running game before the
next.

**Phase 1: the forge's core loop.**
- Data: `crafting.json` (verbs, materials, costs, crafters, conditions);
  `old_iron` in `items.json`; Brannoc's shop line for old iron; his
  conversation's "Work my gear." (story lead's words) opening the forge.
- Logic: `Rpg/Crafting.cs` (heat, seams, every Brannoc verb, the three
  coals, break down), the pouch in `Inventory`, heat on drop in
  `Inventory.Make`, the night's yield in `Arenas.Finish`, the pelt mark in
  `WorldTags`, the duplicate-id fix, save version 3 (heat for old pieces, the
  pouch).
- Interface: `ForgeScreen`; the pack's pouch and the card's heat and grades;
  break down in the pack; the arena's end's carried-out line.
- Tests: every verb's rules and costs; the save migration; the pouch with
  the story's `hasItem`, `take` and `give`; the night's yield; the economy
  simulation's targets.

**Phase 2: the still-room and commissions.** Wenna's brewing, tinctures and
flask; commissions; the fang set and shed fur with the story's words.

**Phase 3: the binder and the slurry.** Vonnra's binding; Snib's jars and
steeping; the seeds' lines.

---

## 17. Decisions, and why

1. **Heat over unlimited crafting.** The only answer the research found to
   "craft the best and done" that does not take away the player's choice
   (Last Epoch); a visible budget is fair where Diablo IV's was cruel because
   no single craft can lose its value to luck alone.
2. **Fixed grades, no ranges within them.** Today's affixes have one value a
   grade; adding ranges would add a "hone" verb and a number to read on every
   line for little decision. Kept the game's own model.
3. **The forge's ceiling equals a lucky drop of the piece's rarity.** C8:
   the chase stays in the world; the forge turns a good find into the best
   version of itself.
4. **Work in enters low; offensive affixes are never made, only moved.**
   Answers (resistances, slayers, armour) are what crafting should guarantee
   (C13); raw power stays in drops and binding.
5. **Three coals, not a chosen coal.** The forge's one meeting with the night
   uses the night's shape; choosing any stand-in outright would let a
   survivor plan every evolution by day, which the skills design keeps the
   night's.
6. **Remake adds heat.** Otherwise the starting weapon could never become
   good, and the beloved piece (C12) would be impossible.
7. **Materials yielded at an arena's end, not dropped.** No confetti, no
   vacuuming; the tally is the reward's moment.
8. **No mid-run crafting.** The draft already is the night's making.
9. **The pouch.** No materials in the pack.
10. **Crafting is a page of its own, opened from the person.** Every craft is
    a conversation first; the page is the counter you work at.
11. **Ember shards are the fire, not a new currency.** One object carries the
    night into the day and carries the reveal.
12. **The items plan's six-grade item levels, Marks, sets, notches,
    sigils, tailor and steeping-by-default are not in Act 1.** They are the
    items plan's, unbuilt, and a crafting design that waited for them would
    make nothing playable; this design's data leaves room for each.

13. **The weapon's upgrade is Remake, and it costs old iron as well as
    gold.** The owner approved it (October 2026): stronger choices, slightly
    slower early weapon ranks.
14. **Falling after the half-hour win spills half the night's materials.**
    The owner approved it: it gives the endless minutes a stake.
15. **The anvil works one seam at a time** (seen in the running game, 19.1):
    every craft for every seam at once was a wall of refusals. A seam is
    chosen and only its crafts are offered (Last Epoch's forge).
16. **One remake a piece a day** (19.2): a Kerchief night's purse remade the starting weapon from Uncommon to Epic in one visit; remade iron cooling overnight spreads the climb over days, as the targets ask, and is the smith's own reason.
17. **Break down yields halved; a shard per 12 ember, not 8** (19.2): measured, iron and shards piled up unspent (190 iron and 100 shards by Act 1's end).
18. **Arena gold cut, by combat** (19.2): champions 7% of the day's rate, fodder 0.15%, bosses and minibosses in full. A Kerchief night pays about 350 gold (it paid 2.5k–3.3k), still three to thirty times another people's night.
19. **Wenna brews from the start; only her tinctures wait for the cure** (a verb's gate, `crafters.wenna.gates`): brewing is the herbalist's trade and nursing the Verge is what she is doing; stitching your coat is what she has no time for.
20. **The still-room is a side panel, not a page** (the owner: full pages are often not the best choice): brewing is an errand on the way out of town; her bench, which works gear, is the forge's page in her place.
21. **The draught key drinks the moonpetal only for a deep wound** (55% of health gone; combat's rule): a rare draught spent on a scratch would feel like a theft.
22. **A trophy is set outside the seams** (`ItemInstance.Setting`): Greymuzzle's fang leads the piece's name, spends no heat and takes no seam, so the one fang in the game never competes with the forge's work.
23. **Crafts never dress the figure again**: a craft changes what a piece does, never how it looks; rebuilding the figure made her blink out of the world (seen, 19.3).
24. **Binding moves plain powers only**: coals stay in Brannoc's cage, and worn skills, trophies and the slurry's powers will not let go. Each of those is somebody's work or the night's; moving them would make binding the answer to everything.
25. **The donor must be in the pack**: what is worn is in use; taking it off first is a beat of choice, not a chore.
26. **Steeping by hand from the pack as well as at Snib's**: jars bought before the cure still work after it. The cure closes the sale, not the gamble already bought.
27. **The slurry's "affix" outcome adds a fourth power past the seams**, the only thing that ever breaks the seam count (5.1).
28. **Vonnra opens only once the toll is paid** (the story lead's condition): her table is the toll-house's, and she deals with those who have paid.
29. **A steeped piece takes no heat back** (19.4): rekindling or remaking it would let the forge work past the bright grade.
30. **"Up" goes past the cap however low the power was** (19.4): it lands one grade above the piece's cap. The first build only added a grade, so on an unfinished piece it was a dud that cost all its heat. The jar's words ("a grade past what the forge can do") are now true every time, and "temper first, then steep" is still the better order.

---

## 18. What this design takes from the items plan, and what it changes

Taken: heat (and rekindling with ember shards), the crafters and their
services' spirit, "show cost, chance and range; never destroy", the one
labelled gamble, the binder's book idea (as binding), losing a crafter
moves the work, the pouch, salvage to materials.
Changed: scrap and ashsteel become one **old iron**; tempering's grades are
the game's four; reforge and hone are cut; tinctures are Wenna's half of
**Work in**, shared with Brannoc's materials; Marks, sigils, notches and
the tailor wait for Act 2; rekindling doubles instead of once per item;
steeping's odds are re-weighted with a worse-case and no Named reroll.

---

## 19. Results

### 19.1 Phase 1, seen in the running game (1920×1080, October 2026)

What looked wrong, and what was done about it:

| Seen | Done |
|---|---|
| The anvil listed every craft for every seam: on an Epic helm, nine rows, most with a red refusal ("No open seam", "as high as a epic piece goes") and a "Work over this" button under each seam | Rebuilt: the seams are rows with a grade badge (numeral in the rarity colour of that rank, pips to the cap; a flame for a coal; a dashed gap for an open seam). One is chosen; only its crafts show; work-ins two to a row; what does not apply is said once, quietly |
| Each seam's line was written twice (as the title and again as "before") | Said once, on the seam row; a craft shows only what it makes |
| A flat orange bar for heat; the cost of a craft was a number in a cost line | A gauge of ember cells; under the pointer or the pad's focus it shows what a craft will surely spend, may spend, or adds |
| Rekindle on a full piece read "Heat 6 to 6 of 6" with a refusal; Break down on a worn piece, a red "Take it off first." | Remake, Rekindle and Break down are three tiles at the foot; quiet when they do not apply, saying why |
| Brannoc's terms were a line once earned and nothing before | A ladder: each term, what it does, the respect it asks, met or locked |
| Empty worn slots were blank frames | Slot glyphs and names, as in the pack |
| "3 wolf pelt", "Needs 3 wolf pelt" | Materials have plurals (`Items.Several`) |
| Old iron's icon read as a bent wire | Remade: a rusted horseshoe, a blade snapped below the guard, square nails (one bent), a ring, in a rust texture |
| The arena's end said "Carried out: 6 ember shard, 4 wolf pelt" in a line | The things themselves as slots, the spilled ones greyed beside them |
| A banked forge offered presses that then failed | A banked forge quotes (so the night can plan) and refuses, said once at the top |

The forge after a craft, the pack's break down by mouse and a real arena's end
after a fall were seen later (19.3).

### 19.2 The economy (`tests/CraftingEconomy.cs`)

Act 1 as ten days, a won night each (tiers 1, 2, 3 by thirds; the four
peoples in turn; a story night in three), eight seeds. Faucets: combat's
sweep at `71608a4` (deft bot; fodder gold 2%, gear from carriers only): ember
57/62/67, champions 864/1052/1079, Kerchief nights 2,570–3,320 gold, the
others 11–22; about 13 pieces of gear a night by the arena's own drop rule;
by day a few of the Verge's beasts, 80 gold of quests and 50 of the story's
prices. The spender wears what is finer, breaks down the rest, and crafts
on what it wears: remake the weapon, temper the lowest grade, fill open
seams, cage up to two coals, rekindle a cold piece.

| Measure | Target | Before tuning | After (the old arena gold) | After (arena gold cut, measured) |
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
an arena's real rates and fails if they move without a re-probe.

**Findings.**
- **Gold is the one faucet crafting cannot hold.** A Kerchief night pays
  2,500–3,300 gold (its champions keep the day's gold rate), the rest of a
  ten-day act pays about 1,500, and crafting's prices were set against the
  second. With champions at a tenth in arenas (combat's one line, at
  `Rules.FodderGold`'s use in `Battle.KillEnemy`), the Kerchiefs stay the
  gold night (about 300, three times an ordinary one) and every target holds.
  **Asked of combat.** The test holds the targets on that economy.
- **Iron and shards were too generous** for their sinks: decision 17.
- **A remake a day** (decision 16).
- **Shards still gather** (77 by Act 1's end). Phase 3's binding (a shard a
  grade), redraws and the endgame's charts draw on them; re-measure then.

### 19.3 Phase 2, built and seen (October 2026)

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

---

## 20. The endgame: the atlas and the scars

The owner: "end game is two types of arenas - permanent and our normal
arenas. permanent is our arpg build maps like poe and the normal arenas are
for mindless survivors fun." And story is about 40% of the game early on.
The story bible names them: **the Wayfinder's atlas** (charts kept by Ysolde,
"the places the road forgets") and **the scars** (a night's scar opens, burns
until you leave or fall, and closes). Combat's mechanics for maps are
`SKILLS_DESIGN.md` §17; the experience lead owns their shape and loop
(`EXPERIENCE_AUDIT.md`). This section is what crafting does for each.

### 20.1 Each arena pays what the other needs

| | Pays | Wants from crafting |
|---|---|---|
| **The scars** (survivors runs) | **fire**: ember shards (more the deeper you stay), the people's materials, kindling | coals caged in gear, to shape the draft; nothing else (the scar is "mindless fun": what you bring in is decided at the forge, not in the run) |
| **The atlas** (build maps) | **iron and bases**: gear at the map's item level (broken down: old iron), gold, the people's materials, charts | the build itself: seams, grades, bound affixes, marks; and charts worked for what they pay |

So a player who only maps runs short of fire (rekindling, caging, burning
charts); one who only runs scars runs short of iron and good bases. Neither
loop is optional for a build, and neither is a chore: each is the other's
supply line (the experience lead's "nights pay materials and kindling that
craft and roll maps; maps pay gear whose kindled affixes feed the nights").

**Why**: Last Epoch's monolith and dungeons, and Path of Exile's league
mechanics, split their currencies by activity so that every activity has a
reason to be run; ours splits them by the two arenas, and the split is the
world's (fire is the night's, iron is the day's).

### 20.2 Two kits

A survivor keeps **two kits** of worn gear: one for the scars, one for the
atlas, chosen at the table. **Why**: a caged coal does nothing in a map (the
draft is the night's), and a map's answers (crit for iron, frost resistance
for winter) are wasted in a scar, where the ember carries the build. Without
two kits every coal is a seam lost to the build, and the player either never
cages or never maps. With them, crafting has two jobs and gear has two lives:
the night kit is coals and the people's answers; the map kit is the build.
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

### 20.3 Build depth for the atlas

Act 1's forge stops at grade IV and Epic (section 15). The atlas is where
the ceilings rise, each by a hand the story gives:

| Layer | What it is | Who | From |
|---|---|---|---|
| **Item level** | a piece's grades can reach what its item level allows: grade V from item level 25, VI from 35 (map tier sets the level: `8 + 2 × tier`) | drops | the atlas |
| **The forge's cap follows the hands** | grade V at the Vigil's armourers (Act 2), VI on Heartwrought (Act 3); the forge never passes what the piece's item level allows; the bright grade stays one above the forge, and only the slurry (or its endgame heir, 20.5) gives it | Brannoc, the Vigil, the Morrow | the story |
| **Remake to Legendary** | at Brannoc's respect 40 (Act 2), costing the people's rare material from a map boss | Brannoc | atlas bosses |
| **Binding** | the build's engine: the offensive affixes (fire, crit, haste, reach), which the forge never makes, are moved from donor drops onto the piece kept; donors are the atlas's flood of gear | Vonnra (or her book) | map drops |
| **Marks** (proposal, combat's yes needed) | a fourth kind of seam content that changes how one day skill behaves in maps: Oathblade's arc wider and it bleeds; a bolt that forks; a chain that returns. Dropped by map bosses, one people's kind each; inscribed in an open seam; one per piece, three per kit; Vonnra: "Marked. It will do it that way now, until it breaks." | Vonnra, from the binders' book (the items plan's Marks) | map bosses |
| **Heat** | unchanged: the budget that stops "craft the best and done"; higher grades cost more heat (V: 6–8, VI: 7–9), so a map piece is a set of choices, not a checklist | – | – |

**Why marks** (and not "sigils", which the canon keeps for the Legion's seven-notch sigils that hold the chain): Path of Exile's build depth is in what changes a skill
(supports, unique interactions), not in bigger numbers. Our day skills have
ranks and arts but nothing that bends them. A mark is a small, readable
change, one per piece, so a kit of three is a build's signature. It is the
binders' own craft (they hold one thing's power in another) and gives Vonnra's
book its endgame.

### 20.4 Working charts (the Wayfinder's table)

A chart (combat's map item, §17.2) is worked at the table by **Ysolde**, the
Wayfinder, in her voice, with the same quote-then-do rules and the same
budget: **a chart has heat** (plain 4, fine 6, rare 8), each verb spends
some, at none it is fixed.

| Verb | What it does | Takes | Heat |
|---|---|---|---|
| **Ink** | a mod added, at random, on the side chosen (the foe's or the survivor's) | 1 ember shard + gold by tier | 2–3 |
| **Burn and redraw** | every unpinned mod rerolled | 2 ember shards | 2–3 |
| **Pin** | one mod held through redraws (one pin a chart) | 2 of the chart's people's material (wolf pelt on a Pack chart) | 1 |
| **Scrape** | one chosen mod removed | 3 old iron (a blade's edge) | 1–2 |
| **Annotate** | +5% quality, to 20% | gold, and a chart of the same people given up | – |

**Why**: Path of Exile's map crafting is the loop's heart (read the mods,
roll, choose what to run). Ours keeps its choices and drops its slot machine:
each verb is chosen and costed, the budget is shown, and the materials are the
two arenas' own (shards from the scars, the people's material and iron from
the atlas). Pinning with the people's material ties a chart to its people: to
pin a mod on a Pack chart you need what the Pack's nights or maps yield.

### 20.5 The scars' crafting

Light on purpose: the scar is "mindless survivors fun".
- **Shards** rise with depth. The scars are truly endless (the owner), so
  `minutesPast / 2` keeps paying; past 30 minutes beyond the win, a shard a
  minute. A fall spills half (decision 14).
- **Coals** are the scar kit's point. The forge's three-coal offer stays the
  only way to choose them (decision 5).
- **The slurry's heir.** If the stream is cured (the gamble closes, section 9),
  the deep scars give **scar-glass** past an hour: one steeping's worth, the
  same table of chances. The gamble survives the cure, earned by staying, not
  bought.

### 20.6 What to build, in order (after phases 2 and 3)

Reordered (October 2026): the two pieces that are crafting's own came first. Two kits wait for UI design's
pack, which is being redone from research.

1. Marks on the item side (built, 20.7).
2. Chart verbs at the table (built, 20.7).
3. Item level on gear and grade odds by item level (built, 20.7; the loot lead now owns item level and builds on it).
4. The scars' depth and scar-glass (built, 20.7).
5. Two kits (pack and table), with UI design's new pack.
6. Higher grades and remake to Legendary (Act 2's hands).

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
- A save from before shelves keeps its 48 places as two shelves.

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

- Those materials are counted into the night's end tally in arenas, never dropped (decision 7).

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
