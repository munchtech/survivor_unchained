# Crafting: the research

How the best games make things, and why each works or fails, gathered for
Survivor Unchained's crafting (`CRAFTING_DESIGN.md` builds on it and cites
its lessons as C1 to C30). Itemization in general (drops, rarity, sets, the
chase, loot fatigue) is in `docs/items/RESEARCH.md`; this file is about
**making**: gathering, recipes, upgrading, affix crafting, the people who do
it, and its economy.

**Method.** Developers' own words first (manifestos, patch notes, official
previews, "Ask the Developer"), then the community wikis for the mechanics'
numbers, then critics for how players received it. Every game is read
against the same six questions:

1. **The loop**: gather, craft, use, want more. Where does it close?
2. **Agency**: what the player chooses, and when.
3. **Determinism or gamble**: what is certain, what is luck, and whether the
   player can see the odds.
4. **Economy**: the faucets (where materials and money come from) and the
   sinks (where they go), and what stops inflation.
5. **Progression and story**: how making ties to getting stronger and to the
   world.
6. **Failures**: chores, inventory bloat, "craft the best item and done",
   and anything else it shows us to avoid.

Each entry ends with **For us**: what this game teaches Survivor
Unchained, a survivors-like by night and a story-rich ARPG by day.

Sources are linked in each entry and gathered at the end.

---

## Part 1: The games

### 1. Path of Exile 1 (Grinding Gear Games, 2013 and on)

- **Loop.** Currency drops (orbs) are both money and crafting tools. A base
  drops; the player rolls it with orbs (Transmutation, Alteration, Regal,
  Chaos, Exalted), uses it, and the pursuit of the next tier of mods sends them
  back to the maps for more currency. Side systems layer on: the crafting
  bench (a chosen mod for a price, recipes found in the world), essences (one
  guaranteed mod), fossils (weighted mod pools), Harvest, beasts, and more.
- **Agency.** Enormous at the top: "metacrafting" chains bench locks,
  fossils and essences into a plan. Near zero at the bottom: a new player
  slams Chaos Orbs and hopes.
- **Determinism.** Mostly gamble, by design, with deterministic finishing
  steps (the bench adds one chosen mod; "can have up to 3 crafted modifiers"
  is a rare unlock). The odds are hidden; players use external calculators.
- **Economy.** The currency is the trade economy: every orb is spent as money
  or as a craft, so crafting is the game's main sink. Trade sets the value of
  everything, so self-found players are effectively balanced against a
  market.
- **Progression and story.** Bench recipes are found in specific areas
  (discovery tied to places). Otherwise crafting is outside the story.
- **Failures.** The **Harvest** episode is the genre's clearest lesson on
  determinism. Harvest let players add, remove and reforge mods of a chosen
  kind. Chris Wilson's manifesto removed most of it because it made "near-perfect
  items" easy and every other system pointless: he asked why anyone would use
  an ordinary Exalted Orb when Harvest gave "a deterministic result", and said
  the team did not want to lose "the feeling of closing your eyes and
  Exalting an item". The community revolted, because determinism had made
  crafting *feel fair*. Both sides were right: certainty is satisfying for
  the player and ruinous for the chase.
- **For us.** Certainty must be bounded (a budget per item) or the top is
  solved. A deterministic finishing step on a random base is a good shape.
  Hidden odds force a wiki; we show ours.

