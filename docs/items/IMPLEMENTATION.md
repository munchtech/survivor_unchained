# Implementation: a phased build plan

How to build the item system in this codebase, phase by phase, with the
schemas, the migration from today's `items.json`, the UI it needs, the tests
to write, and what to build first for the most impact. Mapped to the files as
they are on `claude/vigilant-galileo-l6jqyx` today.

The order is chosen so that **every phase ships a better game on its own**,
and the riskiest balance questions (gear against the ember) are measured
before content is poured in.

---

## 0. Where things live now

| Concern | File |
|---|---|
| Item definitions, affixes, slots | `godot/logic/Rpg/Items.cs`, `godot/data/content/items.json` |
| Instances, rolling, pack, equip, kit | `godot/logic/Rpg/Character.cs` (`ItemInstance`, `AffixRoll`, `Inventory.Make`, `Character.Kit`, `Character.Compare`) |
| Skill requirements | `godot/logic/Rpg/SkillBook.cs` (`Need = 6`, `Meets`) |
| Stats | `godot/logic/Sim/Stats.cs` (`Stat`, `StatMod`, `ModKind`, `ArmorReduction`) |
| Triggers | `godot/logic/Sim/Procs.cs` (`TriggerDef`, `Effect`) |
| Kit into a battle | `godot/logic/Play/Journey.cs` (`StartBattle`, `RefreshKit`, `Douse`) |
| Ember draft | `godot/logic/Sim/LevelUp.cs` (`BuildStatuses`, affinity, `MaxWeapons`) |
| Arena drops | `godot/logic/Play/Zones/ArenaRun.cs` (`PlainGear`, `Rarity`, `OnLoot`) |
| Day drops | `godot/logic/Play/Zones/Verge.cs` (`PlainGear`, `OnLoot`) |
| Oaths and peoples | `godot/logic/Maps/MapOffers.cs` (`OathDef.Gear`, `Lean`, `Denizens.Lean`) |
| Shops | `godot/data/content/shops.json`, `Journey` (stock) |
| Stash | `godot/logic/World/State.cs` (`Stash`, 48) |
| Saves | `godot/logic/World/Save.cs` (versioned, migrated on load) |
| How the survivor looks | `godot/logic/Play/Loadout.cs`, `godot/src/Actors/People.cs`, `godot/src/Actors/Arms.cs` |
| Item UI | `godot/src/Ui/ItemViews.cs` (cards, compare), `Pack.cs`, `Style.cs` (rarity colours) |
| Item pictures | `godot/src/Ui/ItemModels.cs`, `ItemPhotos.cs` |
| Loot on the ground | `godot/src/Fx/BattleFx.cs` (loot beams) |
| Content checks | `godot/tests/ContentTests.cs`, `StoryLint.cs` |

---

## Phase 1: the foundation (data, rolls, item level)

**Goal:** the affix system becomes data with grades, ranges and item level;
every weapon and armour base rolls; drops come from people tables. No new
UI beyond the tooltip showing what is new. Ships: drops that differ from one
another, and a reason to go deeper.

### 1.1 Schemas

Split `items.json` into four files (same loader, `Json.ReadContent`):

