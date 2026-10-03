# Acquisition: where gear comes from

Every source of gear, by day and by night: what drops from whom, what the
oaths and the people change, what the story gives and to whom, what the shops
sell, the one gamble, and the rules that make target farming possible and bad
luck short. Rarity and item level are defined in `SYSTEM.md` §2 and §6.2; the
level bands in `PROGRESSION.md` §1.

The principle (`VISION.md` §3.7): **luck decides when, the player decides
what.** Every Named item has a home that can be farmed; nothing good is only
random.

---

## 1. The shape of it

| Source | Half | Volume | Quality | Job |
|---|---|---|---|---|
| Day elites and packs | day | low | Plain to Rare, ilvl = creature level | keeps the day rewarding; materials |
| Story fights and places | day | a few, authored | Named, often Storied | the story's gifts; choices made visible |
| Quests and people | day | authored | Fine to Named | relationships pay in gear |
| Shops | day | restocking | Plain to Rare; a few Named | bases on demand; a gold sink |
| Arena champions, heralds, the boss | night | the main flow | Fine to Named, ilvl from tier | the engine of gear progression |
| Arena spoils screen | night | – | – | gathers it all; no pack Tetris |
| Echoes and Depths | night, endgame | low, rich | Named-heavy | target farming at the top |
| The toll lots (gambling) | day | gold-limited | Fine to Named by slot | a gold sink with a target |

---

## 2. By night: the arenas

### 2.1 What drops, run by run

Today: champions drop gear 30% of the time × the oaths' `Gear`, the boss
2 + tier/2 items at Uncommon or better, chests give ember (not gear), and all
of it rolls one of nine Plain bases. Proposed:

| Source | Count | Chance of gear | Floor | Notes |
|---|---|---|---|---|
| Champion (elite) | ~20–30 a run | 25% × oath `Gear` | – | ilvl = arena ilvl |
| Champion's chest (from a champion event) | 4–6 a run | ember upgrades, as now; plus 20% a sigil-stone (phase 4) | – | the chest stays the ember's: Vampire Survivors' best moment |
| Herald (minutes 10 and 20) | 2 | 1 item, 100% | Fine; 25% Rare+ | ilvl + 1 |
| The boss (minute 30) | 1 | 2 + tier/2 items | one Rare guaranteed | ilvl + 2; the Named roll and the tally (`§7`) |
| Beyond the half hour: a herald every 5 minutes | open | 1 item each | Rare | rewards staying, as the code already does with heralds; ilvl + 2 |
| Story arena won | – | its authored reward | – | `§6` |

Expected per won run at a tier on the survivor's band: **8–12 items**, about
4 Plain, 3 Fine, 2–3 Rare, 0.5 Marked, 0.2 Named; with the filter at its
default, the spoils screen shows the 3–5 that matter.

### 2.2 Rarity

One table for every non-boss gear roll; the boss rolls with the luck doubled.
"Luck" here is the oaths' `Gear` product (×1.0 to about ×3.0 with three
generous oaths), not the survivor's Luck stat (which stays a card stat).

| Rarity | Base weight | Per tier above 1 | Notes |
|---|---|---|---|
| Plain | 45 | −1.0 | |
| Fine | 35 | −0.5 | |
| Rare | 15 | +1.0 | |
| Marked | 4 | +0.4 | only from ilvl 12 |
| Named | 1 | +0.1 | a set piece one time in three |

Luck divides the roll as `ArenaRun.Rarity` does today (`roll / luck`), so a
×1.5 oath pushes everything up a little and Named items most of all.

### 2.3 What base

Each people has signature base families (`§4`), weighted ×3; every other
base can still drop. Base tier is the highest the ilvl allows 50% of the
time, one below 35%, two below 15%. **Smart loot, softly:** gear rolls a
base that favours the survivor's calling's best attribute 40% of the time
(Diablo III's smart loot was loved; full smart loot also made every drop
predictable, so this is a lean, not a rule).

### 2.4 Item level

`ilvl = 3 × tier + 2` (+1 heralds, +2 the boss and beyond the half hour, +2
for the Oath of the Deep Dark), capped at 40.

## 3. Oaths: what each changes in the loot

