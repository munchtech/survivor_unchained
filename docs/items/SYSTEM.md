# The item system

The whole of Survivor Unchained's itemization: what an item is, how it is
built, how it rolls, how it reads, and how it meets the rest of the game (the
callings, the skill schools, the ember build, the blessings, the oaths). The
principles behind every choice here are in `VISION.md`; the concrete content
(names, numbers, lore) is in `CATALOGUE.md`; where things come from is
`ACQUISITION.md`; what the survivor can do to them is `CRAFTING.md`; the
curves are `PROGRESSION.md`.

Every number below is a **proposal** for the main session and the balance lab,
calibrated against the code as it stands (`StatBlock`, `ArmorReduction`,
`Enemies.ScaleFor`, `Weapons` rank growth). None of it is in the game yet.

---

## 0. What exists today (the starting point)

Read from `godot/logic/Rpg/Items.cs`, `Character.cs`, `items.json`,
`shops.json`, `Maps/MapOffers.cs`, `Play/Zones/ArenaRun.cs` and `Verge.cs`.

| Piece | Today |
|---|---|
| Slots | Nine: weapon, off-hand, head, body, cloak, amulet, two rings, relic. |
| Rarities | Six names (`raritynames`): Common, Uncommon, Rare, Epic, Legendary, Storied, with colours in `Style.Rarity`. |
| Bases | Nine plain bases roll affixes (`"base": true`): leather cap, iron helm, padded jerkin, chain shirt, traveller's cloak, copper and silver rings, knucklebone amulet, old watch shield. |
| Weapons | Nine starting weapons and five skill off-hands. **A weapon is a combat skill**: `ItemWeapon { Id, Rank }`. Its rank rises by one for every rarity step above its def's own. They never roll affixes. |
| Affixes | 33, written in C# (`Items.Affixes`), prefix or suffix, each a function of a tier 0–3. Tier = rarity − 1 + (0 or 1). No item level, no roll range: two Rare "Hale" items are identical. |
| Affix count | `min(3, rarity)`: Common 0, Uncommon 1, Rare 2, Epic+ 3. |
| Skills worn | Five suffixes (`Grants`) put a combat skill in the kit at rank 1 + tier/2. |
| Named things | About fifteen authored items with mods, triggers, world tags, a downside and a lore line (the Ashen Plate, the Warden's Lamp-Iron, the Moonsilver Circlet). Four are `unique`. |
| Storied | `ItemInstance.Name` and `History` exist (a given name and a line per owner) but nothing writes them yet. |
| World tags | Items carry tags the world reads (`wolf_fang`, `kerchief_colors`, `plague_mask`): a statement to a wolf, a disguise to a Kerchief. |
| Drops by day | Verge elites drop one of the nine plain bases, rarity rolled from creature level. Families drop materials (pelts, hides, red cloth, ember shards, barrow dust). |
| Drops by night | Arena elites (30% × the oaths' gear multiplier), chests (ember upgrades, not gear), and the boss (2 + tier/2 items, at least Uncommon, plus a movement manual). Drops **lean** toward the affixes that answer the map's oaths and people (four times as likely). |
| Shops | Brannoc (smithy), Harlan (trading post), Wenna (remedies), Rav (fence), Vonnra (curiosities), Pell (imports). Stock lines with rarity, chance and story conditions. |
| Into the arena | Gear's stats, triggers and statuses go in; so does every skill the gear grants (the weapon's and any worn), which takes one of the six ember weapon slots. Learned day skills do **not** go in. Gear statuses also feed the ember draft's affinity (`LevelUp.BuildStatuses`). |
| How it looks | Only the weapon changes the survivor (nine items map to held models in `Loadouts.Held`). Head, body and cloak items change nothing on the figure. |
| Pack and stash | 24 pack slots, 48 stash slots, no tabs, no filter. |

What is good and must be kept: the **weapon is a skill**; **items speak to the
world** (tags, downsides, lore); **maps lean the loot** toward what answers
them; **named things never roll**. What is missing: item level, roll ranges,
enough bases to climb through, a power layer between "rare" and "named", sets,
crafting, a reason to keep fighting at the top, and any change to the figure.

---

## 1. Shape of an item

Every piece of gear is the same five layers, top to bottom, and the tooltip
shows them in that order.

```
  ┌──────────────────────────────────────────────┐
  │ NAME (rarity colour)            [calling mark]│  1. identity: name, rarity, base, tier
  │ Rare Mail Hauberk · Tier III · ilvl 18        │
  ├──────────────────────────────────────────────┤
  │ +14 armour        (implicit, from the base)   │  2. implicit: what the base always gives
  │ Edge: +35% to Steel skills                    │     (weapons: the skill it brings, its rank)
  ├──────────────────────────────────────────────┤
  │ +48 health                                    │  3. affixes: rolled, 0–4
  │ +21% fire resistance                          │
  │ ✶ +4 Might                   (a bright affix) │
  ├──────────────────────────────────────────────┤
  │ MARK OF THE OPEN GATE  (violet)               │  4. power: a Mark, a unique power,
  │ Your dash leaves a ring of holy fire...       │     or a set's bonuses
  ├──────────────────────────────────────────────┤
  │ ◇ ◇ ◆ Lamp   (notches and sigils)             │  5. notches (sockets), heat, history
  │ Heat 9 · "Taken back from Ash-Fang, night 12" │
  │ The world: Wolves smell the forest on you.    │     world tags, downside, lore
  │ "It weighs what it weighs."                   │
  └──────────────────────────────────────────────┘
```

### Data (proposed)

```
ItemDef (authored, data)                 ItemInstance (rolled, saved)
  id, name, kind, slot                     uid, def
  base: BaseDef?   (tier, implicit,        ilvl                  (new)
        weight, look, notchMax, edge)      rarity
  weapon: { skill, rank }                  affixes: [{ id, grade, roll, bright }]   (roll new)
  unique/set/storied power                 mark: { id, roll }?   (new)
  mods, triggers, tags, statuses           notches: int, sigils: [id]   (new)
  downside, lore, look                     heat: int             (new)
  requires (soft): attribute, amount       name?, history[]      (exist)
                                           look?: { dye, glamour }   (new)
                                           flags: unlit, slurried, storied   (new)
```

Today's `AffixRoll { Id, Tier }` becomes `{ Id, Grade, Roll }`: grade 1–7,
roll 0–1 within the grade's range. A save from before migrates tier `t` to
grade `t + 1` and roll 0.5 (`IMPLEMENTATION.md`, phase 1).

---

## 2. Rarity, and how it reads

Six rungs, the same six indices the code has, renamed for the world and given a
job each. The colour is the colour already in `Style.Rarity`; the beam and the
sound are new (`IMPLEMENTATION.md`, phase 2).

| # | Code name | In the world | Colour | What it is | Affixes | Power layer | Beam, sound |
|---|---|---|---|---|---|---|---|
| 0 | Common | **Plain** | ash grey `#c8c0b0` | A base and nothing else. Worth it for the base: tier, notches, a good implicit. | 0 | – | none; a dull clink |
| 1 | Uncommon | **Fine** | green `#6fd46a` | Something a smith was proud of. | 1–2 | – | a short low beam; a soft ring |
| 2 | Rare | **Rare** | blue `#5aa8ff` | The backbone of every build. A two-word name of its own. | 3–4 | – | a tall beam; a clear bell |
| 3 | Epic | **Marked** | violet `#c070ff` | A Rare that came out of the dark with a **Mark** burned into it: a power that changes how a skill or an art works. | 3 | a Mark | a tall beam with a slow pulse; a struck bell, held |
| 4 | Legendary | **Named** | amber `#ffb040` | An authored thing: fixed powers, rolled within ranges, a lore line, often a downside, sometimes a word to the world. **Set pieces** are Named, with a silver ("argent") rim and the set's name. | fixed | a unique power, or set bonuses | an amber pillar that reaches the sky; a deep toll, like the toll bell at Vonnra's tower |
| 5 | Storied | **Storied** | ember red `#ff6a3a` | A Named thing that has **a history with you**: given by the story, or grown (`§9`). Its rolls are lifted a grade. | fixed | as Named, lifted | the Named pillar, ringed in embers; the toll, then a breath of fire |

**Reading rules.**
- *Colour is rarity, shape is power.* The beam's height and the sound say how
  rare; a Mark, unique power or set bonus is a coloured block in the tooltip
  with its own heading, so the eye finds the power without reading numbers.
- *One glance from the ground.* A Named drop must be seen across the whole
  arena from the high camera (64° pitch, 31 m): a pillar that runs off the
  top of the screen, and a toll that cuts through a horde. Plain and Fine
  drops are quiet enough to ignore, and the loot filter (`§12`) can hide
  them completely.
- *Never "identify".* Every item reads in full the moment it drops (Diablo II
  and early Diablo III's scrolls of identify were pure friction).
- *Two-word names for Rares.* A Rare is named from two lists in the game's
  voice ("Cold Supper", "Low Water", "Gallows Kiss", "Patient Wall");
  Fine items keep the prefix-base-suffix name the code builds today
  ("Hale Chain Shirt of the Hearth"). Lists in `CATALOGUE.md` §5.

---

## 3. Slots and what each is for

Nine slots, unchanged: enough to dress a build, few enough to read at a glance
and to show on the figure. No gloves, boots, belts or quivers: every slot must
earn its place in the UI and on the body, and four of the nine change the
survivor's look (`VISUALS.md`).

| Slot | Kind | Its job | Implicit family | Shows on the figure |
|---|---|---|---|---|
| Weapon | Weapon | **The skill you fight with.** A weapon brings a combat skill at a rank, and an *Edge* (`§4.2`). | skill + rank + Edge | in hand |
| Off-hand | Off-hand, or a one-handed weapon | **A choice:** a second skill (totem, censer, tether, a second weapon) that takes an ember weapon slot, *or* a guard (shield, buckler, lantern, tome) that gives block, armour or an art bonus and leaves the slot free. | skill + rank, or block/armour | in the other hand, or on the forearm |
| Head | Head | Defence and the art (cooldown, power), light, crit. | armour, or a sense (light, crit) | helm, hood, cap, circlet, mask |
| Body | Body | The most defence; the most affixes of weight. | armour + health | material and pieces over the calling's outfit |
| Cloak | Cloak | Movement and the dash; what the weather and the people do to you. | speed, dash, tenacity | the cloak, dyed |
| Amulet | Amulet | Offence and attributes; the best home for a skill worn. | an attribute or a school | (small; a glint at the throat on close-ups) |
| Ring ×2 | Ring | Offence and the ember; the most flexible pool. | one small stat | – |
| Relic | Relic | **A trinket with a price** (Darkest Dungeon's trinkets, Titan Quest's charms): an odd, strong rule, often with a downside. Lanterns, lenses, lamps, bones, ledgers, coins. | a rule | carried at the hip (a lamp, by night, lit) |

The relic slot is where this game's character shows most. Plain relics are
rare; most relics are Named.

---

## 4. Bases

### 4.1 Tiers

Five base tiers, from what a traveller wears on the Low Ford road to what was
buried with the Seventh Legion. A base's tier sets its **implicit** (how much
it gives), its **notches** (`§10`), the **ilvl** it starts dropping at, and its
**look** (`VISUALS.md`). Higher tiers are not always better: a Tier II base can
carry better affixes than a Tier IV one if it dropped deeper.

| Tier | Name | Drops from ilvl | Made by, in the world | Material | Implicit (vs Tier I) | Notches (max) |
|---|---|---|---|---|---|---|
| I | **Worn** | 1 | anyone; a traveller's own | rags, homespun, rawhide, old iron | ×1.0 | 0–1 |
| II | **Sound** | 6 | the Watch's stores, Brannoc, Coyle wagons | leather, quilted linen, mail, good iron | ×1.6 | 1–2 |
| III | **Wrought** | 14 | Brannoc at his best; the Vigil's armourers | riveted mail, half-plate, oiled leather, blued steel | ×2.4 | 1–3 |
| IV | **Legion** | 22 | the old empire; dug from barrows and the Dig | bronze-and-iron plate, scale, red-lacquered leather, sigil-cut | ×3.3 | 2–3 |
| V | **Heartwrought** | 30 | nobody living: made down the stair, in the Morrow's light | pale bone-plate, ember-veined iron, chitin | ×4.4 | 2–4 |

Tier V appears only after the story's turn into Act 3 (or in the endgame
depths, `PROGRESSION.md`) and is the base for every top-end build. Every
Tier I–IV base has a Tier V counterpart, so a favourite base is never
abandoned (Diablo II's normal, exceptional and elite versions of one base;
the lesson is that a known silhouette made better is more exciting than a
new one).