```jsonc
// data/content/bases.json : every base, by family and tier
{ "bases": {
  "watch_hauberk": { "name": "Watch Hauberk", "kind": "body", "family": "body_mail", "tier": 2,
    "weight": "mail", "favours": "Resolve", "notches": [1, 2], "icon": "body_mail_1",
    "implicit": [ { "stat": "armor", "kind": "flat", "value": 4 }, { "stat": "maxHealth", "kind": "flat", "value": 10 } ],
    "look": { "pieces": ["pauldron"], "material": 1 } },
  "watch_sword": { "name": "Watch Sword", "kind": "weapon", "family": "sword", "tier": 2, "hands": 1,
    "favours": "Might", "weapon": { "id": "oathblade", "rank": 1 }, "edge": { "tag": "steel", "more": 0.25 },
    "notches": [1, 2], "icon": "sword_1", "held": "chevalier_sword" } } }

// data/content/affixes.json : moved out of Items.cs
{ "grades": { "mult": [1.0, 1.5, 2.1, 2.8, 3.6, 4.5], "ilvl": [1, 5, 10, 16, 22, 28], "bright": { "ilvl": 34, "max": 1.25 } },
  "affixes": {
    "hale": { "name": "Hale", "prefix": true, "group": "health",
      "slots": { "body": 1, "amulet": 1, "ring": 1, "head": 1, "cloak": 0.6 },
      "mods": [ { "stat": "maxHealth", "kind": "flat", "base": [12, 14] } ],
      "text": "+{0} health" },
    "of_the_whetstone": { "name": "of the Whetstone", "prefix": false, "group": "catalyst", "kindled": true,
      "minGrade": 3, "slots": { "weapon": 1, "ring": 1, "amulet": 1 }, "catalyst": "serration",
      "text": "In the ember: counts as Serration for evolutions" } } }

// data/content/items.json : Named, set pieces, story items, materials, consumables (as now)
//   Named gain "base": "<base id>", "ranges" on their mods, "safeFrom": 1|2|3, "home": {...}
// data/content/sets.json : sets, their pieces and bonuses (2/3/4)
```

Affixes stay data; the few effects data cannot say (catalysts, kindled caps,
Marks' rules) are named hooks the code implements, like `TriggerDef` today.

### 1.2 Instances

`ItemInstance` gains `Ilvl`, `Heat`, `Notches`, `Sigils`, `Mark`, `Flags`,
`Look`; `AffixRoll` gains `Grade`, `Roll` (0–1) and `Bright`. `Name` and
`History` exist. A Named item's ranges roll into `Rolls: double[]` (one per
ranged number).

### 1.3 Migration

`SaveData.Version` → 2. `Saves` migrates on load (it already migrates and never
discards):
- `AffixRoll.Tier t` → `Grade t + 1`, `Roll 0.5`.
- Every item gets `Ilvl = max(1, 3 × rarity + 2)` (a fair guess) and heat by
  rarity.
- Today's nine plain bases map to their Tier I or II base ids (the ids stay
  the same: `leather_cap` is a base, `silver_ring` Tier II).
- Named items without rolls take the middle of each range.
- The removed C# affixes keep their ids, so nothing in a save points nowhere.

### 1.4 Code

- `Items.Load`: read the four files; build `Bases`, `Affixes`, `Sets`.
  `Items.Affixes` becomes data-backed (keep its shape for callers).
- `Inventory.Make(ch, defId, ilvl, rarity, seed, lean)`: grades from ilvl,
  rolls within range, group exclusivity, two prefixes and two suffixes at most,
  four affixes at most (Rare 3–4, Fine 1–2), weights per slot, the lean ×4
  (kept), bright at ilvl 34+.
- `Inventory.Mods`: implicit (halved when the base's affinity is unmet:
  needs `Attributes` passed in) + affixes by grade and roll + Named ranges.
- `Character.Kit`: attributes from gear (`might`, `finesse`, `wits`,
  `resolve` mod keys) fold into the attribute bonuses and **into
  `SkillBook.Meets`** (pass the kit's attribute totals, not only
  `ch.Attributes`); the Edge (a "more" on `damage.<tag>`); the rank-4 cap on
  gear skills; kindled affixes counted and capped.
- `ArenaRun.OnLoot`, `Verge.OnLoot`: replace `PlainGear` with a `Drops` module
  (`logic/Rpg/Drops.cs`): people tables, rarity table, base by ilvl and tier
  band, calling lean. ilvl from tier (`3 × tier + 2`, heralds, boss).
- `of_haste`: from `ModKind.More` to `ModKind.Inc` (`SYSTEM.md` §5.1).

### 1.5 Tests (xUnit, `godot/tests/ItemTests.cs`, new)