Oaths already lean affixes toward what answers them (`OathDef.Lean`). Keep
that, and give each one loot identity of its own, so choosing a map from the
Wayfinder's table is choosing what to hunt.

| Oath | Asks | Gives (ember / gear) today | Leans affixes to (today) | Loot identity, proposed |
|---|---|---|---|---|
| Swarm | packs ×1.5 | ember ×1.5 | reach, haste | set pieces ×1.5 (the many have many pieces) |
| Champions | elites ×2 | gear ×1.6 | keen, cruel | Marked chance ×1.5 |
| Deep Dark | +2 levels | gear ×1.4, ember ×1.2 | hale, sturdy | ilvl +2 |
| Long Vigil | waves ×2 | gear ×1.3 | reach, mending | notches +1 on bases; Watchword fragments |
| Long Winter | chill on hit | gear ×1.5 | hearth, surefooted | frost Marks ×3; Rime catalyst ×3 |
| Blight | poison, less healing | ember ×1.4 | physician, mending | slurry jars drop (`CRAFTING.md` §7); nature Marks ×3 |
| Embers | burning ground | gear ×1.4 | salamander, fleet | fire Marks ×3; ember shards ×2 |
| Hunt | foes ×1.2 speed | ember ×1.25, gear ×1.2 | fleet, surefooted | cloaks and dash affixes ×2 |
| Iron | non-crits ×0.67 | gear ×1.5 | keen, cruel | Named chance ×1.5 |
| Moonless | light ×0.5 | elites ×1.3, gear ×1.3 | lantern | relics ×3; Named relics ×2 |
| Ruin | death bursts | ember ×1.5 | sturdy, reach | sigil-stones ×2 |

## 4. The people who hold an arena

Each people (`MapOffers.Peoples`) has a loot table of its own: signature bases,
materials, its set and its Named items. Act 2 and 3 add three peoples (the
Vigil, the Fevered, the Legion), following the story's turn
(`STORY_BIBLE.md` §7, §8).

| People | Signature bases | Materials | Set | Named items at home (`CATALOGUE.md` §6) | Boss |
|---|---|---|---|---|---|
| **The Pack** | hides, fur cloaks, bone amulets, bows | wolf pelt, boar hide | The Pack's Own (3) | Greymuzzle's Fang (amulet), the Old Hunter's Cloak (rerolled), Pack-Mother's Collar, Moonsilver Circlet (Moon Grove only) | the Pack-Mother |
| **The Risen** | barrow mail, grave lanterns, bone wands, Legion fragments (Tier IV) | barrow dust | – (their Legion set comes in Act 3) | Barrow-Bone Charm, the Barrow Lord's Helm, Wat's Whip, the Drowned Coat | the Barrow Lord |
| **The Lamplings** | lamps, picks, leather caps, ember-staves | ember shard, slurry | The Dig (3) | Grimtunnel's Spare Lamp, Snib's Hard Hat, the Pump-Wheel Buckler | Grimtunnel, Roused |
| **The Kerchiefs** | knives, crossbows, red cloth, brigandines | red cloth | The Red Hand (stalker, 4) | the Red Kerchief (rerolled), Ashford Levy Colours, Redcowl's Hood (only if he lives, `§6`) | the Red Hand |
| **The Vigil** (Act 2) | argent plate, silver rings, swords, censers | silver ink, argent scraps | The Argent Vigil (warden, 4) | Chapter Four (Keegan's handbook), Sallow's Silver Pen, the Cage Key | Sallow's champion |
| **The Fevered** (Act 2, the breakthrough) | masks, cloth, flasks, seed pouches | bitterroot, moonpetal | – | the Blightward Mask (rerolled), the Penhale Lantern | the Thing in the Barn |
| **The Legion** (Act 3) | Legion and Heartwrought everything | Legion seals | The Seventh Legion (4) | the Inner Door's Toll (relic), What It Could Not Burn (weapon), the Standard of the Seventh | the Centurion of the Stair |

**Echoes** (endgame, `PROGRESSION.md` §6): story foes return at the table, each
with its people's table and three Named drops at ten times their usual chance.
The Ford-Warden echo is the only home of the Ford-Warden's Lamp (a relic
counterpart to the Lamp-Iron).