### 4.2 Weapons: skill, rank and Edge

A weapon's implicit is three things:

1. **The skill** it brings (`ItemWeapon.Id`): the base decides it. A sword
   brings Oathblade, a cleaver the Butcher's Cleaver, a crossbow Volley. Every
   findable combat skill has a base family (table below), so any skill can be
   built around by day and brought into the night.
2. **The rank** it brings: Tier I–II bases rank 1, Tier III–IV rank 2,
   Tier V rank 3. A *Masterwork* affix adds one. **Gear may bring a skill in
   at rank 4 at most**: ranks 5 to 8, and the evolution, are the ember's
   alone. (The rule that keeps the arena a survivors game: the smith starts
   it, the ember finishes it.)
3. **Its Edge**: a *more* multiplier on the damage of every skill that shares
   the weapon's kind tag (Steel for blades and axes, Spell for wands, staves
   and rods, Thrown for knives, discs and chakrams, Ranged for crossbows and
   bows, Holy for censers, Nature for pouches and horns). Edge is the one
   sanctioned "more" on ordinary gear, and the lever that lets weapon damage
   keep pace with creature health as levels rise (`PROGRESSION.md` §2).

| Tier | Rank | Edge (more damage to its kind) |
|---|---|---|
| I Worn | 1 | +0% |
| II Sound | 1 | +25% |
| III Wrought | 2 | +60% |
| IV Legion | 2 | +110% |
| V Heartwrought | 3 | +180% |