- **Rolling is deterministic** by seed; **group exclusivity** holds; **no item
  exceeds 2 prefixes, 2 suffixes, 4 affixes**; grades never exceed what ilvl
  allows; rolls within range.
- **Budget bands**: a thousand Rares per band, their point value (`PROGRESSION.md`
  §2.4) within ±20% of the band's target.
- **Migration**: a version-1 save (fixture) loads into version 2 with every
  item intact and its mods within 10% of before.
- **Kit**: a +2 Wits ring lets a Wits-4 warden carry a spell (`SkillBook.Meets`);
  an unmet affinity halves the implicit; Edge applies only to its tag; a gear
  skill never enters at rank above 4.
- **More-count**: no legal kit carries more than six "more" sources.
- `ContentTests`: every base's skill exists; every affix's slots are real;
  every Named item's `base` exists.

## Phase 2: reading and handling (UI, filter, spoils, beams)

**Goal:** the loot is readable, findable and never a chore. Ships: the feel of
a modern ARPG's loot. Can run in parallel with phase 1's back half.

- **Tooltip** (`ItemViews`): the five layers (`SYSTEM.md` §1): name and
  rarity, base, tier and ilvl; implicit; affixes; power block (Mark, Named, set
  with pieces worn lit); notches, heat, history, world tags, downside, lore.
  Alt shows grades and ranges ("[41–48], grade V"). Bright affixes with ✶.
  Unmet affinity in red, in one line.
- **Compare**: `Character.Compare`'s `CompareKeys` grows to every stat a slot
  can roll; `StatNames` likewise; deltas grouped (offence, defence, the art,
  the ember); a second line "in the ember" for Edge and kindled changes.
- **Rarity presentation**: rename `raritynames` to Plain, Fine, Rare, Marked,
  Named, Storied; beams by rarity (`BattleFx`, `VISUALS.md` §9); sounds per
  rarity (`Audio/`; the Named toll is the one to get right); set pieces' argent
  motes; the bright star.
- **Spoils** (`ArenaRun`, `ArenaResult.cs`): items picked up in an arena go to
  the run's spoils, not the pack; the result screen shows them, Named last,
  with keep and salvage.
- **Loot filter** (`Pack.cs`, a settings panel): per rarity show/hide; "for my
  calling"; tier floor; highlight affixes; hidden items auto-salvaged into the
  pouch at the arena's end (setting). Later: rules editor, import/export.
- **Materials pouch**: materials and sigils out of pack slots.
- **Stash tabs** at the Last Lamp: tabs bought with gold; a sets tab.
- **Salvage** everywhere safe and from spoils (needs phase 3's materials; until
  then, sell value).

Tests: a filter round-trips through the save; spoils move to pack and pouch
correctly when the pack is full (overflow to the stash, then refused with a
message, never lost).

## Phase 3: crafting and the first powers (Brannoc, Marks, Named)

**Goal:** the survivor can work on gear, and the power layer above Rare
exists. Ships: the long middle of the game.

- **Materials** (`CRAFTING.md` §1) as item defs; salvage yields.
- **Heat** and **Brannoc's forge** (temper, hone, reforge, add, rework,
  notch, commission): a crafting panel at the smithy, every action showing cost,
  heat range and outcome range before the click. Story gate: `nell.told` = lie
  moves the service to Snib (Act 2 content).
