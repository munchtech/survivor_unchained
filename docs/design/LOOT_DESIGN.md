# Loot: what falls, how it reads, where it goes

The loot and itemisation lead's design (agent `a9a9c345a35e1fcad`). It answers the owner's brief
of 5 October 2026 and builds on two earlier plans: the items plan (`docs/items/`, a design with
little built) and crafting (`docs/CRAFTING_DESIGN.md`, built). Where this differs from the items
plan, this wins; where it touches the forge, crafting's design wins and section 12 lists what I
ask of it. Every number is data (`data/content/loot.json`) and the balance lab's to move.

The owner, 5 October:
- "a very intuitive inventory management is smart. things that can be tucked away like
  spellbooks or stuff is useful, inventory management is a very real concern in these games so we
  need it, but we also don't want to feel cheated with things that should stack, or should not even
  take up inventory spots directly either."
- "we also need to make an item filter and more poe/diablo style drops that can be seen or hidden
  better with better sounds on quality items"
- "we don't have any legendaries (extremely rare) yet do we? or sets. ... should have some
  legendaries even at low lvls for huge dopamine spike."
- "theres far too many common items that we don't need. common items in higher zones can be
  better than greens or even blues (or way later commons even better than early purples) but in
  general items can drop a little less, their drops replaced maybe with crafting stuff."
- "item drops should *mostly* feel good."

## The decisions in one page

1. **Seven tiers, one language.** Common (grey), Uncommon (green), Rare (blue), Epic (violet),
   **Set** (verdigris, new), **Legendary** (amber, extremely rare), Storied (ember red). The colour
   says the band, the beam's height and the sound say how rare, a mark says the exception
   (an upgrade, a better make).
2. **Item level and make.** Every piece carries the level of what dropped it. The level sets its
   **make** (Worn, Sound, Wrought, Legion, Heartwrought), and the make multiplies its base's own
   numbers: a Heartwrought Common beats a Worn Epic, a Wrought Common a Worn Rare. Past level 25 the
   affixes roll a grade higher, past 35 two.