The Edge goes into the arena with the weapon. That is deliberate: a Steel
weapon makes the ember's Steel cards stronger, so a warden with a Legion
blade is pulled toward a steel build (the draft already leans toward the
build's tags; the Edge makes following that lean worth it). A survivor who
drafts away from their weapon's kind gives up the Edge for whatever they
found. That is a real choice every night.

**Weapon families and the skills they bring** (the existing nine starting
items stay as the Tier I base of their family):

| Family | Hands | Skill (today's id) | Kind (Edge) | Attribute it favours | Calling at home |
|---|---|---|---|---|---|
| Sword | one | Oathblade (`oathblade`) | Steel | Might | warden |
| Disc / war-buckler | one, thrown | Judgement Disc (`judgement_disc`) | Thrown | Resolve | warden |
| Cleaver | one | Butcher's Cleaver (`cleaver`) | Steel | Might | reaver |
| Paired axes | both | Axe Gyre (`axe_gyre`) | Steel | Might | reaver |
| Scythe / great blade | both | Reaving Arc (`reaving_arc`) | Steel | Might | reaver |
| Wraps / knuckles | both | Iron Palms (`iron_palms`) | Steel | Might | reaver, warden |
| Wand | one | Seeking Motes (`seeking_motes`) | Spell | Wits | arcanist |
| Staff | both | Cinderfall (`cinderfall`) | Spell | Wits | arcanist |
| Rod | one | Rimeshard (`rimeshard`) | Spell | Wits | arcanist |
| Black wand | one | Umbral Bolt (`umbral_bolt`) | Spell | Wits | arcanist |
| Crossbow / bow | both | Volley (`volley`) | Ranged | Finesse | stalker |
| Knife belt | one | Knifestorm (`knifestorm`) | Thrown | Finesse | stalker |
| Chakram | one | Gale Chakram (`gale_chakram`) | Thrown | Finesse | stalker |
| **Off-hand skills** | | | | | |
| Storm totem | off | Arcweb (`arcweb`) | Spell | Wits | arcanist |
| Censer | off | Dawnpulse (`dawnpulse`) | Holy | Resolve | warden |
| Reliquary | off | Hallowed Ground (`hallowed_ring`) | Holy | Resolve | warden |
| Moon charm | off | Moonbrand (`moonbrand`) | Spell | Wits | arcanist, stalker |
| Tether (bone wand) | off | Grave Tether (`grave_tether`) | Spell | Wits | arcanist |
| Blight flask | off | Blightfield (`blightfield`) | Nature | Resolve | stalker |
| Seed pouch | off | Thornbloom (`thornbloom`) | Nature | Resolve | stalker, warden |
| Antler horn | off | Spirit Herd (`spirit_herd`) | Nature | Resolve | any |
| Green lens | off | Verdant Lance (`verdant_lance`) | Spell | Wits | arcanist |
| **Off-hand guards** (no skill) | | | | | |
| Shield, buckler | off | – (block, armour) | – | Might / Resolve | warden, reaver |
| Lantern | off | – (light, holy, vs the dead) | – | Resolve | any |
| Tome | off | – (art power, cooldown) | – | Wits | arcanist |
| Quiver / bandolier | off | – (projectiles, pierce) | – | Finesse | stalker |

Two-handed families leave the off-hand empty and carry a larger Edge (+25% on
the table's figure) to pay for it.

### 4.3 Armour: weight

Head, body, cloak and off-hand guards have a **weight**: cloth, leather, mail
or plate. Weight sets the implicit's mix and the look; it never forbids. A
heavy piece asks for Might (`§5.3`), and slows the wearer a little unless they
have it.

| Weight | Implicit (body, Tier I) | Speed | Favours | Reads as |
|---|---|---|---|---|
| Cloth | +1 armour, +6% art power | – | Wits | robes, quilting, hoods |
| Leather | +2 armour, +3% move speed | – | Finesse | jerkins, brigandine, hides |
| Mail | +4 armour, +10 health | −2% | Resolve | rings, scale |
| Plate | +6 armour | −5% | Might | plates, pauldrons, greaves |

Scale the armour by the tier's multiplier (Plate Tier V body: +26 armour).
At 20 armour the survivor turns half of each blow (`armor / (armor + 20)`);
the full plate warden at Tier V with armour affixes reaches about 60, three
quarters. That is the ceiling: the formula caps itself gently and must not be
pushed past ~80% by gear alone.

Full base lists, by slot and tier, are in `CATALOGUE.md` §2.

---

## 5. The stat model

### 5.1 How a number is made (unchanged)

`value = (base + Σ flat) × (1 + Σ increased) × Π (1 + more)` (`Sim/Stats.cs`).
The item system's rule for which layer gear may use:

| Layer | Who may use it | Why |
|---|---|---|
| Flat | implicits, affixes, uniques, sets | health, armour, crit points, attributes, resistances |
| Increased | affixes, Marks, uniques, sets | **gear's damage bonuses are "increased"**, so they add with the ember's passives (Might, Precision) instead of multiplying them. As the ember build grows, gear's share of the night's power falls on its own. This is the single most important balancing property of the system. |
| More | weapon Edge; at most **one** more per Mark, unique or set bonus | A few multipliers, each one visible, named and chosen. Diablo III's set bonuses (+1,000% and up, multiplied together) and Diablo IV's launch "x" affixes are what this rule exists to prevent. |

A test (`IMPLEMENTATION.md` §5) counts the "more" sources a full kit can carry
and fails above six.

### 5.2 The stat keys gear can touch

All exist in `Stat` today unless marked *new*.

- **Defence:** `maxHealth`, `armor`, `regen`, `healing`, `lifesteal`,
  `block`, `dodge`, `resist.<school>` (8), `from.<family>` (10), `tenacity`,
  `thorns`.
- **Offence:** `damage`, `damage.<school>` (8), `damage.<tag>` (20: projectile,
  melee, area, summon, dot...), `critChance`, `critDamage`, `cooldown`,
  `area`, `projectiles`, `projectileSpeed`, `pierce`, `duration`,
  `statusChance`, `statusDamage`, `summonDamage`, `summonHaste`,
  `executeThreshold`, `knockback`, `vs.<family>` (10).
- **The art and movement:** `abilityCooldown`, `abilityPower`, `dashCharges`,
  `dashCooldown`, `moveSpeed`.
- **The ember and the night:** `xpGain` (ember gained), `luck` (rarer cards in
  the draft), `pickupRadius`, `lightRadius`, `goldGain`; *new*:
  `emberStart` (ember levels at the arena's start, today a trait tag
  `ember_start`), `draftCards` (cards per draft), `rerolls`, `banishes`
  (today kit fields), `greatChoices` (great-blessing cards offered).
- **Attributes** (*new as mod keys*): `might`, `finesse`, `wits`, `resolve`.
  Today attributes are character fields only; gear that raises them must feed
  both the attribute bonuses in `Character.Kit` and the skill requirement in
  `SkillBook.Meets` (a +2 Wits ring can let a warden carry a spell by day).

### 5.3 Attribute affinity, not requirements

No item is forbidden to anyone (`Callings`: anyone can do anything in the
ember; the same goes for gear). Instead every base names an attribute it
**favours** and an amount: 6 for Tier I–II, 10 for Tier III, 14 for Tier IV,
18 for Tier V. A survivor who measures up gets the full implicit; one who does
not gets **half** of it (and a heavy piece slows them a further 5%). The
tooltip says it in one line, in red when unmet: "Asks 14 Might (you have 11):
half its armour."

This keeps a calling's own gear best in its hands, keeps attribute points
interesting at every level-up, and never leaves a dropped item useless to the
survivor who found it.

---

## 6. Affixes

### 6.1 Rules

- **Prefixes** are power (damage, defence, the weapon); **suffixes** are
  everything else (resistances, speed, the art, the ember, the world). At most
  **two of each**, four in all.
- Each affix belongs to a **group**; an item holds one affix per group
  (no "Hale" twice). Groups are listed in `CATALOGUE.md` §3.
- Each affix lists the **slots** it can roll on and a **weight** per slot.
  Slots matter: crit on rings and heads, armour on body and off-hands, the
  ember on rings and relics, the dash on cloaks.
- **Grade** I–VI, gated by item level. A seventh, **bright** grade (`§6.3`)
  only drops deep.
- **Roll** within a grade's range, shown on demand (hold Alt: "+46 health
  [41–48], grade V").
- What the map leans toward (`MapOffers.Lean`) stays: affixes that answer the
  map's oaths and people are four times as likely, as now.
- Day and night: **every affix works in both halves** except the *kindled*
  family (`§6.4`), which only has anything to act on where the ember burns,
  and says so: "In the ember: ...".

### 6.2 Grades and item level

| Grade | Name in the tooltip (Alt) | Rolls from ilvl | Value (× grade I) |
|---|---|---|---|
| I | Rough | 1 | ×1.0 |
| II | Plain | 5 | ×1.5 |
| III | Good | 10 | ×2.1 |
| IV | Fine | 16 | ×2.8 |
| V | Rare | 22 | ×3.6 |
| VI | Masterful | 28 | ×4.5 |
| VII | **Bright** ✶ | 34 | ×4.5 to ×5.6 (VI's top, and up to a quarter past it) |

An item rolls each affix's grade from the grades its ilvl allows, weighted
toward the top two: 40% the highest allowed, 30% the next, 30% spread below.
So a deeper item is usually but not always better, and a perfect high roll
stays rare.

**Item level** is the level of whatever dropped it, or the arena tier's level
(`ACQUISITION.md` §2), capped at 40. It is shown on the tooltip ("ilvl 22") and
decides the base tiers and affix grades that can roll. Character level does
not limit what can be worn; base affinity (`§5.3`) does the work a level
requirement would.

### 6.3 Bright affixes

A bright affix (Diablo IV's greater affix, Last Epoch's exalted tier) is grade
VII: the top of grade VI's range, and up to 25% beyond it, marked with an
ember star ✶. They roll only at ilvl 34+ (Tier 10 arenas and the depths): 1 in
12 affixes on a Rare, 1 in 8 on a Marked item, and Named items roll each of
their ranges bright 1 time in 10. Two bright affixes on one item is an event
worth a sound of its own. They are the long tail of the chase (`PROGRESSION.md`
§6), not the thing a build needs.

### 6.4 Kindled affixes: gear that talks to the ember

A small family of suffixes, Rare and up, at most **one per item** and **two
per survivor's kit** counted (a third does nothing, and the tooltip says so).
They are how gear shapes a night without out-shining it:

| Kindled affix | In the ember | Cap (whole kit) |
|---|---|---|
| of the First Spark | The arena begins with +1 ember level (+2 at grade VI). | 3 levels |
| of Second Thoughts | +1 reroll in drafts. | +3 |
| of Refusal | +1 banish. | +2 |
| of Many Roads | Drafts show a fourth card. | 4 cards (the existing "four, with the right gear") |
| of Omens | Great blessings offer a fourth choice. | 4 |
| of the Calling | Cards of your calling's favoured tags come 25% more often (today 35% more; this adds). | – |
| of the Whetstone, of Rime, of the Pyre... (one per evolving passive) | **Counts as one rank of that passive for evolutions.** A rank-8 weapon can evolve without the passive being drafted. | one per passive |
| of the Long Night | +X% damage after the fifteenth minute. | – |

The catalyst suffixes (`of the Whetstone`: counts as Serration; `of Rime`:
Chilling Presence; `of the Pyre`: Searing Aura; `of Brambles`: Thorns;
`of the Wide Field`: Expanse; `of the Feint`: Evasion) are the bridge between
the two halves (Vampire Survivors' evolutions want a passive; here a piece of
gear can stand in for it). They are tuned so a survivor who plans for an
evolution by day reaches it a little sooner by night, never skips the rank-8
climb.

### 6.5 Skills worn

The five existing `Grants` suffixes stay, generalised: any findable combat
skill can be worn from an amulet, ring or relic, on Rare and up, at rank
1 + (grade − 1) / 2, capped by the same rank-4 rule. A worn skill takes an
ember weapon slot like any other gear skill. The weight stays low (×0.35):
finding the skill you want worn is a good day.

The full list of about sixty affixes, with groups, slots, weights and ranges
by grade, is `CATALOGUE.md` §3.

---

## 7. Marks: the power layer of Marked items

A **Mark** is a power burned into an item by the dark it came out of: a rule,
not a number. "Oathblade's swings throw a crescent every third swing."
"Your dash leaves a ring of cold." "Blink leaves an image that casts your last
spell." It is Diablo IV's aspect and Diablo III's legendary power, given to
blue items with three affixes rather than to every orange.

- **Where:** Marked items (rarity 3) carry exactly one; Named items never.
- **Pools:** each Mark belongs to a skill school, a skill, an art, or a calling
  theme, and has slots it can burn into (offence Marks on weapons, amulets and
  rings; defence Marks on body, head and cloak; art Marks on head and relic).
- **Range:** every Mark has one rolled number (its strength), graded by ilvl
  like an affix.
- **Night and day:** most Marks act in both halves. Those that speak of the
  ember ("each blessing you take...") act only where it burns.
- **The binders' book.** Vonnra can lift a Mark off an item into her book (the
  item is destroyed) and later press it into another Rare of a fitting slot
  (`CRAFTING.md` §5). The book keeps the **best strength** of each Mark it has
  been given (Diablo IV's codex after Loot Reborn: collection as progress).
  The first time a Mark is seen, it is written into the book at its lowest
  strength anyway, so a survivor who has seen a Mark can always use it.
- About thirty Marks, by school and calling, are in `CATALOGUE.md` §4.

Marks are the layer that makes builds by day: they hit the survivor's few
day skills and the art in hand, and they keep working when the ember draws
new weapons, because most are written against tags ("your Steel skills") or
the art, not one weapon.

---

## 8. Named items (uniques)

Authored items with a power that can make a build. Today's rule holds: **named
things never roll affixes**. They roll **ranges**: every number on a Named item
has a range, so a second copy can be better (and is worth picking up).

**What makes a good Named item here:**
1. **It changes how you play,** not only how hard you hit. "Your dash is
   gone; your art has two charges" beats "+40% damage".
2. **It speaks to the world.** About a third carry a world tag (the Pack lets
   you pass, the Watch takes you for a deserter, Chid will know what it is).
3. **It has a price,** said plainly in the downside line, for about half of
   them.
4. **It has a home:** a people, a boss, a story fight, a person (`ACQUISITION.md`
   §4), so it can be hunted.
5. **It has a line of lore** in the narrator's or a person's voice, and that
   line respects `STORY_BIBLE.md`: it never says an act's answer before the act
   (Chid's items do not say what he is in Act 1). `CATALOGUE.md` marks the act
   each lore line is safe from.
6. **No dead uniques.** A Named item that names a blessing or a skill must be
   good without it ("if you take Kindling..." items also give something on
   their own).

Two classes of Named:
- **Uniques**: one-off, build-defining. About thirty to begin
  (`CATALOGUE.md` §6).
- **Set pieces**: `§9`.

---

## 9. Sets

Sets here are **small and loose**: three or four pieces, bonuses at 2, 3 and
4, and never more than one "more" in the whole set. Each set is a people's or an
order's gear, in its colours, and each looks like a set on the figure
(`VISUALS.md` §5).

Lessons from the genre (`VISION.md`): Diablo III's six-piece sets with
thousand-percent bonuses made one build per class and turned every other item
into a rounding error; Diablo II's sets were mostly weaker than rares and
therefore ignored past the early game; Grim Dawn's and Last Epoch's smaller
sets that mix with uniques worked. So:

- **Four calling sets** (four pieces each: one per calling, built around its
  starting skills and arts), strongest at 4 but always leaving five slots for
  uniques, Marked items and rares.
- **Five people's and orders' sets** (three pieces each), cross-calling,
  built around a school or a way of fighting.
- **One teaching set** (the Watch's kit, three pieces), which drops early, is
  cheap, and teaches what a set is in Act 1.
- **One Legion set** (four pieces, Act 3 and the depths), the endgame set.
- **Set pieces may be rerolled within range** like any Named item, and a
  **ring of the Seventh** (a unique ring) makes a set count one piece more,
  so a 3-piece set can be finished in two pieces (Diablo III's Ring of Royal
  Grandeur; the most loved item in that game because it **freed** a slot).

The ten sets and their bonuses are `CATALOGUE.md` §7.

### Storied items

A Named item becomes **Storied** (rarity 5) when it has three lines of history
with the survivor. History is written by the world, never bought:

- won a story fight with it worn;
- taken it back from a nemesis (`BETA_DESIGN.md`, "Death is content": the thing
  that killed you carries one item; taking it back writes "Taken back from
  Ash-Fang, who took your light");
- slain an arena's boss beyond the half hour with it;
- had it named by a person (Brannoc can put a name to a blade he reworked;
  Maeca names a bow; Chid blesses a lantern), at most once per item.

A Storied item's every range is lifted one grade (its roll reread against the
next grade's range; the bright chance doubles), its name is written in ember,
and its history shows in the tooltip, one line a deed. This is Diablo III's
Primal and Ancient, earned instead of rolled, and the **History** field the
save already has.

---

## 10. Notches and sigils (sockets and runes)

The Seventh Legion cut its sigils into everything it made: seven notches on
the vault door, one for each link. Gear can carry **notches** (sockets), and
**sigil-stones** (runes) go into them.

- **Notches:** by base tier (`§4.1`) and slot: weapons, off-hands, heads and
  bodies only. Plain and Fine items roll more notches than Rares (Diablo II's
  bargain: a white base for a runeword, a blue item for its affixes). Brannoc
  can cut one more, once, at a cost in heat (`CRAFTING.md` §3).
- **Sigil-stones:** twelve, from common to very rare. Each gives a small bonus
  that depends on the slot (a weapon, armour, or a helm), like Diablo II's
  runes. Three of a kind become one of the next at Vonnra's.
- **Watchwords:** sigils set in a particular order in a Plain or Fine item with
  exactly that many notches make a **Watchword** (Diablo II's runewords):
  the item turns Named, takes the Watchword's name, and gains its power. A
  Watchword is a recipe the survivor must find (written on walls, in the
  Vault, in Keegan's handbook, in the dead watchman's book), which makes
  each find a piece of the world's lore as well as a build.
- About twelve sigils and twelve Watchwords are in `CATALOGUE.md` §8. They are
  phase four (`IMPLEMENTATION.md`): good, but last.

---

## 11. Synergies

### 11.1 With the callings

No gear is locked to a calling; every base favours an attribute, and each
calling starts strong in two (`Callings.StartAttributes`: the warden Might
and Resolve, the reaver Might, the arcanist Wits, the stalker Finesse).

| Calling | Weapon families at home | Armour weight | Its set | Its Marks lean to |
|---|---|---|---|---|
| Warden | sword, disc, censer, reliquary, shield | plate, mail | **The Argent Vigil** (4) | holy, block, Shield Bash, Bulwark, the dead |
| Reaver | cleaver, paired axes, scythe, wraps | leather, hides, bare (a reaver's "body armour" is war-paint, fur and straps) | **The Barefoot Garrison** (4) | bleed, orbit, Crashing Leap, War Cry, low health |
| Arcanist | wand, staff, rod, black wand, totem, tether, tome | cloth | **Ash-of-Morrow** (4) (the binders' line) | fire, frost, storm, arcane, Blink, Time Slip |
| Stalker | crossbow, knife belt, chakram, flask, pouch, quiver | leather | **The Red Hand** (4) (the Kerchiefs) | projectiles, marks, poison, Mark Prey, Smoke Bomb |

A calling's set reads its starting arts and weapons, but every set bonus is
written against tags ("your Steel skills", "your art"), so a set still works
after the ember has drafted the survivor into something else.

### 11.2 With the skill schools

The schools (`School`: physical, fire, frost, storm, nature, arcane, holy,
shadow) each get, across the catalogue: a damage prefix, a resistance suffix,
at least three Marks, two uniques, and a people or order whose gear leans to
it. The statuses the gear applies (`ItemDef.Statuses`) feed the ember draft
(`LevelUp.BuildStatuses`), so a burning weapon brings burn-hungry cards: keep
that, and give every school's gear one status to bring.

### 11.3 With the blessings

Great blessings are chosen at the arena's start and at minute fifteen, from
all of them; milestone blessings come later. Gear touches blessings in three
ways only:
1. **Omens** (kindled affix): one more great-blessing card.
2. **Answers** (about eight Named items): "If you hold Kindling, ...", each
   good on its own as well (`§8` rule 6).
3. **Leans** (Marks and set bonuses with blessing tags): a set built round
   summons makes summon blessings likelier, by tag, through the existing
   affinity.

Gear never *grants* a blessing. Blessings are the ember's milestones, and the
night must stay the night's.

### 11.4 With the oaths and the people

Already the best idea in the loot: a map's gear leans toward what answers it
(`OathDef.Lean`, `Denizens.Lean`). Keep it, and widen it:
- each oath also raises one of: ilvl (+2 for Deep Dark), the Marked chance
  (Champions), the Named chance (Iron, Moonless), notches (Long Vigil),
  sigil drops (Ruin), or set pieces (Swarm) (`ACQUISITION.md` §3);
- each people has signature bases and Named items (`ACQUISITION.md` §4), so
  "run the dead for the Barrow Lord's helm" is a plan a player can make.

### 11.5 With the ember build

Summarised from above, because it is the heart of the design:

| Gear brings into the night | Limit |
|---|---|
| Its stats (increased bonuses add with the ember's) | Inc, not More (`§5.1`) |
| The weapon's and off-hand's skills, and worn skills | rank 4 at most; each takes an ember weapon slot |
| The weapon's Edge (more damage to its kind) | one Edge |
| Statuses that steer the draft | – |
| Kindled affixes (first spark, rerolls, fourth card, catalysts) | one per item, two per kit, caps per effect |
| Marks and Named powers | written against tags and arts, so they keep working as the build changes |

**What gear never brings:** ember levels past the cap, a blessing, an
evolution, a rank past 4. The night's build is the night's.

---

## 12. Inventory, filter and the pack

Inventory tedium is the most common complaint in the genre, and this game has
a 24-slot pack. Rules:

- **Spoils, not pick-ups, in the arena.** Gear dropped in an arena is gathered
  into the run's **spoils** (Hades' end-of-run reward, Last Epoch's loot
  summary); the survivor walks over it to claim it but it takes no pack space
  until the arena ends, when the spoils screen shows everything with salvage
  and keep buttons. No town trips mid-run, ever.
- **Materials take no slots.** They go to a materials pouch (stacks of any
  size), viewable from the pack.
- **A loot filter** from day one, simple and in the game's words: show Plain
  never / for my calling / always; Fine likewise; highlight affixes; hide
  bases below tier N; always show Named, sets, sigils, Marked. Hidden items are
  auto-salvaged into the pouch at the end of the arena (with a setting to turn
  that off). An advanced editor later (`IMPLEMENTATION.md` §4).
- **Stash tabs** at the Last Lamp (Mother Rook's), bought with gold (a sink),
  with a tab for sets and one for sigils.
- **Compare** (exists) grows to every stat a slot can roll and shows the delta
  in the arena's terms too ("+12% Steel damage in the ember").