- **Marks**: about thirty (`CATALOGUE.md` §4) as `TriggerDef`s and named rule
  hooks in `Battle`/`Arts` (most are triggers on dash, art, crit, kill or a
  status already supported by `TriggerEvent`; a few need new hooks: a third
  swing, Blink's image). Marked rarity drops from ilvl 12.
- **The binders' book**: per-save record of Marks seen and their best strength;
  lift and press at Vonnra's.
- **Named items**: the thirty-two (`CATALOGUE.md` §6), with homes and
  `safeFrom`; existing story Named items get ranges.
- **The Wayfinder's tally** (Named pity), visible on the table.
- **Wenna's tinctures**; **Chid's consecration**.

Tests: crafting never destroys an item; heat never goes negative; every craft
shown to the player is the craft performed (`preview == result` for
deterministic crafts); every Named item is obtainable (a `LootLint`, like
`StoryLint`: each `home` names a people, boss, place or fact that exists, and
each fact-gated item's fact can be set); no Named item is seen before its
`safeFrom` act (search shops, people tables and story rewards against the act
gates); the tally guarantees a Named on the fifth.

## Phase 4: sets, Storied, sigils, slurry, looks

**Goal:** the endgame layers and the figure. Ships: the chase.

- **Sets** (`sets.json`, `CATALOGUE.md` §7): the bonus engine (count pieces
  worn, the Ring of the Seventh's +1), tooltip with pieces lit.
- **Storied**: history lines written by world events (story fight won, nemesis
  taken back, boss beyond the half hour, named by a person); the lift at three.
- **Notches, sigil-stones, Watchwords**; recipes in the journal as they are
  found.
- **Slurry** (Snib) and **cleanse** (Chid).
- **The tailor** (Rav): glamour and dyes.
- **Echoes and the Depths** at the table; **Vonnra's weekly fortune**.

## Phase 5: the figure follows the gear (parallel from phase 1)

Visual work can start as soon as bases carry a `look` (phase 1), in the order
of `VISUALS.md` §10:
1. `material_tier` in `person.gdshader`, and piece lists per base (`look`
   field) read by `Loadouts.Of` into `PersonSpec` (today the outfit is chosen
   by calling only: add the body, head and cloak items' looks).
2. Her outfit pieces shown by tier (`People.HerOutfit` gains a piece filter).
3. KayKit helmets, hats, capes and shields as attachments.
4. `Loadouts.Held` for every weapon family and tier band (`Arms.cs` has the
   models).
5. Night glow on Heartwrought and Storied gear, from the ember level.
6. Icon keys per family and tier band (`ItemModels`), `ItemPhotos.Version` bump.
7. Heartwrought modelling (Act 3).

Tests (`LoadoutTests.cs` exists): every base's `look` names pieces that exist;
every weapon family maps to a held model; every icon key has a model.

---

## What to build first, for the most impact

If only five things land before the release candidate, land these:

1. **Grades, ranges and item level** (phase 1.1–1.4). Without them no two drops
   differ and depth means nothing. It is mostly a data move and a rewrite of
   `Inventory.Make`.
2. **Weapon bases that roll, with tiers and the Edge.** The weapon is the
   game's most important item and today it never changes after creation.
3. **Drops by people and ilvl, and the spoils screen.** The arena is where gear
   comes from; this makes every map a choice and every run end with a reward
   moment.
4. **The tooltip, compare, beams and sounds, and a simple filter** (phase 2).
   Presentation is half the reward, and the Named toll bell alone changes how
   the arena feels.
5. **The figure follows body, head and cloak** with the material-tier shader and
   her outfit pieces (phase 5.1–5.2). The cheapest big visual win in this plan:
   the survivor visibly gets better as they play.

Then Marks and Named items (phase 3), because they make builds; then sets and
the rest.

## Questions for the owner

Decisions this plan cannot make alone:
- **Level cap 30?** (`PROGRESSION.md` §1). The code has none.
- **Gear skills into the arena at up to rank 4**, and **the Edge**: both change
  the arena's balance; the balance lab should test them before content relies
  on them (`PROGRESSION.md` §5.3).
- **The woman survivor's armour by tier** is mostly showing more of her
  existing outfit pieces; the owner should say how her look should change with
  heavier gear before any new pieces are modelled.
- **Smart loot strength** (40% toward the calling's attribute): softer or
  stronger.
- **The Depths and echoes**: whether the game wants an endless endgame at all,
  or ends with the story and an epilogue (`STORY_BIBLE.md` §8).