## 5. By day

### 5.1 Packs and elites

Verge elites today drop one of nine Plain bases with a rarity rolled from
their level. Proposed: the same people tables as the arenas (a wolf elite drops
like the Pack), ilvl = creature level, rarity from §2.2 with no oath luck, and
a third of the arena's rate: the day is for the story; the night is for gear.

### 5.2 Places

Hand-placed finds are exploration's reward (Elden Ring's lesson, `RESEARCH.md`
§7). Each zone should hold a few, authored, never respawning:

| Place | What lies there | Condition |
|---|---|---|
| The Low Ford (prologue) | The Warden's Lamp-Iron (exists) | kill the Warden |
| The Old Watch-post | Corran's Sword (Sound sword, a Named rework: "Held at his post") | find the post |
| The Moon Grove | the Moonsilver Circlet (today a 15% Vonnra stock line: move it here) | open the bramble wall |
| The caravan wreck | the Watch's Kit, one piece (teaching set) | – |
| The Sealed Vault, outside | a Legion fragment (Plain Tier IV base, unusable until the affinity is met) | – |
| The Sinkhole | a pale Heartwrought shard (crafting curiosity, Act 1 tease) | faith knowledge |
| Redcowl's Roost | a Red Hand set piece | the Roost cleared or Redcowl dealt with |
| The Dig | Grimtunnel's Spare Lamp (exists), Snib's Hard Hat | `dig.pump` broken / Snib bribed |

### 5.3 Quests and people