Sources: [Harvest manifesto](https://www.pathofexile.com/forum/view-thread/3069670);
[GameBanshee on the manifesto](https://gamebanshee.com/a9xq6);
[Maxroll crafting resources](https://maxroll.gg/poe/resources/crafting-resources);
[Maxroll metacrafting](https://maxroll.gg/poe/crafting/metacrafting).

### 2. Path of Exile 2: the changes (early access, December 2024 on)

- **What changed.** No crafting bench. No Orb of Scouring (an item cannot be
  reset to white), no Alteration, no Chromatic; sockets moved from gear to
  gems, so no six-link lottery. Currency is **additive**: Transmutation and
  Augmentation make a magic item, Regal makes it rare, Exalted adds a mod;
  Chaos swaps one; Annulment removes one; Divine rerolls values; Vaal corrupts.
  **Essences** guarantee one chosen mod. **Omens** (from Ritual) bend how the
  next orb behaves (only prefixes, two mods at once). **Runes and soul cores**
  go into gear sockets (removing one destroys the item). Salvage benches turn
  gear into quality materials. In 0.3, tiered orbs (Greater, Perfect) and a
  reworked essence system raised the floor of what an orb adds.
- **Agency.** Moved to the middle game: Jonathan Rogers said players should
  craft "casually", picking up an item and using a Chaos Orb on it, with "a
  big focus on midgame crafting as opposed to high end projects and perfect
  items", and fewer interacting systems at the start.
- **Determinism.** Still mostly gamble, but every step is small and additive,
  so a failure costs one orb, not the item. Omens and essences are the
  deterministic levers.
- **Economy.** Without Scouring, a good base can't be recycled, so bases
  stay valuable and drops stay interesting.
- **Failures.** Early-access players found too few deterministic options for
  self-found play; GGG answered with tiered orbs and reworked essences. The
  lesson: additive steps that never ruin the item, with a few chosen levers.
- **For us.** "Pick an upgrade off the ground, then enhance it" is exactly
  the survivors-like rhythm (the night drops, the day improves). Additive,
  small steps; no reset; one or two chosen levers (an essence-like material).

Sources: [Maxroll interview with Jonathan Rogers](https://maxroll.gg/poe/news/wudijo-path-of-exile-2-interview-with-jonathan-rogers);
[Maxroll PoE2 crafting overview](https://maxroll.gg/poe2/resources/path-of-exile-2-crafting-overview);
[Mobalytics on 0.3's changes](https://mobalytics.gg/poe-2/guides/0-3-crafting-changes);
[Mobalytics on omens](https://mobalytics.gg/poe-2/guides/omen-crafting).

### 3. Last Epoch (Eleventh Hour Games, 1.0 in 2024)

- **Loop.** Gear drops with **forging potential**; shards (salvaged from
  affixes with Runes of Shattering, or dropped) add or raise an affix one tier
  at the forge; each craft spends a random amount of potential (0 to about
  18, more for higher tiers); at zero the item is finished. Uniques can carry
  **legendary potential** (1 to 4): at the Eternity Cache, an exalted item's
  affixes move onto the unique, as many as its potential, so a lucky unique
  plus a good exalted becomes a legendary.
- **Agency.** High and legible: the player picks which affix to add or raise
  and sees the shard cost and the potential range. Glyphs modify a craft
  (Hope: a chance to spend no potential; Chaos: change the affix while raising;
  Order: keep the roll; Despair: seal an affix into a fifth slot). Runes
  remove a random affix (refunding shards), reroll values, or shatter an item
  into shards.
- **Determinism.** The target is chosen; the cost is random; crafting caps
  below the best drops (crafted tiers stop at 5, drops reach 7), so the chase
  stays in drops. Critical successes give a free tier now and then.
- **Economy.** Every item is an ingredient (shatter for shards); the forge is
  the sink for everything that drops. The Circle of Fortune faction makes
  self-found play the default, with target-farming tools.
- **Progression and story.** Light: the forge is a menu, available from the
  start; the Eternity Cache sits at the end of a dungeon (a place you earn).
- **Failures.** Little to criticise in crafting itself; the weakness is that
  the forge has no person in it, and potential running out early on a great
  base feels arbitrary.
- **For us.** The best model of **a budget per item**: transparent, finite,
  failure that spends budget but never destroys. **Crafted tiers capped below
  the best drops** keeps the chase alive. **Shatter everything into
  ingredients** kills dead drops. **Move affixes between items** (legendary
  potential) turns two finds into one.

Sources: [Last Epoch support: forging potential](https://support.lastepoch.com/hc/en-us/articles/46361900702363);
[Last Epoch support: legendary items](https://support.lastepoch.com/hc/en-us/articles/46361924310555-Legendary-Items);
[Maxroll beginner crafting](https://maxroll.gg/last-epoch/resources/beginner-crafting-guide);
[Maxroll legendary crafting](https://maxroll.gg/last-epoch/resources/legendary-items-crafting-guide).

### 4. Diablo IV (Blizzard, 2023; Loot Reborn, Season 4, 2024; Season 11 rework)

- **Loop.** Loot Reborn cut the number of drops and moved customisation to the
  blacksmith. **Tempering**: a recipe (a manual found as loot, learned for
  good) adds a random affix from its family (weapons, offensive, defensive,
  mobility, utility, resource); each item had limited **tempering durability**,
  so bad luck could "brick" it. **Masterworking**: materials from the Pit raise
  all affixes rank by rank; every fourth rank one affix (chosen at random) got a
  large bonus; it could be reset. The **Codex of Power** keeps every
  legendary aspect salvaged, upgraded by better copies. Season 11 then let the
  player **choose** the tempered affix and restore charges indefinitely, and
  rebuilt masterworking as a 0 to 20 quality bar with a capstone that turns a
  random affix greater.
- **Agency.** Tempering after Season 11 is fully chosen; masterworking keeps a
  random capstone.
- **Determinism.** The most instructive arc in the genre: launch was all
  gamble; Season 4 added "better to brick early than later" (randomness with a
  hard budget); players hated bricking a great item on the last roll; Season
  11 made tempering deterministic, and the developers said they may have gone
  "too far" and might bring back some randomness for excitement.
- **Economy.** Salvage materials and gold feed the blacksmith; the Pit gates
  masterwork materials behind an activity; the Codex makes duplicates progress.
- **Progression and story.** Manuals are found loot (discovery), learned once.
  The blacksmith is a vendor, not a person.
- **Failures.** **Bricking** (a budget that runs out on luck alone destroys the
  value of a rare find); **affix soup** before Loot Reborn (too many, too small,
  too conditional); and the swing to full determinism, which flattened the
  excitement.
- **For us.** A budget is good; a budget that can be wasted by luck alone on
  your best item is not. Show the result **before** the budget is spent, or let
  the player choose the target and gamble only the size. Fewer, bigger drops.
  A codex of what you have seen makes duplicates matter.

Sources: [Blizzard: Season 4 Loot Reborn](https://news.blizzard.com/diablo4/24077223/);
[Icy Veins: developers on the Season 11 changes](https://wp-prod.icy-veins.com/diablo-4-devs-explain-why-tempering-and-masterworking-changed/);
[Icy Veins: "Why Tempering & Masterworking Make Diablo 4 a Crafting Nightmare"](https://wp-prod.icy-veins.com/why-tempering-masterworking-make-diablo-4-a-crafting-nightmare/);
[Blizzard forums: masterwork reset and tempering](https://us.forums.blizzard.com/en/d4/t/masterwork-reset-and-tempering-improvement/169336).

### 5. Grim Dawn (Crate Entertainment, 2016 and on)

- **Loop.** **Components** drop as partial pieces (3 to 8 fragments make a
  whole); a completed component goes into an item (one per item) and gains a
  random bonus from a table by its kind. **Augments** (one per item, beside the
  component) are bought from faction quartermasters with reputation.
  **Blacksmiths** craft from **blueprints**, which drop as loot, are learned for
  good, and include relics, components and gear; crafting a relic rolls a
  completion bonus. Different smiths in the world offer different bonus
  choices.
- **Agency.** Strong: the player chooses which component and augment fit a
  build, which faction to grind for which augment, which blueprint to craft.
- **Determinism.** Components and augments are certain; completion bonuses
  are random (and can be rerolled by re-crafting). Blueprint drops are luck,
  with rare ones from Nemesis bosses.
- **Economy.** Fragments are a clean faucet with a known exchange rate;
  reputation is a second currency earned by play; iron bits pay smiths.
- **Progression and story.** **Factions are the story made economic**: who you
  side with decides which augments you can buy. Blacksmiths are people in
  places (Angrim, Duncan), and each place's smith is a little different.
- **Failures.** Inventory pressure from fragments and blueprints before the
  later stash expansions; a lot of menus.
- **For us.** **Affixes bought with standing from the people you helped**
  (augments by faction) is the best model in the genre for crafting as
  consequence. Two slots of different kinds (a component and an augment) give
  two decisions per item without soup. Partial pieces that combine are a clean
  way to make a rare thing feel earned.

Sources: [Crate forums: the factions](https://forums.crateentertainment.com/t/guide-about-grim-dawn-factions/90788);
[Grim Dawn archive wiki: blueprints](https://grimdawn-archive.fandom.com/wiki/Blueprints);
[Crate forums: item colours and rarity](https://forums.crateentertainment.com/t/items-color-and-rarity-full-explanation/35245/1);
[Crate forums: faction rewards](https://forums.crateentertainment.com/t/grim-misadventure-60-faction-rewards/28766).

### 6. Torchlight and Torchlight II (Runic Games, 2009, 2012)

- **Loop.** The **enchanter** adds a random enchantment for gold. In
  Torchlight, every enchant carried a chance of **total disenchantment**
  (every enchantment wiped), rising with each one added. Torchlight II made
  enchanting safe (up to four enchantments, enchanters in town and in the
  field with different pools, a disenchanter to clear them) and added the
  **transmuter** (gems up a grade at random, uniques swapped for random
  uniques, sockets made).
- **Agency.** Low in the first game (the only decision is when to stop);
  higher in the second (which enchanter, when to clear).
- **Determinism.** Pure gamble; the first game's risk was the drama.
- **Economy.** Gold is the sink; costs rise with each enchant.
- **Failures.** The first game's push-your-luck was memorable and also the
  worst feeling in the game (a favourite item stripped bare). The sequel
  removed the ruin and kept the gamble.
- **For us.** A push-your-luck moment is good drama when it is the player's
  choice and the stakes are stated; it must never be the only way to improve
  an item. One deliberate gamble, clearly labelled, is enough.

Sources: [GameBanshee review of Torchlight](https://gamebanshee.com/kudyr);
[Giant Bomb: Torchlight II](https://giantbomb.com/wiki/Games/Torchlight_II).

### 7. Diablo II and III (in brief; detail in `docs/items/RESEARCH.md`)

- **Diablo II's runewords and Horadric Cube**: fixed recipes, discovered
  outside the game (players shared them), turning common drops (runes, gems)
  into the best items. Certain, rare and beloved, and wiki-dependent.
- **Diablo III's Kanai's Cube**: extract a legendary's power into a codex and
  wear it without the item. Every legendary found once is kept forever; the
  most praised addition to the game.
- **For us.** Recipes the world teaches (not a wiki); a book that keeps what
  you have seen.

Sources: `docs/items/RESEARCH.md` sections 1 and 2.

### 8. Vampire Survivors (poncle, 2021 and on)

- **Loop.** In a run: weapons rank to 8; with a named passive held, a chest
  from a boss after minute 10 **evolves** the weapon. **Unions** fuse two
  maxed weapons. Between runs: gold buys **PowerUps**, each purchase raising the
  price of every other by 10% of its base, and every purchase **refundable**
  for free.
- **Agency.** Evolutions are the run's recipe: the player plans a weapon and
  its catalyst, and the draft's offers decide whether the plan comes together.
- **Determinism.** Recipes are fixed and (once found) known; whether the cards
  come is luck. PowerUps are certain.
- **Economy.** One currency (gold); the escalating PowerUp cost is the sink;
  refunds remove regret.
- **Progression and story.** Evolutions are the game's discovery: the
  collection screen fills as you find recipes.
- **Failures.** Recipes are found by accident or on a wiki; late-game
  PowerUps make runs trivial (players turn them off).
- **For us.** The ember's evolutions (combat's) are already this. Crafting's
  job is to **feed** the recipe (a gear catalyst) without owning it. Escalating
  prices that apply across a family of purchases are a clean, readable sink;
  refundable purchases remove fear of trying.

Sources: [Vampire Survivors wiki: evolution](https://vampire-survivors.fandom.com/wiki/Evolution);
[GameSpot: how to evolve weapons](https://www.gamespot.com/articles/vampire-survivors-how-to-evolve-weapons/1100-6508815/);
[Vampire Survivors wiki: PowerUp](https://vampire-survivors.fandom.com/wiki/PowerUp?oldid=5168).

### 9. Brotato (Blobfish, 2023)

- **Loop.** Enemies drop **materials**, which are at once experience and the
  shop's money; between waves the player buys weapons and items, rerolls the
  shop, locks offers, and **combines two identical weapons of a tier into one
  of the next** (to tier IV). Chests can be taken or **recycled** for
  materials.
- **Agency.** Every wave is a shop decision; combining is a planned merge.
- **Determinism.** The merge is certain; the shop is luck, with rerolls.
- **Economy.** One currency means every purchase is weighed against every
  other; Harvesting (a stat) is an investment that pays later; recycling
  turns any item into some value.
- **Failures.** Few; the shop can be fiddly at high item counts.
- **For us.** Merging two of a thing into a better one is the survivors-like's
  native craft. **Recycle at the point of decision** (the spoils) so nothing is
  dead. A single resource that doubles as power makes spending a real choice.

Sources: [Brotato wiki: materials](https://brotato.wiki.spellsandguns.com/Materials);
[Brotato wiki: shop](https://brotato.wiki.spellsandguns.com/Shop).

### 10. Halls of Torment (Chasing Carrots, 2023 and on)

- **Loop.** Equipment found in a run is lost at its end, unless the player
  carries it to a **well** during the run and lowers it in the bucket: **one item
  a run** can be lifted. The Wellkeeper then sells it back in the hub for gold,
  and it is the player's for good, worn into every later run. Quests unlock
  further gear and traits.
- **Agency.** The well is a mid-run decision with a cost: walk to the well
  (away from safety) and choose the one thing worth keeping.
- **Determinism.** Finding is luck; keeping is chosen.
- **Economy.** Gold buys back what was lifted; the one-a-run limit paces the
  collection.
- **Failures.** Players miss the well the first few runs (it must be taught).
- **For us.** The best survivors-like answer to "what comes out of a run":
  **a mid-run choice about what to carry home**, made under pressure, paid for
  in the hub. Our arena already has a way out after the win; what is carried
  out, and whether staying risks it, is our version.

Sources: [Prima Games: keeping items](https://primagames.com/gaming/how-to-keep-items-permanently-in-halls-of-torment);
[Chasing Carrots](https://www.chasing-carrots.com/halls-of-torment/);
[Godot showcase](https://godotengine.org/showcase/halls-of-torment/).

### 11. Hades and Hades II (Supergiant, 2020, 2024 and on)

- **Loop (Hades).** Darkness from runs buys talents at the **Mirror of Night**
  (respec for a Chthonic Key); gems buy **House Contractor** renovations, some
  cosmetic and some mechanical; Nectar given to people returns **Keepsakes**;
  in a run, **Wells of Charon** sell for obols, **Daedalus Hammers** offer a
  choice of two or three weapon upgrades, **Poms** rank a boon.
- **Loop (Hades II).** Reagents gathered in runs (with four **gathering tools**:
  pick, spade, rod, tablet) feed the **Cauldron**'s **Incantations**: permanent
  changes to the hub and the runs, unlocked by milestones, and a few of them
  **required to finish the story**. Seeds planted in the **garden** grow over
  encounters (five for nightshade, thirteen for wheat, twenty-one for poppy),
  across runs.
- **Agency.** Moderate and frequent: each hub visit spends a few currencies on
  one or two chosen things.
- **Determinism.** Hub purchases are certain; run upgrades are drafted.
- **Economy.** Many currencies, each from a different place, each with its
  own sink; the house renovations soak up the surplus.
- **Progression and story.** The best in the genre: the hub is people, and
  spending is talking. Incantations are story beats ("the cauldron learns
  something"), the Contractor rebuilds the house you live in, and a keepsake is
  a relationship in your hand.
- **Failures.** Currency count is high (Hades II has a dozen); late-game
  surplus has nothing to buy.
- **For us.** **Spending is a conversation**: every craft at the Waystation
  should be done by someone, with a line. **Things that grow while you are
  away** (the garden) make the hub change between runs. **Story incantations**
  (a craft that opens a door) tie making to the plot. Mid-run upgrades are
  drafted choices of two or three (the Hammer).

Sources: [Hades wiki: Darkness](https://breezewiki.discard.no/hades/wiki/Darkness);
[Prima: Hades items](https://primagames.com/gaming/hades-items-guide-nectars-keys-ambrosia-titan-blood-and-more/2);
[GGRecon: Hades II incantations](https://www.ggrecon.com/guides/hades-2-incantations/);
[Prima: Hades II seeds](https://primagames.com/gaming/how-to-plant-all-seeds-in-hades-2).

### 12. Dead Cells (Motion Twin, 2018)

- **Loop.** Enemies drop **blueprints** and **cells**. Both must be carried to
  the **Collector** at the end of a biome: a blueprint dropped before then is
  lost on death; cells are spent there to unlock the blueprint for future runs.
  The **Blacksmith's Legendary Forge** spends cells to raise the quality of what
  drops in later runs. Legendaries drop rarely, more from elites and from
  bosses killed without being hit.
- **Agency.** Which unlocks to buy; when to risk carrying.
- **Determinism.** Unlocks are certain; drops are luck.
- **Economy.** Cells are a "spend it or lose it" currency at every gate.
- **For us.** **Carrying under risk** gives the run's end tension. Unlocks
  that widen the pool (not raise power) keep runs varied.

Sources: [Dead Cells wiki: blueprints](https://deadcells.wiki.gg/wiki/Blueprint);
[Dead Cells wiki: blacksmith](https://deadcells.wiki.gg/wiki/Blacksmith).

### 13. Slay the Spire (Mega Crit, 2019; Slay the Spire 2, 2025)

- **Loop.** At a **rest site** the player either **rests** (heal 30% of maximum
  health) or **smiths** (upgrade one card, permanently for the run). Relics add
  options (dig, lift, toke, recall).
- **Agency.** One clean choice between survival now and power later. The
  upgraded card is shown before it is chosen.
- **Determinism.** Total: the upgrade is known.
- **For us.** The best small crafting choice in any roguelite: **one action,
  shown before the click, traded against something else you need**. A craft
  costs the chance to do something else.

Sources: [Untapped: rest sites](https://sts2.untapped.gg/en/guides/rest-sites);
[Metabot: rest or upgrade](https://metabot.gg/en/slay-the-spire-2/guides/campfire-rest-vs-upgrade).

### 14. Risk of Rain 2 (Hopoo, 2020)

- **Loop.** A **3D printer** shows one item; using it destroys one random item
  of the same rarity from the player's inventory (scrap first) and gives the
  shown one. A **scrapper** turns items into scrap of their rarity. **Cauldrons**
  in the Bazaar trade several lower items for a higher one.
- **Agency.** Convert unwanted into wanted, at a rate.
- **Determinism.** The output is certain; the input is random unless the player
  scrapped first (scrap is consumed first), which is the trick that turns luck
  into a plan.
- **For us.** **Scrap is a planning tool**: turning the unwanted into a
  neutral token first makes the next conversion predictable. Salvage before
  crafting.

Sources: [Risk of Rain 2 wiki: 3D printers](https://riskofrain2.wiki.gg/wiki/3D_Printers);
[Risk of Rain 2 wiki: scrapper](https://riskofrain2.wiki.gg/wiki/Scrapper).

### 15. Valheim (Iron Gate, 2021 and on)

- **Loop.** Each biome's materials make the gear to survive the next. Every
  **boss drops the key** to the next tier (an antler pickaxe for copper, a
  swamp key for iron). **Stations are upgraded by building extensions beside
  them** (the workbench to level 5: chopping block, tanning rack, adze, tool
  shelf). Gear is upgraded at the station in place, keeping the item.
  **Recipes appear when the player first picks up every ingredient.**
- **Agency.** Which set to build for which biome (frost resistance for the
  mountains, poison for the swamp).
- **Determinism.** Total: a recipe is a recipe.
- **Economy.** Materials are the only currency; each biome is a faucet; the
  upgrade is the sink. Inflation is held by biome danger.
- **Progression and story.** The world is the tech tree; the station you build
  with your hands is the visible progress.
- **Failures.** Late-game grind for a few materials; base-building chores.
- **For us.** **The danger answers itself**: the materials of a place make the
  gear that answers that place. **Discovery by touch** (pick it up, see what it
  makes) teaches without a wiki. **Upgrade in place** (the beloved item made
  better) rather than replace. **The station grows** as visible progress.

Sources: [PC Gamer: the workbench](https://pcgamer.com/valheim-workbench-upgrade-level);
[Bamboo Gaming: boss and biome roadmap](https://www.bamboogaming.net/valheim/progression);
[jeu.video: how recipes unlock](https://jeu.video/en/guide/valheim-how-to-unlock-recipes-next-biome).

### 16. Don't Starve (Klei, 2013)

- **Loop.** Stand near a Science Machine or Alchemy Engine to **prototype** a
  recipe once; after that it can be crafted anywhere.
- **Agency.** Which prototypes to spend scarce materials on.
- **For us.** **Learn it once with the master, then do it yourself.** A craft
  learned at the Waystation could later be done in the field.

Sources: [Don't Starve wiki: Science Machine](https://dontstarve.wiki.gg/wiki/Science_Machine);
[Don't Starve wiki: Alchemy Engine](https://dontstarve.wiki.gg/wiki/Alchemy_Engine).

### 17. Terraria (Re-Logic, 2011 and on)

- **Loop.** Stations unlock recipe families; the **Guide** shows every recipe
  an item is part of. The **Goblin Tinkerer** reforges an item's random
  modifier for a third of its value, so a good modifier costs more to reroll
  than a bad one; his price changes with his **happiness** (where he lives,
  who his neighbours are).
- **For us.** **Cost that scales with what you are risking** is a self-limiting
  sink. **A crafter's mood sets the price** ties relationships to the economy.
  An in-world person who answers "what can I make with this?" removes the wiki.

Sources: [Terraria wiki: reforge](https://terraria.wiki.gg/wiki/Reforge);
[Terraria wiki: making money](https://terraria.wiki.gg/wiki/Guide:Making_money).

### 18. Minecraft (Mojang, 2011 and on)

- **Loop.** The crafting grid's recipes lived on wikis for six years; the
  **recipe book** (1.12, 2017) unlocks a recipe the moment an ingredient is
  obtained. The **anvil**'s hidden **prior work penalty** doubles with each use
  (1, 3, 7, 15, 31...) until a job costs over 40 levels and the anvil says "Too
  Expensive!": the item is finished. A grindstone resets it by stripping the
  enchantments.
- **For us.** Discovery must be in the game. A **doubling cost per use** is a
  natural, readable limit on working one item forever (our heat and
  rekindling).

Sources: [Craftdex: the recipe book](https://craftdex.net/articles/the-recipe-book-and-unlocks);
[Minecraft wiki: recipe book](https://minecraft.wiki/w/Furnace_recipe_book);
[Champbop: "Too Expensive"](https://champbop.com/minecraft/how-to-bypass-too-expensive-in-minecraft/).

### 19. Subnautica (Unknown Worlds, 2018; Subnautica 2, 2026)

- **Loop.** Scan two or three **fragments** of a machine found in the world to
  learn its **blueprint**; databoxes teach whole blueprints; the fabricator
  makes it from materials.
- **For us.** **Knowledge as the gate, gathered in pieces across the world**:
  a recipe is a reward for exploring, and pieces make it feel earned.

Sources: [Keengamer: scanner and blueprints](https://www.keengamer.com/articles/guides/subnautica-2-scanner-guide-how-blueprint-unlocks-work/);
[The Games Wiki: blueprints and scanning](https://thegameswiki.com/subnautica-2/wiki/blueprints-and-scanning).

### 20. World of Warcraft professions (Blizzard, 2004 and on; Dragonflight's overhaul, 2022)

- **Loop (classic).** Gather, level a skill by crafting low-value items,
  learn recipes from trainers, drops and **faction quartermasters at
  reputation**.
- **Dragonflight's overhaul**, in its own preview: professions had become a
  chore (rushing through worthless crafts for skill), crafted gear was
  irrelevant, and crafters were indistinguishable. The answers: **crafting
  orders** (commissions, with the customer supplying reagents, public, guild or
  personal), **specialisations** (knowledge points earned by weekly treasures,
  first crafts and quests, spent on a crafter's own tree), **quality** (five
  levels for gear, three for consumables, set by skill against difficulty, with
  reagent quality adding skill and **Inspiration** a chance of extra skill), and
  **recrafting** a lower-quality item later instead of replacing it.
- **Failures.** Skill grinding (fixed by making crafts meaningful),
  reputation grinds for recipes, auction-house dominance.
- **For us.** **Commissions** (bring the materials, choose the result) and
  **recrafting the same item better later** are both strong. Reputation-gated
  recipes are crafting as consequence. Never ask the player to make junk to
  level up.

Sources: [Blizzard: "Dragonflight Preview: An Eye on Professions"](https://worldofwarcraft.blizzard.com/en-us/news/23827585/dragonflight-preview-an-eye-on-professions);
[Warcraft Tavern: the overhaul detailed](https://warcrafttavern.com/wow/news/dragonflight-professions-overhaul-detailed);
[PC Gamer: how professions work](https://pcgamer.com/world-of-warcraft-wow-dragonflight-professions).

### 21. Final Fantasy XIV (Square Enix, 2013 and on)

- **Loop.** Crafting is a class of its own (Disciples of the Hand) with levels,
  gear and a combat-like **synthesis**: fill **progress** to finish, raise
  **quality** for a high-quality result, without letting **durability** reach
  zero, spending **CP** on actions; a **condition** each step (Normal; Good, 25%
  from Normal; Excellent, 4%; Poor after Excellent) rewards reacting.
- **Agency.** The deepest moment-to-moment crafting in any game: a rotation
  you play.
- **Determinism.** Mostly skill, with conditions as luck to adapt to.
- **Failures.** A second job's worth of time; macros make it a chore once
  solved.
- **For us.** **A craft can be a small game of its own** when the decisions
  are real and the resource is visible (durability, CP). Our heat bar is the
  durability of an item's whole life, not one craft; FFXIV warns that a
  minigame repeated becomes a macro.

Sources: [Icy Veins: crafting basics](https://www.icy-veins.com/ffxiv/crafting-basics-in-ffxiv);
[Console Games Wiki: crafting](https://ffxiv.consolegameswiki.com/wiki/Crafting).

### 22. Monster Hunter (Capcom, 2004 and on)

- **Loop.** Hunt a monster, carve and break its parts, craft its weapon or
  armour, use it to hunt a harder one. **Weapon trees** branch: at points the
  player picks a specialised line. Rare parts (gems, plates) drop at low rates;
  breaking a specific part raises the odds of its material. Monster Hunter:
  World's **melding** turns surplus into specific materials, and the wishlist
  tracks what a chosen item still needs.
- **Agency.** Which monster to hunt is which gear to make; breaking parts is
  target farming.
- **Determinism.** Recipes are fixed; the parts are luck, softened by part
  breaks and melding.
- **Progression and story.** The best fusion of crafting and identity in the
  genre: wearing a monster's armour says you beat it.
- **For us.** **Choosing the hunt is choosing the craft**: the Wayfinder's
  people (the Pack, the Risen, the Lamplings, the Kerchiefs) should each yield
  their own materials. A wishlist of what a craft still needs is cheap and
  kind. Surplus should melt into something.

Sources: [Capcom wiki: the series](https://capcom.fandom.com/wiki/Monster_Hunter_(series));
[Gematsu: Monster Hunter: World's crafting](https://www.gematsu.com/2017/09/monster-hunter-world-details-crafting-eating-palico-pukei-pukei);
[Prima: the melding pot](https://primagames.com/tips/monster-hunter-world-how-use-melding-pot).

### 23. The Legend of Zelda: Tears of the Kingdom (Nintendo, 2023)

- **Loop.** **Fuse** any material to a weapon, shield or arrow: a monster's horn
  adds damage, a rock makes a hammer, an ember makes a fire arrow. Weapons
  break, so fusing is constant.
- **Agency.** Total and improvised: anything with anything, in the field, in a
  second. Fujibayashi wanted players to "freely create whatever comes to mind";
  the team tuned each combination so nothing felt like a let-down.
- **Determinism.** Total; the creativity is the game.
- **Failures.** Durability is the engine of the loop and the most divisive
  thing in it.
- **For us.** **Improvised, immediate, physical**: a material in the field
  changes what you are holding now. The night is not ours to change, but the
  day's fights can be: a mid-day improvised craft (rubbing grave-salt on a
  blade before the barrow) fits.

Sources: [Nintendo: Ask the Developer, Tears of the Kingdom, part 4](https://www.nintendo.com/sg/interview/totk/04.html);
[GoNintendo on the intent behind Fuse](https://www.gonintendo.com/contents/21435-zelda-tears-of-the-kingdom-devs-on-their-intent-behind-the-fuse-and-ultrahand).

### 24. Kingdom Come: Deliverance (Warhorse, 2018; II, 2025)

- **Loop.** Recipes are read from books; brewing is done by hand at an
  alchemy bench, step by step (grind in the mortar, add to the cauldron in
  order, work the bellows, turn the hourglass), and mistakes make a weaker
  potion. The first game let a perk **auto-brew** a recipe already brewed by
  hand; the second removed auto-brew and kept only automatic preparation.
- **For us.** **The first time by hand, the rest by rote**: a ritual is
  wonderful once and a chore at the twentieth. A craft's first making can be a
  scene; repeats should be one press.

Sources: [Kingdom Come wiki: alchemy](https://kingdomcomedeliverance.wiki.gg/wiki/Alchemy);
[Kingdom Come wiki: Routine I](https://kingdom-come-deliverance.fandom.com/wiki/Routine_I);
[Steam discussion on auto-brew in KCD2](https://steamcommunity.com/app/1771300/discussions/0/601895662819247070).

### 25. The Witcher 3 (CD Projekt Red, 2015)

- **Loop.** **Alchemy**: a potion is brewed once, then **refilled for free with
  alcohol whenever Geralt meditates**. **Crafting**: diagrams found in the
  world, made by **craftsmen of four ranks** (novice, journeyman, master,
  grandmaster); the master armourer (Yoana) and master swordsmith (Hattori)
  are unlocked by **their own quests**; witcher gear sets are found by
  **scavenger hunts** for diagrams.
- **For us.** **Craft once, refill at rest** kills the consumable chore.
  **Crafters are people with quests**, and their rank is the story's
  progress. A set found by following a trail is crafting as exploration.

Sources: [Gamereactor: alchemy guide](https://www.gamereactor.eu/the-witcher-3-wild-hunt-a-guide-to-alchemy/);
[Consolepulse: Yoana and Hattori](https://consolepulse.com/multiplatform/the-witcher/guides/the-witcher-3-master-armorers-yoana-hattori-guide);
[Gamer Walkthroughs: "Of Swords and Dumplings"](https://gamerwalkthroughs.com/witcher-3-wild-hunt/novigrad/of-swords-and-dumplings/).

### 26. Elden Ring (FromSoftware, 2022)

- **Loop.** A **crafting kit** and **cookbooks** (104, each a found key item)
  make consumables only (arrows, pots, greases, meat). Weapons are raised with
  **smithing stones** (+25) or **somber stones** (+10), found in the world;
  giving **bell bearings** to the Twin Maiden Husks turns a found material into
  one you can buy without limit.
- **For us.** Keep consumable crafting separate from gear power. **A found
  thing that turns a scarce material into a bought one** (the bell bearing) is
  a superb late-game faucet: exploration buys the end of a grind.

Sources: [Elden Ring wiki: crafting kit](https://eldenring.fandom.com/wiki/Crafting_Kit);
[Fextralife: cookbooks](https://eldenring.wiki.fextralife.com/Cookbooks);
[Fextralife: Smithing-Stone Miner's Bell Bearing](https://eldenring.wiki.fextralife.com/Smithing-Stone+Miner's+Bell+Bearing+[2]);
[Elden Ring wiki: bell bearings](https://eldenring.fandom.com/wiki/Bell_Bearings).

### 27. Darkest Dungeon (Red Hook, 2016)

- **Loop.** **Heirlooms** (crests, deeds, portraits, busts) found on
  expeditions upgrade the **hamlet's buildings**: the blacksmith (better
  weapon and armour tiers, cheaper work), the guild (skill levels). Each
  dungeon drops one heirloom kind more than others. Inventory is tight, so
  every heirloom carried out displaces food or torches.
- **For us.** **The town grows from what you bring back**, and the choice of
  where to go is the choice of what to build. **Carrying out competes with
  surviving**.

Sources: [Darkest Dungeon wiki: heirlooms](https://darkestdungeon.wiki.gg/wiki/Heirlooms);
[Darkest Dungeon wiki: the hamlet](https://darkestdungeon.wiki.gg/wiki/Hamlet).

### 28. Crashlands (Butterscotch Shenanigans, 2016): how a crafting loop was fixed

- **What broke.** A new station unlocked all its recipes at once, so players
  rushed from station to station and stopped exploring.
- **The fix.** Recipes became **drops from breaking the world's resources**, so
  breaking things taught recipes, which needed better things to break. Their
  framing: a loop is an action plus a reward that makes the next action
  wanted.
- **For us.** Pace recipes; let the world teach them.

Source: [Game Developer: "How we unbroke our crafting system"](https://www.gamedeveloper.com/design/how-we-unbroke-our-crafting-system).

### 29. Star Wars Galaxies (Sony Online, 2003): crafting as a role

- At its peak, Raph Koster wrote, about half the players ran a shop; crafting
  with resource quality and experimentation was a way of playing, not a
  menu. Removing the merchant roles hurt the game.
- **For us.** A single-player game has no market, but the lesson stands:
  crafting is worth building only if it is **a way of playing** (planning,
  choosing, a stake), not a toll booth.

Sources: [Raph Koster: Postmortems](https://www.raphkoster.com/games/books/postmortems/);
[Quarter to Three on SWG's crafting](https://forum.quartertothree.com/t/crowfall-youve-got-your-swg-crafting-in-my-shadowbane/76322).

---

## Part 2: Across the games

### 2.1 Where each loop closes

| Game | Gather | Craft | Use | Want more because |
|---|---|---|---|---|
| PoE1 | currency from maps | orbs on bases | mapping | the next mod tier |
| Last Epoch | shards from salvage | forge, budgeted | the next zone | a better base, more potential |
| Diablo IV | salvage, Pit | temper, masterwork | the Pit | greater affixes |
| Grim Dawn | fragments, reputation | components, augments | the build | faction rewards |
| Vampire Survivors | the draft | evolution | the run | the next recipe |
| Halls of Torment | a run's finds | the well | every run | one a run |
| Hades II | reagents, seeds | incantations | the house and runs | the story |
| Valheim | a biome | its gear | the next biome | the next boss |
| Monster Hunter | a monster | its gear | a harder monster | the rare part |
| Witcher 3 | diagrams, herbs | master craftsmen | the contract | the set |
| Darkest Dungeon | heirlooms | the hamlet | the next expedition | the next building |

The strong loops have **two properties**: the thing you gather comes from the
thing you are already doing (fighting, exploring), and the thing you make
changes how you do it next (a new place, a new way to fight). The weak ones
add a third activity (a profession grind) between the two.

### 2.2 The determinism spectrum

| Pure gamble | Gamble with a budget | Chosen target, random size | Chosen target, shown before paying | Fully chosen |
|---|---|---|---|---|
| Torchlight's enchanter, PoE's Chaos Orb | D4 Season 4 tempering, Last Epoch's potential cost | Last Epoch's forge, PoE2's essences | Slay the Spire's smith, Hades' Hammer | D4 Season 11, PoE's Harvest, Valheim |

The genre has swung along this line for fifteen years. Pure gamble feels
unfair; fully chosen solves the game. Grinding Gear pulled Harvest back from
the right end; Blizzard pushed Diablo IV from the middle to the right and then
said it may have gone too far. **The middle columns are where satisfaction
and the chase both live**: the player chooses *what*, luck decides *how good*,
and a visible budget decides *how many tries*.

### 2.3 Budgets: how long an item can be worked

| Game | Budget | Spent by | Restored by | Feels |
|---|---|---|---|---|
| Last Epoch | forging potential | each craft, a random amount | glyph of hope (a chance) | fair: shown, finite |
| Diablo IV S4 | tempering durability | each temper, success or not | nothing (until S11) | cruel: luck alone could end it |
| Minecraft | prior work penalty | each anvil use, doubling | the grindstone (strip all) | clear: "Too Expensive!" |
| FFXIV | durability (per craft) | each action | some actions | tactical |

A budget is the cleanest answer to "craft the best item and done": every item
has a life, and a great base with a long life is itself a find. It goes wrong
when the budget can be spent with nothing to show for it, on the best item,
by luck alone.

### 2.4 Discovery: how the player learns what can be made

From worst to best for a story game:
1. **A wiki** (Minecraft before 2017, Diablo II's runewords, Vampire Survivors'
   unions): the knowledge is outside the game.
2. **Everything at once** (Crashlands before its fix): no discovery.
3. **Recipes found as loot** (Grim Dawn, Diablo IV, Elden Ring, Crashlands
   after): discovery by luck.
4. **Recipes appear when you touch the material** (Valheim, Minecraft's book):
   discovery by exploring.
5. **Recipes taught by people, as part of their story** (The Witcher's master
   craftsmen, Hades II's incantations): discovery by relationship.

The best answer for us mixes 4 and 5: touch the material and the person who
works it knows what it makes; earn their trust or their story and they make
more.

### 2.5 Economy: faucets, sinks, inflation

- **Every drop has a value** in the best systems: Last Epoch shatters,
  Brotato recycles, Risk of Rain scraps, Diablo IV salvages to the Codex.
  Dead drops are fatigue.
- **One currency or many?** One (Brotato, Vampire Survivors) makes every spend
  a trade-off; many (Hades II, Diablo IV) give each activity its own reward
  but bloat. The middle: a money for everything and a few materials, each from
  one place and for one kind of craft.
- **Sinks that scale with the stake** (Terraria's reforge at a third of
  value; Vampire Survivors' escalating PowerUps; Minecraft's doubling) stop a
  rich player from trivialising crafting without a hard cap.
- **Faucets tied to choices** (Monster Hunter's hunt, Darkest Dungeon's
  dungeon, Grim Dawn's faction) make where you go a crafting decision.
- **Self-found games balance against the player, not a market**: Path of
  Exile's crafting only makes sense with trade; Last Epoch's Circle of Fortune
  and Grim Dawn work alone.

### 2.6 Crafters as people

The Witcher's master craftsmen (quests), Hades' Contractor and Keepsakes
(relationships), Terraria's Goblin Tinkerer (happiness sets the price), Grim
Dawn's faction quartermasters (reputation buys augments), Darkest Dungeon's
blacksmith (the building grows) and Hades II's Cauldron (story beats) all
show that **a craft done by a person is remembered**, and a craft done in a
menu is a transaction. None of them lets the story **take a crafter away**;
that is open ground.

### 2.7 Mid-run making in roguelites

| Game | Mid-run make | Shape |
|---|---|---|
| Slay the Spire | smith at a rest site | one upgrade, shown, against healing |
| Hades | Daedalus Hammer, Pom | a choice of two or three |
| Brotato | combine two weapons | merge two into one better |
| Risk of Rain 2 | printer, scrapper, cauldron | convert at a rate |
| Dead Cells | carry to the Collector | bank or lose |
| Halls of Torment | the well | lift one thing home |
| Vampire Survivors | evolution | a recipe completed by a chest |

The survivors-likes do almost no item crafting mid-run; their "craft" is the
build (evolutions, merges). What they do well at the end of a run is **decide
what comes home** (the well, the Collector). That is where a survivors-like's
crafting meets its run.

### 2.8 The failures, gathered

| Failure | Seen in | Cause | Cure |
|---|---|---|---|
| **Chores** | WoW's old skill grind; KCD's twentieth brew; FFXIV macros; Witcher-less potion restocking | repeating a solved action for its own sake | one press for repeats; refill at rest; no crafting junk to level up |
| **Inventory bloat** | Grim Dawn fragments; Hades II's dozen currencies; early Diablo IV | materials in the pack, too many kinds | a materials pouch; few materials, each with one job |
| **Craft the best and done** | Harvest; D4 Season 11 worries; Valheim's end | unlimited deterministic crafting | a budget per item; crafted caps below the best drops; new tiers by act |
| **The wiki** | Minecraft before 1.12; D2 runewords; VS unions | recipes outside the game | discovery by touch and by people |
| **Ruin** | Torchlight's disenchant; D4 bricking | luck destroys the best item | failure costs budget, never the item; the one gamble labelled |
| **Front-loading** | Crashlands before its fix | everything unlocked at once | pace recipes with exploration and story |
| **Irrelevance** | WoW's crafted gear before Dragonflight; Elden Ring's crafting kit for many players | crafted things weaker than drops | crafting improves the drops you love; its targets are what drops can't promise |
| **Market capture** | PoE, D3's auction house | trade sets every value | self-found balance |
| **Affix soup** | D4 launch | too many tiny conditional affixes | few affixes, each a decision |

---

## Part 3: The lessons (cited in `CRAFTING_DESIGN.md`)

- **C1. Gather from what you already do.** Materials come from fighting and
  exploring, never from a separate gathering job (2.1; Valheim, Monster Hunter).
- **C2. Make what changes how you play next.** A craft should open a place, a
  build or a fight, not only raise a number (2.1).
- **C3. Choose what; let luck decide how good; show the budget.** The middle
  of the determinism line (2.2; Last Epoch, PoE2's essences).
- **C4. Show the result before the budget is spent** where luck is involved,
  or make the outcome known (Slay the Spire, Hades' Hammer; the cure for D4's
  bricking).
- **C5. Every item has a life.** A visible, finite working budget per item,
  with a dear way to extend it (Last Epoch's potential, Minecraft's anvil).
- **C6. Failure spends budget, never the item** (Torchlight II over Torchlight;
  D4's bricking).
- **C7. One deliberate gamble, labelled, optional** (PoE's Vaal Orb; Torchlight's
  enchanter as drama, not as the only path).
- **C8. Crafted ceilings sit below the best drops** so the chase stays in the
  world (Last Epoch's tier 5 against 7).
- **C9. No dead drops.** Everything salvages to something (Last Epoch, Brotato,
  Risk of Rain, Diablo IV).
- **C10. Scrap first makes conversion a plan** (Risk of Rain's printers).
- **C11. Move a power from one thing into another** (Last Epoch's legendary
  potential, Kanai's Cube): two finds become one keeper.
- **C12. Upgrade in place.** The beloved item is made better, not replaced
  (Valheim, WoW's recrafting, Brotato's merge).
- **C13. The danger answers itself.** A place's materials make the answers to
  that place (Valheim's biomes, Monster Hunter's monsters).
- **C14. Choosing where to go is choosing what to make** (Monster Hunter,
  Darkest Dungeon, Grim Dawn's factions).
- **C15. Discovery by touch.** Carry a material and see what it makes
  (Valheim, Minecraft's book).
- **C16. Discovery by people.** Trust and story teach the best recipes (The
  Witcher, Hades II).
- **C17. A craft is done by someone**, in their voice; spending is a
  conversation (Hades, The Witcher).
- **C18. Standing sets the terms.** How a crafter feels about you changes the
  price or the quality (Terraria's happiness, Grim Dawn's reputation).
- **C19. The story can open a craft** (Hades II's story incantations, The
  Witcher's crafter quests) **and can take one away**, moving it rather than
  deleting it (open ground; our own).
- **C20. Things that grow while you are away** make the hub change between
  runs (Hades II's garden, WoW's commission wait).
- **C21. Decide what comes home, under pressure** (Halls of Torment's well,
  Dead Cells' Collector, Darkest Dungeon's packs).
- **C22. Mid-run upgrades are a choice of two or three**, not a menu (Hades'
  Hammer, Slay the Spire).
- **C23. A craft costs the chance to do something else** (Slay the Spire's rest
  or smith; Brotato's single currency).
- **C24. The first by hand, the rest by rote.** A ritual once, one press after
  (Kingdom Come).
- **C25. Craft once, refill at rest** for consumables (The Witcher).
- **C26. Cost that scales with the stake** (Terraria's reforge; escalating
  prices) instead of hard caps.
- **C27. Few materials, each with one job, in a pouch** (the cure for bloat).
- **C28. A codex of what you have seen** makes duplicates progress (Diablo
  III, Diablo IV).
- **C29. Self-found balance**: gold buys services, never best-in-slot.
- **C30. Exploration buys the end of a grind** (Elden Ring's bell bearings):
  a found thing turns a scarce material into an available one.

---

## Sources

ARPGs
- Path of Exile: [Harvest manifesto](https://www.pathofexile.com/forum/view-thread/3069670) · [GameBanshee](https://gamebanshee.com/a9xq6) · [Maxroll crafting resources](https://maxroll.gg/poe/resources/crafting-resources) · [Maxroll metacrafting](https://maxroll.gg/poe/crafting/metacrafting)
- Path of Exile 2: [Maxroll interview with Jonathan Rogers](https://maxroll.gg/poe/news/wudijo-path-of-exile-2-interview-with-jonathan-rogers) · [Maxroll crafting overview](https://maxroll.gg/poe2/resources/path-of-exile-2-crafting-overview) · [Mobalytics 0.3](https://mobalytics.gg/poe-2/guides/0-3-crafting-changes) · [Mobalytics omens](https://mobalytics.gg/poe-2/guides/omen-crafting)
- Last Epoch: [forging potential](https://support.lastepoch.com/hc/en-us/articles/46361900702363) · [legendary items](https://support.lastepoch.com/hc/en-us/articles/46361924310555-Legendary-Items) · [Maxroll beginner](https://maxroll.gg/last-epoch/resources/beginner-crafting-guide) · [Maxroll legendary](https://maxroll.gg/last-epoch/resources/legendary-items-crafting-guide)
- Diablo IV: [Loot Reborn](https://news.blizzard.com/diablo4/24077223/) · [developers on Season 11](https://wp-prod.icy-veins.com/diablo-4-devs-explain-why-tempering-and-masterworking-changed/) · [the crafting nightmare](https://wp-prod.icy-veins.com/why-tempering-masterworking-make-diablo-4-a-crafting-nightmare/) · [forums](https://us.forums.blizzard.com/en/d4/t/masterwork-reset-and-tempering-improvement/169336)
- Grim Dawn: [factions](https://forums.crateentertainment.com/t/guide-about-grim-dawn-factions/90788) · [blueprints](https://grimdawn-archive.fandom.com/wiki/Blueprints) · [rarity](https://forums.crateentertainment.com/t/items-color-and-rarity-full-explanation/35245/1) · [faction rewards](https://forums.crateentertainment.com/t/grim-misadventure-60-faction-rewards/28766)
- Torchlight: [GameBanshee review](https://gamebanshee.com/kudyr) · [Giant Bomb](https://giantbomb.com/wiki/Games/Torchlight_II)

Survivors-likes and roguelites
- Vampire Survivors: [evolution](https://vampire-survivors.fandom.com/wiki/Evolution) · [GameSpot](https://www.gamespot.com/articles/vampire-survivors-how-to-evolve-weapons/1100-6508815/) · [PowerUp](https://vampire-survivors.fandom.com/wiki/PowerUp?oldid=5168)
- Brotato: [materials](https://brotato.wiki.spellsandguns.com/Materials) · [shop](https://brotato.wiki.spellsandguns.com/Shop)
- Halls of Torment: [Prima](https://primagames.com/gaming/how-to-keep-items-permanently-in-halls-of-torment) · [Chasing Carrots](https://www.chasing-carrots.com/halls-of-torment/) · [Godot showcase](https://godotengine.org/showcase/halls-of-torment/)
- Hades: [Darkness](https://breezewiki.discard.no/hades/wiki/Darkness) · [Prima](https://primagames.com/gaming/hades-items-guide-nectars-keys-ambrosia-titan-blood-and-more/2) · Hades II: [incantations](https://www.ggrecon.com/guides/hades-2-incantations/) · [seeds](https://primagames.com/gaming/how-to-plant-all-seeds-in-hades-2)
- Dead Cells: [blueprints](https://deadcells.wiki.gg/wiki/Blueprint) · [blacksmith](https://deadcells.wiki.gg/wiki/Blacksmith)
- Slay the Spire: [rest sites](https://sts2.untapped.gg/en/guides/rest-sites) · [rest or upgrade](https://metabot.gg/en/slay-the-spire-2/guides/campfire-rest-vs-upgrade)
- Risk of Rain 2: [3D printers](https://riskofrain2.wiki.gg/wiki/3D_Printers) · [scrapper](https://riskofrain2.wiki.gg/wiki/Scrapper)

Survival crafting
- Valheim: [PC Gamer](https://pcgamer.com/valheim-workbench-upgrade-level) · [progression](https://www.bamboogaming.net/valheim/progression) · [recipes](https://jeu.video/en/guide/valheim-how-to-unlock-recipes-next-biome)
- Don't Starve: [Science Machine](https://dontstarve.wiki.gg/wiki/Science_Machine) · [Alchemy Engine](https://dontstarve.wiki.gg/wiki/Alchemy_Engine)
- Terraria: [reforge](https://terraria.wiki.gg/wiki/Reforge) · [money](https://terraria.wiki.gg/wiki/Guide:Making_money)
- Minecraft: [recipe book](https://craftdex.net/articles/the-recipe-book-and-unlocks) · [wiki](https://minecraft.wiki/w/Furnace_recipe_book) · [anvil](https://champbop.com/minecraft/how-to-bypass-too-expensive-in-minecraft/)
- Subnautica: [scanner](https://www.keengamer.com/articles/guides/subnautica-2-scanner-guide-how-blueprint-unlocks-work/) · [blueprints](https://thegameswiki.com/subnautica-2/wiki/blueprints-and-scanning)
- Crashlands: [Game Developer](https://www.gamedeveloper.com/design/how-we-unbroke-our-crafting-system)

MMO professions
- World of Warcraft: [Dragonflight preview](https://worldofwarcraft.blizzard.com/en-us/news/23827585/dragonflight-preview-an-eye-on-professions) · [Warcraft Tavern](https://warcrafttavern.com/wow/news/dragonflight-professions-overhaul-detailed) · [PC Gamer](https://pcgamer.com/world-of-warcraft-wow-dragonflight-professions)
- Final Fantasy XIV: [Icy Veins](https://www.icy-veins.com/ffxiv/crafting-basics-in-ffxiv) · [Console Games Wiki](https://ffxiv.consolegameswiki.com/wiki/Crafting)
- Star Wars Galaxies: [Raph Koster's Postmortems](https://www.raphkoster.com/games/books/postmortems/) · [Quarter to Three](https://forum.quartertothree.com/t/crowfall-youve-got-your-swg-crafting-in-my-shadowbane/76322)

Others
- Monster Hunter: [Capcom wiki](https://capcom.fandom.com/wiki/Monster_Hunter_(series)) · [Gematsu](https://www.gematsu.com/2017/09/monster-hunter-world-details-crafting-eating-palico-pukei-pukei) · [Prima: melding](https://primagames.com/tips/monster-hunter-world-how-use-melding-pot)
- Tears of the Kingdom: [Ask the Developer](https://www.nintendo.com/sg/interview/totk/04.html) · [GoNintendo](https://www.gonintendo.com/contents/21435-zelda-tears-of-the-kingdom-devs-on-their-intent-behind-the-fuse-and-ultrahand)
- Kingdom Come: [alchemy](https://kingdomcomedeliverance.wiki.gg/wiki/Alchemy) · [Routine I](https://kingdom-come-deliverance.fandom.com/wiki/Routine_I) · [KCD2 discussion](https://steamcommunity.com/app/1771300/discussions/0/601895662819247070)
- The Witcher 3: [alchemy](https://www.gamereactor.eu/the-witcher-3-wild-hunt-a-guide-to-alchemy/) · [master armourers](https://consolepulse.com/multiplatform/the-witcher/guides/the-witcher-3-master-armorers-yoana-hattori-guide) · [Of Swords and Dumplings](https://gamerwalkthroughs.com/witcher-3-wild-hunt/novigrad/of-swords-and-dumplings/)
- Elden Ring: [crafting kit](https://eldenring.fandom.com/wiki/Crafting_Kit) · [cookbooks](https://eldenring.wiki.fextralife.com/Cookbooks) · [bell bearing](https://eldenring.wiki.fextralife.com/Smithing-Stone+Miner's+Bell+Bearing+[2]) · [bell bearings](https://eldenring.fandom.com/wiki/Bell_Bearings)
- Darkest Dungeon: [heirlooms](https://darkestdungeon.wiki.gg/wiki/Heirlooms) · [hamlet](https://darkestdungeon.wiki.gg/wiki/Hamlet)
- General: [bit-tech: how to fix your crafting system](https://bit-tech.net/features/gaming/developers-heres-how-to-fix-your-stupid-crafting-system/1)