3. **Fewer drops, better drops, the rest is crafting.** Gear comes only from what visibly carries
   it (champions, minibosses, heralds, bosses, strongboxes, the Verge's elites). About a third fewer
   gear drops than today; each roll is likelier to be good, and Commons thin out as levels rise.
   A carrier that drops no gear drops the people's material or old iron instead.
4. **Legendaries are rare, early and certain once.** About one gear roll in 230. The first story
   boss a survivor beats drops one for certain (Diablo III's first-kill rule); a visible tally,
   "the dark's debt", guarantees one at the 120th roll without one. Four of the first eight can
   drop from level 1 to 3. Every one changes how you play.
5. **The pack is for gear.** The 24 places hold only things you wear. Materials and trophies go in
   the **pouch**, books and charts in the **satchel**, quest things and tools on the **key ring**,
   draughts on the **belt**, gold in the **purse**. None take a place; all stack.
6. **An item filter from the first night.** Four presets (Everything, Default, Strict, Only the
   best), five plain toggles, and a rule list later. Legendary, Set, Storied and quest things can
   never be hidden. Hidden things are not picked up by walking over them, and at a fight's end they
   are broken down for old iron.
7. **Nothing the filter shows is ever lost to a fight.** At a night's or a map's end everything
   shown and still lying is gathered home; Rare and up that will not fit goes to Rook's storeroom.
8. **Presentation by tier, and one moment for a Legendary.** Beams grow with the tier, each tier
   has its own drop sound, and a Legendary hushes the music, tolls, and raises a pillar of amber
   to the sky that the screen's edge points to.

---

## 1. Research: how the best loot games solve each part

The items plan's `docs/items/RESEARCH.md` covers the genre's history and its 28 lessons (cited
here as R1 to R28). This section adds what that research did not cover, part by part, for the
questions the owner asked.

### 1.1 Rarity ladders and the top tier

| Game | Ladder | What the top tier does | Lesson |
|---|---|---|---|
| Diablo II | normal, magic, rare, set, unique; runes beside | Quality is checked in order, **unique, then set, then rare, then magic**, each against its own chance improved by item level and magic find; a monster's treasure class can also roll **NoDrop** ([PureDiablo](https://www.purediablo.com/d2wiki/Treasure_Class)) | The ladder is a sequence of independent checks; "nothing" is a real outcome. |
| Diablo III, Loot 2.0 | magic, rare, legendary, set | Legendaries buffed but made to matter; **a guaranteed legendary for a character's first kill of each act boss below 60**; smart loot rolls for your class 85% of the time ([Diablo wiki](https://diablo.fandom.com/wiki/Loot_2.0)) | Guarantee the first spike; aim most drops at the player in front of you. |
| Diablo IV, Loot Reborn (Season 4) | magic, rare, legendary, unique, mythic | **Fewer items drop**, salvage pays more and crafts cost less; rares 2 affixes, legendaries 3; greater affixes only on top items ([mein-mmo](https://mein-mmo.de/en/diablo-4-season-4-patch-notes-show-what-gets-better-less-loot-but-stronger,1121161/), [Prima](https://primagames.com/gaming/all-big-changes-and-updates-coming-in-diablo-4-season-4-loot-reborn)). Mythic uniques were found "weeks later in the inventory" until they got **their own drop sound, purple beam and label** ([Icy Veins](https://www.icy-veins.com/d4/news/uber-uniques-are-getting-a-facelift-in-diablo-4)); that sound became the fans' favourite in the game ([mein-mmo](https://mein-mmo.de/die-besten-sounds-in-diablo-4-laut-fans/)). | Fewer, better, and the rest becomes crafting. The top tier must be impossible to miss. |
| Grim Dawn | common, magic, rare, epic, legendary | Rares from about level 8, epics 12, legendaries 50; **common and single-affix drops fall as level rises**; monster infrequents drop only from named kinds ([Grim Dawn](https://www.grimdawn.com/guide/items/the-hunt-for-loot)) | Thin the commons with level; give the best things homes. |
| Last Epoch | normal, magic, rare, exalted, unique, set, legendary | Low-powered and levelling uniques drop with **more legendary potential** than the endgame ones ([Upcomer](https://upcomer.com/last-epoch-loot-rarity-colors-explained)) | Early uniques can be exciting without being endgame. |
| Path of Exile | normal, magic, rare, unique | Uniques wearable at level 1 (Goldrim, Wanderlust, Tabula Rasa) carry whole campaigns ([PoE Vault](https://www.poe-vault.com/guides/beginner-guide-to-unique-items-for-leveling-in-path-of-exile)) | A low-level unique that changes the run is the cheapest dopamine there is. |

### 1.2 Item level, bases and why a white can matter

- Diablo II gives every base and unique a quality level; a drop's item level is its monster's, and
  a monster must exceed an item's quality level to drop it ([PureDiablo](https://www.purediablo.com/d2wiki/Treasure_Class)).
  Its normal, exceptional and elite bases are why a grey elite armour is worth carrying (R18).
- Path of Exile and Last Epoch gate affix tiers by item level; Last Epoch keeps low bases useful
  because their implicits and affix pools differ, not only their numbers
  ([Last Epoch forum](https://forum.lastepoch.com/t/confusion-about-gear-progression/24098)).
- Diablo IV scales every number on an item by its item power, so a rare can beat a legendary of
  lower power. That is the owner's "late common beats early purple" in its purest form, and also
  why D4 players stopped reading rarity at all (R8.2). We take the base's scaling (make) and keep
  affixes graded, so rarity still means something.

### 1.3 Inventory, stacking and slotless stores

- Diablo IV moved gems into the materials tab ([PCGamesN](https://www.pcgamesn.com/diablo-4/gems-inventory)),
  aspects into the Codex of Power on salvage, and quests and consumables into their own tabs
  ([mein-mmo](https://mein-mmo.de/en/blizzard-solves-an-annoying-problem-with-season-4-players-say-this-completely-changes-diablo-4,1126382/),
  [PureDiablo](https://diablo4.purediablo.com/Inventory)). Players called the aspect change one
  that "completely changes Diablo 4". Potions are a counter, never a place.
- Path of Exile 2 keeps a fixed 12×5 grid and lets "affinities" route currency and the rest to
  their tabs; its complaint is the opposite of clutter, too many half-empty themed tabs
  ([Steam](https://steamcommunity.com/app/2694490/discussions/0/4628107674950649701)).
- Torchlight Infinite's pet loots by category, basic, intermediate and advanced
  ([Deltia's](https://deltiasgaming.com/?p=296729)).
- The genre's verdict (R8.3, R24): materials never in the grid, auto-pickup for currency, stacks
  without silly caps, town trips optional. The management that stays fun is **choosing which gear
  to keep**, not finding room for herbs.

### 1.4 Item filters

- **Path of Exile.** Rules top to bottom, first match wins; each can set label colours and size,
  a beam, a sound and a minimap icon. NeverSink's filter has **seven strictness levels**, soft for
  the campaign to uber-strict for deep mapping, and its colours, icons and beams are **clustered by
  value** so a glance reads the band ([NeverSink](https://gitee.com/agg/NeverSink-Filter),
  [Maxroll](https://maxroll.gg/poe2/news/filterblade-launch-for-path-of-exile-2)).
- **Last Epoch** ships it in the game: up to 75 rules of show, hide or recolour, with conditions on
  rarity, type, affixes and their tiers, level and class; higher rules override lower; **hidden
  items still drop**, only their labels go; Shift+F opens it ([Maxroll](https://maxroll.gg/last-epoch/resources/loot-filter-guide)).
- **Grim Dawn** has a simple rarity threshold in the corner (most players pick "green and up").
- Lessons: ship it in the game with good defaults; strictness is the one choice most players
  make; rules are for the few; never let a filter hide a jackpot.

### 1.5 Presentation

- Beams and drop sounds by value are the cheapest dopamine in the genre (R8.7, R22). Diablo IV's
  mythic fix (1.1) shows the cost of a top tier that looks like the tier below.
- Vampire Survivors' chest is a slot machine you always win: one, three or five things, and the
  five-thing reveal cannot be skipped ([Gamezebo](https://www.gamezebo.com/walkthroughs/torchlight-infinite-auto-loot/),
  [The Vibes](https://www.thevibes.com/articles/lifestyles/53373/vampire-survivors-an-escalating-dopamine-rush-disguised-as-a-retro-game)).

### 1.6 The survivors half

- **Vampire Survivors**: gear does not drop; chests from elites carry the run's powers, and coins
  carry the meta. Everything the run gives is a choice or a reveal, never a pickup to manage.
- **Halls of Torment**: minibosses offer **three pieces of equipment, take one**; a well in each
  dungeon sends **one** new piece home per run, which unlocks it for good
  ([Prima](https://primagames.com/gaming/how-to-keep-items-permanently-in-halls-of-torment)).
- Lesson: in the horde, loot comes from things that visibly carry it and is decided at the run's
  end, not by vacuuming the floor under fire.

### 1.7 What we take

- L1. Fewer gear drops, each better; the difference becomes crafting materials (D4 S4, D3 2.0).
- L2. A visible top tier with its own beam, sound and label, impossible to miss (D4 mythics).
- L3. Guarantee the first legendary; protect against long droughts visibly (D3, R10).
- L4. Thin commons as level rises; make the commons that remain bases worth reading (GD, D2).
- L5. The base scales with level; affixes stay graded so rarity still means something (D2, PoE).
- L6. Only wearable gear competes for places; everything else is counted (D4, R24).
- L7. A filter in the game, strictness first, rules later, jackpots unhidable (PoE, LE).
- L8. In the horde, gear comes from carriers and is gathered at the end (VS, HoT).
- L9. Effects over numbers for the top tiers (R3), and low-level uniques that carry a run (PoE).
- L10. Give the best things homes so they can be hunted (GD's infrequents, D2's quality levels).

---

## 2. Principles

1. **Most drops feel good.** A drop is either a likely upgrade, a better base, a material you
   want, or a jackpot. Junk is filtered and broken down, not walked to.
2. **Read in a glance, understood in two seconds.** Colour for the band, beam and sound for
   rarity, one mark for the exception, a tooltip with a compare.
3. **The world pays in what it is.** Gear's homes are peoples and places; a filler drop is the
   people's material.
4. **Never cheated.** Things that should stack stack; things that should not take a place do not;
   what you were shown is never lost to the fight.
5. **The night stays the night's.** Gear shapes the ember and never owns it (`SKILLS_DESIGN.md`
   §10, crafting's rule). Legendaries change how you play, but no item grants a rise from death:
   the owner's "unless she carries the skill that grants it".

---

## 3. The tiers

| # | Tier | Colour | What it is | Affixes | How often (a gear roll, level 1 / 16 / 40) |
|---|---|---|---|---|---|
| 0 | **Common** | ash grey `#c8c0b0` | A base, and its make. Worth it when the make is better than what you wear. | 0 | 41% / 17% / 3% |
| 1 | **Uncommon** | green `#6fd46a` | A base with one affix. | 1 | 35% / 42% / 39% |
| 2 | **Rare** | blue `#5aa8ff` | The backbone: two affixes. | 2 | 19% / 32% / 44% |
| 3 | **Epic** | violet `#c070ff` | Three affixes, rolled finer. | 3 | 3.8% / 8.2% / 13% |
| – | **Set** | verdigris `#3fd6c0` | An authored piece of a small set: fixed powers, and bonuses for wearing more of it. Rarity 3 under the hood (heat, seams), its own tier for the eye. | fixed | 0.9% / 1.1% / 1.0% |
| 4 | **Legendary** | amber `#ffb040` | An authored thing with a power that changes how you play, a home, a lore line, often a price. Never rolls affixes; its base scales with its make. | fixed | 0.4% / 0.5% / 0.5% |
| 5 | **Storied** | ember red `#ff6a3a` | A named thing with a history with you (given by the story, or grown: items plan §9). | fixed | never drops |

- The Set tier is the one addition to the colours. Verdigris is old bronze's patina: things made
  to be kept together. It sits 58° of hue from Uncommon's green, but some eyes still join them, so
  colour is never its only cue: a small **chain-link mark** on its tiles and tooltip header (the
  game's chains; UI design's suggestion), a double border and a twin beam.
- A Legendary's tooltip keeps its power and lore to about six lines, so the compare still fits
  beside it at 1080 (UI design's limit).
- Rarity numbers stay 0 to 5 in the code (crafting's heat and seams read them). A set piece is
  rarity 3 with a `set`; the tier is worked out from both (`Drops.TierOf`).
- **Why so few Legendaries.** The owner asked for "extremely rare". At 0.4% to 0.5% a roll and the
  drop counts in section 5, a player sees about three to five in Act 1, one of them certain.
  Diablo III's late flood (R8.2) is what we avoid: a Legendary must still stop the room.

---

## 4. Item level, make and zone scaling

### 4.1 Item level

Every piece carries a **level** (`ItemInstance.Level`), shown on its tooltip ("level 18"):

| Where it came from | Its level |
|---|---|
| A creature (champion, miniboss, herald, boss, elite) | the creature's level |
| A boss's hoard, a chest | the boss's level |
| A map's strongbox | the map's level + 1 |
| A quest, a shop, a commission | the survivor's level |
| The starting kit, and anything from before levels (old saves) | 1 |

Capped at 40 (map tier 16 is level 40). Character level never limits what can be worn.

### 4.2 Make: why a late Common beats an early Epic

The level sets the piece's **make**, and the make multiplies its base's own numbers (its
implicits: a helm's armour and health, a ring's critical chance, a cloak's speed). Downsides are
never multiplied. A weapon's make adds increased damage instead, since a weapon's base is its
skill.

| Make | Levels | Base numbers | Weapon damage | Seen in |
|---|---|---|---|---|
| **Worn** | 1–7 | ×1.0 | – | the prologue, Act 1's first days |
| **Sound** | 8–15 | ×1.8 | +10% | Act 1's later nights, the atlas's first tiers |
| **Wrought** | 16–23 | ×2.8 | +25% | Act 2, tiers 4–7 |
| **Legion** | 24–31 | ×4.0 | +45% | Act 3, tiers 8–11 |
| **Heartwrought** | 32+ | ×5.5 | +70% | the deep atlas, tiers 12–16 |

Armour has its own, gentler curve (×1, 1.8, 2.8, 3.4, 4.0): its reduction saturates
(armour ÷ (armour + 20)), and a full Heartwrought set at ×5.5 came to about 75% (combat). The
lasting answer is combat's: armour measured against the size of the blow (Path of Exile's rule),
so deep armour is worth what deep blows ask. A piece's flat rule damage (Kell's Lamp's flare, the
Drowned Coat's black water) grows with its make as its numbers do, so a deep copy is not a toy;
rules that read the blow or the weapon already grow with what they read.

The make is a word on the tooltip's second line ("Common helm · Wrought · level 18"), not in the
name. **Why discrete makes, not a smooth curve**: two pieces are compared at a glance by a word
(Diablo II's normal, exceptional, elite: R18); a curve would ask the player to read decimals.
(The story lead's yes: "Legion" is the valley's word for the old empire's best iron, from about
Act 2; "Heartwrought" never before Act 2's end, which level 32 keeps.)

Every armour base gets implicits worth about one and a half affixes, so a Common has something to
scale (section 10.3). Measured with the power score (4.4) over 200 rolls of each, the owner's claims
hold for every helm, body and cloak base, and a test holds them (`LootTests`):

| Chain Shirt (power) | Common | Uncommon | Rare | Epic |
|---|---|---|---|---|
| Worn (level 1–3) | 3.7 | 5.8 | 9.9 | 15.7 |
| Sound (10) | 8.3 | | | |
| Wrought (18) | 14.0 | | 20.7 (level 20) | |
| Heartwrought (34) | about 24 | | | about 40 |

- a **Sound Common** beats a **Worn Uncommon** of the same base;
- a **Wrought Common** beats a **Worn Rare**;
- a **Heartwrought Common** beats a **Worn Epic**;
- and a deep Rare or Epic is still far better than a deep Common: rarity keeps its meaning.

Rings and amulets are where affixes live: their small implicits scale too, but a Common ring never
beats a good roll. A late Common ring is a base for the forge, as in Path of Exile.

### 4.3 Grades: affixes rise with depth

Affix grades keep crafting's model (fixed values a grade, I to VI; `CRAFTING_DESIGN.md` §5.1, 17.2).
A drop's grades come from its rarity, as today (Uncommon I–II, Rare II–III, Epic III–IV; the finer
of the two oftener the deeper it was made, crafting's `FinerGrade`), **raised one grade from level 25
and two from level 35**,
to VI at most. Nothing below level 25 changes, so Act 1's forge economy holds as measured. The
forge's own caps are crafting's (the forge never passes what a piece's level allows).

### 4.4 The power score

`Drops.Power(item)` sums an item's numbers by a value per unit (armour 1 a point, health 0.12,
critical chance 0.6 a percent, increased damage 0.35 a percent, and so on, in `loot.json`), minus
its downsides. It is never shown as a number. It drives three things: the filter's **upgrade**
test (better than what is worn in that slot, by a margin), the tile's up-arrow, and the tests
above. Weapons only compare with weapons of the same skill: another skill is another way to play,
not an upgrade.

---

## 5. Drops: fewer, better, and the rest is crafting

### 5.1 Who carries gear

Gear comes only from what visibly carries it; the rank and file never drop gear (they drop ember,
and their people's material at the night's end: crafting §6.1). This is today's rule in the
arenas, now everywhere.

| Source | Gear rolls (today) | Gear rolls (now) | If no gear | Floor and quality |
|---|---|---|---|---|
| Arena champion, captain, keeper | 1 at 60% | 1 at 45% | the people's material ×1–2, or old iron (30%) | – |
| Arena miniboss | 1 at 60% | 1 | + 1 material | Uncommon; Rare+ ×1.5 |
| Arena herald, lieutenant | 1 at 60% | 1 | + 1–2 materials | Uncommon; Rare+ ×1.5 |
| Arena or story boss's hoard | 2 + tier/2 | 2, 3 from tier 3 | + 2–3 materials | first roll Rare; Rare+ ×2; Legendary ×4 |
| Verge elite | 1 | 1 at 70% | the people's material | – |
| Map pack carrier (grade 1 / 2) | 1 / 2 | 1 at 55% / 1 + 40% | material | – / Rare+ ×1.3 |
| Map keeper (grade 3) | 2+ | 2 | + material | first Uncommon; Rare+ ×1.4 |
| Map ruler | 3–5 | 3 + quantity | + 3 materials | first Rare; Rare+ ×2; Legendary ×4 |
| Map strongbox | 3–5 | 2 + quantity | + 2 materials | first Uncommon; Rare+ ×1.5 |

About a third fewer gear drops than today, each one likelier to be Rare or better. A chart's
**quantity** adds rolls and its **rarity** multiplies Rare+ weights, as now. The survivor's
**luck** raises Rare+ weights by half of what it adds (luck 1.4: ×1.2), never the count.

### 5.2 One roll, in order

`Drops.Roll` (logic, `Rpg/Loot.cs`), for each gear roll:

1. **The tier**, from the weights by level (section 3's table; formulas in `loot.json`), with the
   source's multipliers, the chart's and luck. A Set or Legendary is only rolled if one exists that
   may drop here (its least level, its home, its story condition); otherwise that weight falls to
   Epic.
2. **The piece.** A Legendary or Set piece from those allowed here, the ones the survivor has never
   owned four times as likely (duplicate protection), the people's own twice as likely. Otherwise a
   base: a weapon one time in four (two in three of those of the survivor's calling: Diablo III's
   smart loot, the rest to show other ways to play), else armour or jewellery.
3. **Its level and make** (4.1, 4.2).
4. **Its affixes**, leaning to what answers the map or the people (today's `lean`).
5. **The filter's verdict** (section 7), which sets its label, beam and sound.

The piece is rolled whole **when it falls** (today it is rolled when picked up), so the filter
can read its affixes and the beam can say what it is.

### 5.3 Legendaries early, and certain once

- **The first one is certain.** The first story boss a survivor beats drops a Legendary from the
  early pool (least level 1 to 3), leaning to their calling. Diablo III's first-kill rule, here at
  the moment the story most wants to pay.
- **The dark's debt.** Every gear roll that is not Legendary adds one; at 120 the next boss's or
  ruler's hoard holds a Legendary for certain, and the debt clears. It is shown, never hidden (R10):
  on the night's and the map's result, a row of marks under "What the dark owes you" (the story
  lead's words), and "The dark settles up." when it pays. It never switches off.
- **Homes.** Each Legendary and Set piece has a home: a people (twice as likely from their
  carriers), a place or a story condition (the Pelt of the Pack only after the Pack is
  slaughtered). Homes make them huntable at the Wayfinder's table (choose a people's chart to hunt
  their Legendary), the way Grim Dawn's infrequents are.
- **Expected in Act 1** (`LootTests` simulates it from the counts above): about 250 gear rolls,
  three to five Legendaries (one certain), two to four set pieces, fifteen Epics.

### 5.4 Duplicates

A Legendary owned before can still drop (a better make is a better copy); a never-owned one is
four times as likely. An old copy sells, or waits on Rook's shelves. The forge never works a
Legendary or a set piece, and does not yet break one down (crafting's call; they have agreed 5 old
iron and 3 ember shards when it does).

---

## 6. Where things go: the pack and the slotless stores

### 6.1 The rule

**The pack's 24 places hold only what you wear.** Everything else is counted in a store that never
fills and never takes a place:

| Store | Holds | Stacks |
|---|---|---|
| **Pack** (24 places) | weapons, off-hands, helms, bodies, cloaks, amulets, rings, relics | no (each piece is itself) |
| **Pouch** | materials and the crafters' currencies (old iron, ember shards, pelts, hide, cloth, dust, herbs, slurry jars) and **trophies** (Greymuzzle's fang, the map rulers' mark-trophies): what the Waystation's hands work with | counts, no limit |
| **Satchel** | manuals, tomes, the Keeper's Office, and the **Wayfinder's charts** | books by kind (manuals to 3); each chart its own entry |
| **Key ring** | quest things and tools (lockpicks, blasting ember, Wenna's flask, the strongbox, ledgers, keys) | by kind, at the item's stack |
| **Belt** | draughts and remedies (health, moonpetal, antidote, bandages) | counts, a carry limit of 20 each (combat's number to move, not places) |
| **Purse** | gold | a number |

- **Inventory management stays**, where it is a choice: which pieces of gear to keep, and Rook's
  storeroom shelves (crafting prices the second). Gear is what a survivor weighs; herbs are not.
- **Quest things still needed** show a small mark on the key ring and cannot be dropped or sold
  (today's `Needed` rule). Once their part is played they are keepsakes and can go.
- **Tools on the key ring still speak to the world** (`WorldTags` reads them, as it read the pack).
- **A save from before** moves everything that is not gear out of the pack into its store on load.

**Why a belt.** Draughts are drunk from a key; a place in the grid for each stack was the clearest
"cheated" in the owner's sense. Diablo IV and Last Epoch made potions a counter for the same reason.
**Why charts in the satchel.** The atlas's charts multiply in the endgame (Path of Exile's map
tabs exist for this); they are paper, like the books.

### 6.2 When the pack is full

- **In a fight**, a piece you walk over with no room stays where it lies, as today, said once.
- **At the end of a night or a map**, everything the filter **shows** that is still lying comes
  home: into the pack while there is room; Rare and up beyond that to Rook's storeroom ("Rook will
  keep it for you", as the nemesis's returns already say); the rest is broken down for old iron,
  and the result says so. What the filter **hides** is broken down (if the toggle is on, the
  default). **Why**: dodging a horde to vacuum the floor is the genre's worst chore (L8), and a
  thing shown and lost to a fall feels like theft.
- **By day in the Verge**, gear stays on the ground where it fell until taken (persistent, as now).

---

## 7. The item filter

### 7.1 The model (`Rpg/LootFilter.cs`)

A filter is a preset, five toggles, and an optional list of rules. A rule has an **action**
(show, hide, emphasise) and **conditions**, all of which must hold:

| Condition | Example |
|---|---|
| tier | Common, Uncommon, Rare, Epic, Set, Legendary, Storied; material, chart, book, draught, quest |
| slot | helm, ring, weapon... |
| level | at least 20; or within 5 of my level |
| make | Wrought or better |
| affix | any of: of the Salamander, Gravebane |
| grade | any affix at grade IV or better |
| upgrade | better than what I wear in that slot (4.4) |
| calling | a weapon of my calling |

Rules are read top to bottom; the first that matches decides (Path of Exile's rule; Last Epoch's
order is the same idea). If none match, the preset decides. An action also carries the look:
label colour and size, beam on or off, sound on or off, a mark on the minimap.

**Never hidden, whatever the rules say**: Legendary, Set, Storied, quest things, and a piece's first
sighting of its kind (a base or make never seen before). **The hold key** (Alt; the pad's L3 held)
shows every hidden label, and walking over a hidden thing while it is held picks it up.

### 7.2 The presets

| Preset | Shows | Hides |
|---|---|---|
| **Everything** | all of it | nothing |
| **Default** (new characters) | Legendary, Set, Storied (emphasised); upgrades (marked); Epic and Rare; Uncommon; Commons that are upgrades, of a better make than you wear in that slot, or a weapon of your calling; all materials, books, charts, draughts | other Commons |
| **Strict** | as Default | also Uncommon that are not upgrades |
| **Only the best** | Legendary, Set, Storied, Epic, upgrades | the rest |

**Why four**: NeverSink's seven levels show that strictness is the one choice most players make,
and they move up it as their gear improves; four is enough for a game this size and each is a
different sentence. The rule list is for the few, later (UI's screen).

### 7.3 The toggles (the filter page's first face)

1. **Show upgrades always** (on): anything better than what you wear shows, whatever its tier.
2. **Show my calling's weapons** (on).
3. **Show Commons of a better make** (on).
4. **Break down what I hide, at a fight's end** (on): for crafting's old iron.
5. **Drop sounds from**: Rare (default), Epic, or Legendary only.

### 7.4 What the filter does

- **On the ground**: shown things get their label, beam and sound; hidden ones lie unlit and
  silent (still drawn as a small dark shape, so the world is honest).
- **Underfoot**: hidden things are not picked up by walking over them.
- **At a fight's end**: section 6.2.

---

## 8. Presentation

### 8.1 By tier

| Tier | Label | Beam (VFX lead) | Drop sound (placeholders mine, FM synth, ours) | Map |
|---|---|---|---|---|
| Common | small grey text | none | a dull clink: cloth thump for armour, a short iron tick for a weapon | – |
| Uncommon | green text | a low glow, 0.8 m | the clink and a soft high ring | – |
| Rare | blue text on a dark plate | 2.5 m, steady | one clear bell, struck once | small dot |
| Epic | violet, bordered plate | 5 m, a slow pulse | a struck bell held, with a low hum under it | violet diamond |
| Set | verdigris, double border, chain-link mark | 6 m, two strands that twist | two bells a fifth apart, struck together: a pair | verdigris diamond |
| Legendary | amber, large, framed, a slow shimmer | the sky pillar (8.2) | the toll (8.2) | amber star, and the screen's edge |
| Storied | ember red, framed | the pillar ringed in sparks | the toll, then a breath of fire | ember star |
| Material | small text in its colour | none | a soft pat | – |
| Chart | parchment text | 2 m, pale | paper and a small chime | chart mark |
| Quest | gold text | 1.5 m, gold | a short warm chime | – |

Rules: the beam's height says the tier; colour says the band; a **mark** on the label says the
exception (an up-arrow for an upgrade, a small anvil for a better make than worn). Drop sounds play
**when the thing lands**, from where it lands, so a Rare dropped behind you is heard behind you;
the pickup keeps its short sound. A tier's sound plays at most twice a second (a boss's hoard of
three Rares rings once, a little louder, not three times).

### 8.2 The moment a Legendary falls

1. **The fall.** The carrier dies; the thing falls with a heavier arc than gear, and lands.
2. **The hush.** For a second the music and the world's noise drop away (never the fight's own
   sounds: a warning under a hush is a blow unheard, combat's rule), and the
   **toll** sounds: a deep bell, a fifth and an octave above it, long in the air, like the toll
   bell at Vonnra's tower. It is never heard for anything else.
3. **The pillar.** An amber pillar rises from it past the top of the screen, a ring of embers on
   the ground round it, its light thrown on the creatures near it. If it lies off screen, the
   screen's edge glows amber where it is.
4. **The word.** A line under the HUD: "This one has a name." (the story lead's words; when the
   dark's debt pays it, "The dark settles up.").
5. **Until taken**, a faint toll every eight seconds, and the pillar stays.
6. **Taken**: a reveal like the chest's (the experience director stages it): the name in amber,
   the power, the lore line. The first Legendary a survivor ever takes is held longer, and the
   game pauses for it in an arena (Vampire Survivors' chest pauses its world; a Legendary is rarer
   than any chest).

The Set moment is the same, smaller: no hush, the pair of bells, the twin beam, and on taking it,
"2 of 3: the Watch's Kit" if it completes a bonus.

---

## 9. Loot across the game

| Where | Gear from | What it pays besides | Notes |
|---|---|---|---|
| **Story nights** (story arenas, 10–14 min) | champions, the stage's miniboss, the boss's hoard | the people's material, ember shards (crafting §6.1) | The first story boss beaten: the certain Legendary. Each story boss twice as likely to drop its people's Legendary. |
| **The Verge by day** | elites, places (shrines, caches: the story's) | the beasts' materials | Persistent on the ground. The early Legendaries' homes are here and in the first nights. |
| **The atlas** (permanent maps) | packs' carriers by grade, keepers, the ruler, strongboxes | materials, charts, mark-trophies | Level = the map's (8 + 2 × tier), so the make climbs with the tier: the atlas is where Wrought to Heartwrought bases come from, and where Set and Legendary homes are hunted by people. |
| **The scars and table nights** (survivors arenas, endless) | champions' turns, minibosses, heralds, the boss | shards (more the longer), the people's own | Past the half hour each minute adds 2% to Rare+ weights (to double at 80 minutes) and the Legendary weight grows with it: staying is how the scars pay. Gathered at the end (6.2). |
| **Crafting** | – | old iron from what is broken down, hidden drops broken down automatically, the materials that replace a third of the gear drops | The forge turns a good base into the best version of itself; the best things still come from the world (crafting C8). Legendaries and set pieces are never worked. |
| **Shops, quests** | at the survivor's level | – | Never a Legendary for gold (R21). Quest rewards can be named pieces. |

---

## 10. Content

### 10.1 The first Legendaries

Eight in Act 1, the Moonsilver Circlet among them. Four drop from level 1 to 3 (the early pool,
from which the certain first one comes). Each is built on a base, so a later copy is a better
make. The lore is the story lead's (WRITING_PASS §25), verbatim: none says an act's answer early
(`STORY_BIBLE.md`), the Kerchiefs' town stays unsaid, and "Forty-One Mouths" stays C06's.

| Legendary | Slot (base) | Least level | Home | Power (how it changes play) | Price | Lore |
|---|---|---|---|---|---|---|
| **The Drowned Coat** | body (padded jerkin) | 1 | the Risen; the Verge's drowned | Your dash leaves black water for 3 s that slows what wades in it by 40%; +30% fire resistance. *You dash through the crowd, not away.* | You mend 15% less. | "Wrung out, it is wet again by morning. Whoever wore it last went into the ford in it, and did not come out." |
| **Nan's Cleaver** | weapon (butcher's cleaver) | 2 | the Kerchiefs | Below half health every kill mends 2% of your health; your blows bleed (15%). *You fight best hurt.* | Above four fifths of your health you deal 15% less (combat: "at full" is never true in a horde). | "Firepot Nan's, from the Roost's kitchen. It has jointed everything the road brought in, and the road brought in a great deal. She will want it back." |
| **Corran's Sword** | weapon (worn oathblade) | 3 | the Risen | Standing still, your weapons strike 25% faster, and a blow that lands sends a ring of steel round you, once a second. *Plant your feet in the horde.* | 8% slower. Holloway knows it (tag). | "Notched along the spine in tens, the way a man counts nights on a post nobody relieves. The Watch's book has him down as a deserter." |
| **Ditchwater** | weapon (hunter's crossbow) | 3 | the Risen; the Low Ford road | Volley's bolts pierce one more and chill what they pass through. *Line them up.* | – | "Pulled out of the ditch on the Low Ford road, wound and loaded, with weed in the stock. Whoever loaded it never got to fire it." |
| **The Fever-Year Staff** | weapon (ember staff) | 6 | the Risen | Cinderfall poisons as it burns; what dies poisoned passes the poison to three near it. *Seed a plague, then walk.* | You mend 10% less. | "Charred to the grip. In the fever year they burned the bedding of the dead, and somebody stirred the fire with this until it was done." |
| **The Slurry Wheel** | off-hand (old watch shield) | 6 | the Lamplings | Every block throws slurry round you: poison on everything within 3 m; you block more often. *Stand in it and let them come.* | 15% more damage from lamplings. | "A spare wheel off the Dig's pump, beaten flat and strapped for an arm. It still weeps green." |
| **Kell's Lamp** | relic | 8 | the Lamplings | Every two seconds your lamp flares: fire on everything within 3.5 m. *Your light is a weapon; stay close.* | – | "It came back up the shaft on its own, still lit. Kell did not." |
| **Moonsilver Circlet** (exists) | head | 10 | the Moon Grove; Vonnra's stock | as today: +15% damage at night; crits at night call moonlight | – | as today |

Story-gated, given or dropped only on a branch: **Pelt of the Pack** (cloak; after the Pack is
slaughtered; every wolf killed this fight +2 health, to +80; "Grey to the roots, and stitched from
more than one wolf. Maeca could tell you whose, and won't."). No item grants a rise from death (principle 5): the items
plan's Snib's Hard Hat and Kell's revive are cut for the owner's rule.

### 10.2 The first sets

**The Watch's Kit** (3; least level 2; the Risen, who were the Watch; a teaching set)
- Watch Coif (head, on the iron helm): +12 health. Watch Hauberk (body, on the chain shirt): +3
  armour. The Watch's Torch-Shield (off-hand, on the old watch shield): +10% holy damage.
- **2 worn**: +25% armour; your light carries 25% further.
- **3 worn**: standing still, you block a blow every six seconds, as a shield-wall does. The Watch
  takes you for one of its own (tag).
- "Eleven men on a wall built for sixty, and every one of them still oils his mail."

**The Levy Red** (3; least level 5; the Kerchiefs; not "the Red Hand", which is their map ruler)
- Roost Hood (head, on the leather cap): +4% critical chance. Levy Colours (cloak, on the
  traveller's cloak): +5% speed. Kerchief Knives (weapon, on the knife belt): Knifestorm.
- **2 worn**: +6% critical chance; Kerchiefs take you for one of theirs (the red kerchief's tag).
- **3 worn**: your thrown and loosed skills fly one more; your critical strikes bleed.
- "Red was a town's colour before it was a gang's. Nobody in the Roost will tell you which town."

**Why these two**: one teaches what a set is, early, cheaply, for any calling; one is a way of
fighting in a people's colours that Act 1 already sets up. Three pieces each (R5: small sets that
leave room for Legendaries and Rares). The items plan's other eight sets wait for their acts.

### 10.3 Commons, trimmed

- **Eighteen of the twenty-eight Commons never take a place again**: the six materials go in the
  pouch, the three draughts on the belt, the lockpicks on the key ring, the chart in the satchel,
  and the nine starting weapons stay what they are (the calling's). What is left in the grid are
  bases, and every base now has two implicits that scale with its make:

| Base | Implicits (Worn) |
|---|---|
| Leather Cap | +2 armour, +16 health |
| Iron Helm | +3 armour, +8 health; 2% slower |
| Padded Jerkin | +3 armour, +12 health |
| Chain Shirt | +5 armour, +6 health; 4% slower |
| Traveller's Cloak | +3% speed (never scaled), +3 armour, +12 health |
| Copper Ring | +1.5% critical chance |
| Silver Ring | +6% damage to the dead |
| Knucklebone Amulet | +6 health, +0.2 health a second |
| Old Watch Shield | +3 armour, block |

- **Fewer Commons fall** (41% of rolls at level 1, 17% at 16, 3% at 40), and the Default filter
  hides those that are not upgrades or a better make. Of the Commons a player meets late, the ones
  that show are the ones worth reading.

---

## 11. What is built (logic), and its tests

| Piece | Where | Tests |
|---|---|---|
| Tiers, power score, make, item level, grade shift | `Rpg/Loot.cs`, `Rpg/Character.cs` (`ItemInstance.Level`, `Inventory.Mods`) | `LootTests`: tier of each kind; make by level; the three "Common beats" claims; grades unchanged below 25, raised past it |
| Drop roll and tables | `Rpg/Loot.cs`, `data/content/loot.json`; the four zones call it | weights by level; floors; sources; set and legendary eligibility and homes; the first certain Legendary; the debt; duplicate protection; the Act 1 simulation |
| Stores | `Rpg/Character.cs` (`Inventory`: satchel, key ring, belt; `Find`, `Count`, `Take`, `Remove`), `World/Save.cs` | routing of every kind; stacking; counts and takes across stores; quest things; charts; the save's move out of the pack; world tags from tools |
| Filter | `Rpg/LootFilter.cs` | presets; first match; never-hidden; toggles; upgrades |
| Sets and Legendaries | `items.json`, `loot.json` (`sets`), `Character.Kit` | bonuses at 2 and 3; content valid (powers parse, homes exist, least levels) |
| Drop event and placeholder sounds | `Sim` (`Ev.Drop`), `src/Audio/Sfx.cs` | – (heard in the game) |
| End-of-fight gathering | `Arena/Arena.cs`, `Play/Zones/MapRun.cs` | gathers shown, breaks hidden, overflow to the storeroom |

---

## 12. Asks of the other areas

- **UI design** (Pack, Storeroom, Trader, filter): the stores as tabs (Pouch, Satchel, Key ring,
  **Belt**), the level and make on tooltips, Set and Legendary tooltips, the up-arrow and anvil
  marks, the filter page (presets and toggles first, rules later), and the night's result listing
  its finds best last as the map's does. **Answered** (aab47bfdab5955dac, in
  `docs/handoff/ui_design.md` at ed2ea5c5): four tabs fit; the satchel is a scrolling list sorted
  by tier; the level is a bare number top-left on a tile, the up-arrow top-right; Set gets the
  chain-link mark; Legendary tooltips about six lines; the filter page is four presets across the
  top, toggles in a column, rules later below.
- **Skills VFX** (beams and drop effects): beams by tier per 8.1; the Legendary pillar, ground ring
  and screen-edge pointer (8.2); the Set's twin beam; hidden things drawn small and unlit; a look
  for the Drowned Coat's black water (`zone_drowned`).
- **Crafting**: the ilvl grade shift past 25 (4.3) against your forge caps; Legendary and set
  pieces never worked; break-down yields for hidden drops; trophies now in the pouch and charts in
  the satchel (the `Inventory` calls to use are in my branch: `Inventory.Holds`, `Inventory.Remove`);
  the materials that replace a third of gear drops against your economy targets.
- **Combat**: the drop counts and weights (5.1) and every Legendary's numbers; the moment's
  half-second hush in a fight; whether "standing still" and "at full health" read in the horde.
- **Experience director**: the Legendary moment and the first-Legendary pause; whether drops
  "mostly feel good" in a night as played.
- **Story**: answered (WRITING_PASS §25): the lore, verbatim; "This one has a name."; "What the
  dark owes you" and "The dark settles up."; the makes' names, yes. Holloway's line for Corran's
  Sword waits for this branch on the integration branch.

---

## 13. Decisions, and why

1. **Set is its own tier for the eye, rarity 3 underneath.** The owner thinks in greens, blues,
   purples, legendaries and sets; the forge's heat and seams read rarity, so the number stays.
2. **Make scales the base, grades stay fixed.** The owner's "late common beats early purple" needs
   the base to grow; crafting's readable grades need affixes not to. Diablo IV scaled everything
   and rarity stopped meaning anything.
3. **Grades rise only past level 25.** Act 1's forge economy was measured against today's grades.
4. **Gear only from carriers, a third fewer, the rest materials.** D4's Loot Reborn, and the
   survivors genre's rule that loot comes from what visibly carries it.
5. **A certain first Legendary, and a visible debt.** The owner's "huge dopamine spike" at low
   level, without making Legendaries common.
6. **The pack holds gear only.** "Not cheated"; and the management that stays is the interesting
   one.
7. **Trophies in the pouch, charts in the satchel, draughts on the belt.** Each is counted or
   read by kind, never placed; the belt is the one store the brief did not name.
8. **Hidden drops are broken down at the end, not left.** No dead drops (crafting C9), no chores.
9. **No Legendary grants a rise.** The owner's rule for story fights and maps.
10. **Rolled when it falls.** The filter and the beam must know what it is before it is taken.