Rewards should be the person's own thing, with lore in their voice:
- **Maeca**: a bow she has kept since Ashford (cured or allied wolves);
  "Maeca's Last Arrow" (Storied; only if she becomes the survivor's lover).
- **Wenna**: the Blightward Mask (exists) for the cure; tinctures after.
- **Holloway**: the bounty, and a Watch officer's cloak if the road is safe.
- **Brannoc**: a commissioned piece (`CRAFTING.md` §3) once he trusts you; the
  last two lamp-irons if he forges them (Act 2, a dark gift).
- **Chid**: the Pilgrim's Ember-Lantern blessed (Storied) for the devout.
- **Harlan**: a Coyle Company signet (ring) if the cargo comes home.
- **Pell**: Varrow Imports' "special stock" if allied.
- **Keegan** (Act 2): a Vigil piece if she comes north with you; her own blade
  if she dies at the gate.

### 5.4 The nemesis

`BETA_DESIGN.md`: the creature that killed the survivor carries one item and
roams. Keep, and add: taking it back writes a history line (`SYSTEM.md` §9),
and the nemesis carries one item of its own, a Rare or better of its people,
rolled at the survivor's level + 3.

## 6. Choices made visible

Some Named items exist only on one branch of the story. This is the strongest
reason to replay, and it makes every outcome pay something.

| Fact | Outcome | Item it opens |
|---|---|---|
| `beasts.outcome` | slaughtered | **Pelt of the Pack** (cloak: health, speed; every wolf in the valley knows) |
| | allied | **Greymuzzle's Collar** (amulet: your summons are wolves; the Pack walks with you in arenas held by the Pack) |
| | cured | **Moonpetal Crown** (head: mending, nature; Wenna's gift) |
| | exploited | **Pell's Bounty Purse** (relic: gold and a price: the Pack hunts you in the Verge) |
| `caravan.cargo` | kept | the **Coyle Strongbox** opens: three Rares and a Coyle signet |
| `be.crates` | redcowl | **Ashford Levy Colours** (cloak, Red Hand set): the Kerchiefs let you pass |
| `redcowl` | killed | **Redcowl's Hood** (head, Red Hand set; lore says his name only after Act 1 ends) |
| `pell.fate` | ran | **Varrow Silver** (ring) when he returns in Act 2 |
| `nell.told` | gone or risen | **Brannoc's Twelfth Iron** (relic, Act 2: he breaks eleven and keeps the last for you) |
| `nell.told` | lie | Brannoc's service ends; **the Kiln Ford** becomes an arena (Act 2) with its own Warden's drops |
| `maeca.lover` | – | Maeca's Last Arrow (Storied, Act 2) |
| `keegan` | comes north | **Chapter Four** (relic) |

## 7. Bad luck, duplicates and target farming

### 7.1 The Wayfinder's tally (Named pity)

Ysolde writes down who comes back from her maps (her secret, `STORY_BIBLE.md`:
she sells the list). The tally is the honest half of that habit: a row of notches
on the table, **visible**, one for every arena boss slain without a Named drop.
At five notches the next boss drops a Named item for certain, from that people's
table, and the tally clears. It never caps and never resets otherwise.
(Research lesson 10: pity must be visible and never silently stop.)

### 7.2 Duplicate protection

- A Named drop prefers items the survivor has never owned, 70% of the time,
  until all of a people's table has been seen once.
- A set piece prefers pieces the survivor lacks, 2 to 1.
- A Mark already in the binders' book at its best strength is still worth
  salvaging (sigil chips), and a better one upgrades the book.

### 7.3 Target farming, all the ways

| Goal | How |
|---|---|
| A particular Named item | its people's arenas (×3 weight at home); its echo (×10); Vonnra's fortune (×5 for a week) |
| A set | its people; the Oath of the Swarm; the missing-piece lean |
| A Mark | the oath that leans to its school (×3); or press it from the book |
| A school's affixes | the map's oaths and people already lean (`MapOffers.Lean`) |
| A base | Brannoc's commission; the toll lots by slot |
| A Watchword | its recipe (found), its sigils (Ruin oath), a Plain base with the notches (Long Vigil) |
| Higher ilvl | higher tier; the Deep Dark |

## 8. Shops and vendors

Today's six keep their character and gain a job each in the item system.

| Vendor | Today | Proposed additions |
|---|---|---|
| **Brannoc's Smithy** | Plain bases, starting weapons, the Ashen Plate | bases up to the highest tier the story has opened; **crafting** (salvage, temper, rework, notches: `CRAFTING.md` §3); commissions. If his service ends (Act 2), Snib's bodgery takes it, worse and stranger. |
| **Coyle Trading Post** (Harlan) | draughts, Plain jewellery and cloaks | **dyes** (`looks.json` cloak dyes and more); materials bought; a weekly caravan of Fine bases if the cargo came home. |
| **Wenna's Remedies** | cures, the thornseed pouch | **tinctures** (`CRAFTING.md` §4): a chosen resistance or mending affix added. |
| **Rav's Table** | a fence: buys everything; lockpicks, kerchief, knives | the **tailor** (glamour and dye, `VISUALS.md` §7): he "sews a fair seam"; buys back what you sold today; **cart lots** (a cheaper gamble, Kerchief pieces likelier). |
| **Vonnra's Curiosities** | relics, charms, totems, the circlet (15%) | the **toll lots** (`§9`); the **binders' book** (Marks); sigil-stones combined; the weekly fortune. |
| **Varrow Imports** (Pell) | censer, bone charm, tether, wands, blasting ember | foreign bases (chakram, green lens, quiver); one Marked item a week, dear. |
| **The shrine** (Chid) | – | **consecrate** (`CRAFTING.md` §6); cleanse a slurried item. |
| *Act 2:* the Vigil quartermaster at Silverstair | – | argent bases; a set piece if Keegan stands with you. |
| *Act 3:* Snib's bodgery | – | everything Brannoc did, at odd odds, and slurry steeping done properly. |

Prices follow the code's `markup` and `pays`; bases cost about **10 × ilvl ×
tier** gold, and Rares four times a Plain.

## 9. The toll lots (gambling)

Vonnra sells **lots**: unclaimed goods held at the toll, sealed, sorted by
slot. Pick a slot and pay; the lot opens on the counter. (Diablo II's gambling
and Diablo III's Kadala: the gold sink with a target.)

| Outcome | Chance |
|---|---|
| Fine | 55% |
| Rare | 33% |
| Marked | 9% |
| Named (of any people) | 3% |

Price: 40 × ilvl gold, at the survivor's level + 2. The lots count toward the
Wayfinder's tally at half a notch per Named-less lot. Rav's **cart lots** are
half the price with a third of the Named chance and Kerchief pieces likelier.

Lore: the lots are what the drowned left at the toll. The survivor will
understand that later than the player does (Act 2).
