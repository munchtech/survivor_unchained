# Research: itemization in the genre


Background for the item plan (`README.md` says where it fits). Summarised and paraphrased from developer talks, patch notes, wikis and player discussion; quotations are short fragments. Drop rates and caps from live games change, so check any number before relying on it. The Grim Dawn, Torchlight, Titan Quest and Elden Ring sections are more lightly sourced than the rest.
Scope: concrete mechanics, what players loved, what they hated, and the design lesson for each game, followed by cross-cutting themes and a closing list of design lessons. Everything below is summarised and paraphrased; quotations are kept to short fragments. Where a number is given it comes from wikis or patch notes, and live-service values (drop rates, caps) have changed over time, so check them before relying on them.

---

## 1. Diablo II (2000, LoD 2001, Resurrected 2021)

### Mechanics
- **Item bases in three tiers.** Every weapon and armour type exists as Normal, Exceptional and Elite versions (for example Cap, War Hat, Shako). The base fixes defence and damage ranges, strength and dexterity requirements, socket maximum and quality level. Because the base matters on its own, a white (normal) Elite base with the right socket count can be worth more than most rares. Unique and set items are tied to one base, so the unique Harlequin Crest is always a Shako.
- **Sockets and runewords.** Gems, jewels and 33 runes (El to Zod) go into sockets. Putting specific runes in a specific order into a non-magic base with exactly the right number of sockets turns it into a runeword: a named item with fixed (sometimes ranged) powerful stats, such as Enigma, Spirit, Insight or Infinity. Runewords made white items a crafting target and let players build toward endgame gear on purpose instead of waiting for one specific unique.
- **Sets** (green) give partial and full-set bonuses. Most were weak at endgame apart from a few, such as Tal Rasha's and Immortal King, plus "partial set" uses like two pieces of Angelic for the ring.
- **Uniques** (gold) have fixed affixes with rolled ranges. Build-enabling items (Shako, SoJ, Arachnid Mesh, Griffon's Eye) defined the meta.
- **Magic Find (MF)** raises the quality of drops, not the number of drops. It has diminishing returns that differ by tier. On the commonly cited table, 1000% MF works out to roughly +375% effective for rares, +333% for sets and +200% for uniques. Magic items get no diminishing returns. The result is a natural soft cap: stacking 300 to 500% MF is common and going past that is wasteful, which created a real trade-off between MF gear and kill speed (the "MF swap" and "Pindleskin runs" culture).
- **Ethereal items**: +50% base defence or damage and −10 strength/dexterity requirements, but they can't be repaired (they lose durability for good). Paired with mercenaries (who don't wear down durability on most items) and with indestructible runewords, a downside became a puzzle.
- **Gambling** (Gheed and others): spend gold on unidentified items with a small chance of being rare, set or unique. Mostly used for rings, amulets and circlets. A gold sink with a lottery feel.
- **Horadric Cube**: a transmutation box. Rune upgrades (3 of a lower rune into 1 higher), gem upgrades, socket-adding recipes, rerolling, and crafted items (Blood, Caster, Hit Power, Safety) with fixed plus random affixes. It also serves as extra inventory space.
- **Ladder and trade.** Seasonal ladders reset economies and keep ladder-only runewords out of the hands of non-ladder players. With no in-game currency (gold was worthless and capped), players used items as money. First came the **Stone of Jordan (SoJ)**, which was small (1x1), universally useful and scarce. Duping eventually wrecked it, and high runes (Ist, Ber, Jah) became the currency. D2's later "Uber Diablo" event was triggered by selling SoJs, an early in-game sink for an item-currency.

### What players loved
- The "Zod/Jah drop" moment. Extremely rare, easy-to-read, high-value drops that everyone recognises.
- Runewords: deterministic targets built from pieces, and white bases mattering.
- Bases you can understand. An Elite Monarch with 4 sockets is obviously valuable, even to beginners.
- Item-as-currency gave trade a tactile, item-centred feel. Running Mephisto and Pindleskin with MF gear is a simple, satisfying loop.

### What players hated
- Inventory and stash Tetris (fixed-size stash, mule characters, the 10x10 cube taking space). Charms taking inventory space was a deliberate trade-off that many hated and some loved.
- Duping and bots inflated the economy. The SoJ economy collapsed.
- Late-game sets and most rares were irrelevant, so the "useful item" pool was a small fraction of drops.
- Extreme rarity of high runes for self-found players. Before D2R and patch 1.13 rune-rate changes, many players never saw a Ber.

### Design lessons
- A base type tier system gives a readable, cheap axis of progression and makes normal items occasionally exciting.
- Deterministic recipes (runewords) running alongside random drops give players a long-term plan.
- Diminishing returns on a "find better loot" stat create interesting trade-offs instead of mandatory stacking.
- If players need money, they will turn your rarest small item into it. Design sinks on purpose.

Sources: https://diablo2.diablowiki.net/Magic_find_diminishing_returns ; https://diablo2.diablowiki.net/Stone_of_Jordan ; https://diablo-archive.fandom.com/wiki/Runes ; https://maxroll.gg/d2/resources/trade-guide ; https://www.purediablo.com/?p=11583

---

## 2. Diablo III (2012, RoS 2014)

### Launch problems and the Auction House
- At launch (Inferno difficulty), drops were tuned on the assumption that players would fill gaps through the gold and real-money auction houses (RMAH). Rares rolled with fully random stats, often for the wrong class (a Wizard finding Strength gear). Legendaries were weak and very rare.
- Jay Wilson at GDC 2013 said the AH "really hurt the game". Blizzard expected a small share of players to use it. In fact over half used it regularly, so buying beat killing monsters as the source of upgrades, and drops that were already tuned to be scarce felt worthless. He said the gold AH did more damage than the RMAH because more people used it. Both were shut down on 18 March 2014.

### Loot 2.0 / Smart Loot (patch 2.0.1, February 2014)
- **Smart Loot**: a large share of legendaries (often cited as about 85%) and many rares roll the finder's main stat and class-relevant items.
- **Fewer, better drops**: the stated aim was fewer items, each more likely to matter. Legendary drop rates went up sharply and legendaries got **legendary powers**, unique effects that change skills ("Skill X now does Y"), instead of plain stat blocks.
- Account-bound legendaries and crafted items (and later a "drop-time" 2-hour trade window in groups) replaced the open economy.
- **Mystic enchanting**: reroll exactly one affix per item, choosing from 2 new options plus the original, with cost rising per reroll. It locks onto the first affix you touch. Adding this targeted repair step turned a nearly good item into a project.
- **Blood shards** (Kadala): gambling currency earned in Rifts, spent on a chosen item slot. It gave an approximate target-farming path. Later bad-luck protection made Kadala more likely to give a legendary after many tries.

### Sets: 2/4/6 bonuses and their pitfalls
- RoS-era sets grant bonuses at 2, 4 and 6 pieces. Over seasons the 6-piece bonuses rose to absurd multipliers (thousands of percent up to tens of thousands of percent, applied to one skill).
- **Lock-in**: once a 6-piece bonus multiplies a single skill by 150x or more, the "build" is the set. Commentators summed it up as: *if you want to play a skill, you play the set.* Many people noted that six-piece one-skill sets did the job legendary powers should have done and wiped out off-meta skills.
- **Multiplicative bloat**: set, legendary power, cube power, paragon and gem multipliers stacked into numbers in the billions. Each patch had to raise Greater Rift scaling to match, and balance changed by "who got the next multiplier".
- Mitigations: Royal Ring of Grandeur (one fewer piece needed per set), Ring of Royal Grandeur in the cube, and Legacy of Nightmares (a set that rewards wearing *no* other set pieces). It was briefly the diversity champion and then outscaled.

### Kanai's Cube (2.3)
- Destroy a legendary to **extract its power permanently** into one of three slots (weapon, armour, jewellery), usable on every character. This turned duplicate and weak legendaries into "collection" progress and let players combine powers. Very well liked because it raised the value of every legendary drop for the first time per power, and enabled build experimentation.
- It also became a source of power creep. Every cube power is another multiplier.

### Ancient and Primal; Paragon
- **Ancient** (about 10% of legendaries): roughly 30% higher base values. **Primal Ancient** (very rare, unlocked by soloing GR70): perfect rolls on all stats. Primals gave the "perfect item" chase a defined end point and a visible red border. They also made non-primal versions feel worse.
- **Paragon**: unlimited account XP levels that add small stats. It gave "always progressing" and removed the hard cap. At high Paragon it was criticised as an infinite grind that buried gear differences under raw stats. Later seasons capped Paragon's main-stat contribution.

### What players loved
- After 2.0: frequent legendary drops, smart loot, Kanai's Cube, seasons with a seasonal theme and free Haedrig's Gift set, plus clear progression to Primals.

### What players hated
- Launch: worthless drops, AH-centred play.
- After RoS: set dependency, damage numbers too large to read, "one build per class per season", and the loss of trade as a social game.

### Design lessons
- An open marketplace that is more efficient than playing replaces the core loop. Either gate trade or design drops assuming it exists, but don't do both badly.
- Effect-based legendaries are better than stat sticks. Keep multipliers few and on separate axes, or the numbers become unreadable and balance becomes impossible.
- Full-set bonuses that multiply one skill end build variety. Prefer small set sizes, or bonuses that change behaviour instead of scaling it.
- Collection mechanics (Kanai's Cube) turn duplicate drops into permanent progress.

Sources: https://www.pcgamer.com/diablo-3-auction-house-jay-wilson ; https://diablo.fandom.com/wiki/Loot_2.0 ; https://www.shacknews.com/article/83266/diablo-3-patch-201-deploys-with-loot-20 ; https://www.icy-veins.com/d3/kanais-cube-guide ; https://us.forums.blizzard.com/en/d3/t/genuinely-dont-think-one-set-buffing-one-skill-is-the-best-idea/11940 ; https://us.forums.blizzard.com/en/d3/t/a-short-study-on-intra-class-build-diversity/11233 ; https://wp-prod.icy-veins.com/talismans-in-diablo-4-a-new-system-with-old-risks/

---

## 3. Diablo IV (2023 and later)

### Launch mechanics
- **Aspects and the Codex of Power**: legendary powers are separate from items. Many aspects are unlocked permanently in the Codex by completing dungeons. Others are extracted from dropped legendaries at the Occultist (destroying the item) and imprinted onto a rare or legendary, turning it into a legendary. At launch, an extracted aspect was single-use, while Codex aspects were reusable at a fixed (often low) roll.
- **Affixes**: 4 affixes on legendaries at launch, drawn from a pool of more than 200 distinct properties. Many were conditional ("+X% damage to Vulnerable / Crowd-controlled / Close / Distant / Injured / Healthy enemies", "while Fortified", "while Berserking", "damage over time to Chilled", and so on).
- **Uniques** with fixed powers. **Uber uniques** (later renamed **Mythic uniques**) such as Shako, Grandfather, Doombringer, Andariel's Visage, Ring of Starless Skies, Tyrael's Might and Harlequin Crest, with extremely low drop rates at launch.
- **Obols / Purveyor of Curiosities**: a gambling vendor (D3's Kadala, renamed) using a capped currency.

### Launch complaints
- **Affix soup**: too many niche and conditional damage affixes that all reduce to "more damage" in slightly different buckets. Players mocked them as "damage on Tuesdays". Evaluating an item meant reading 4 lines of situational text and doing bucket maths (additive "+% damage" versus multiplicative aspects). The community compiled more than 200 properties.
- Most legendaries were salvage fodder. The usable outcome rate was tiny, so drops felt like noise, and the most common action was "pick up, glance, salvage".
- Uber uniques were so rare (often estimated at well under 1 in tens of thousands of eligible drops) that most players never saw one. Some unique powers were weak.
- Item power and level gates. Upgrades were often just a bigger item power number with the same useless affixes.

### Season 4 "Loot Reborn" (May 2024) and its lessons
Changes (applied to both Seasonal and Eternal realms):
- **Fewer affixes per item**: legendaries drop with 3 affixes, rares with 2. Ancestral items have a higher floor.
- **A consolidated affix pool**: many conditionals were removed or merged. Generic affixes such as "+% Damage", "+Max Life" and skill ranks became the main stats. The goal was stated as "quality over quantity".
- **Greater Affixes**: affixes rolling about 1.5x normal value, marked with a star and an icon on drop. Items with 1 to 4 GAs became the long-term chase.
- **Tempering**: adds up to 2 extra affixes from build-themed recipe families (learned by salvaging manuals), with limited reroll charges ("durability"). It returns crafting agency but keeps some RNG and a "bricking" risk.
- **Masterworking**: 12 upgrade ranks. Every 4th rank boosts one affix chosen at random (a big "crit"). Later in S4 a reset option was added (verify the exact patch). Patch notes also removed failure chance from masterworking and made tempering results clearer.
- **Codex aspects** now unlock at maximum roll when you salvage a better one. Aspects become collectibles that upgrade themselves.
- **Helltide/Tormented bosses and boss ladder**: from S4/S5, Tormented versions of bosses drop guaranteed max-level loot and give a better Mythic chance (about 7.5% per kill reported in S5). From S5, **Resplendent Sparks** let players craft a chosen Mythic, which is a deterministic pity route. Andariel and Duriel drop specific uniques, so you can target farm.
- Loot filtering by sorting, and salvage-all becoming practical.

Reception: widely called "the game D4 should have launched as". Major reviewers said D4 was "finally great", and Steam player counts set records. Remaining complaints: tempering and masterworking are long grinds with sharp RNG (rolling the wrong masterwork affix, bricking tempers), Greater Affixes again make 99% of drops trash at the very top, and power creep came fast (S4 to S5 numbers inflated and a later stat squish was needed in the 2025 expansion era). The *Vessel of Hatred* / later updates and the *Lord of Hatred* expansion brought back set bonuses through a talisman/charm system. Commentators flagged the D3 lesson that sets must not become mandatory.

### Design lessons
- Cutting affix count and conditionals made items **readable at a glance**, and readability alone made loot feel better without lowering depth much.
- A visible "this roll is exceptional" marker (GA star, D3's Primal border) creates a clear top-end chase that doesn't need more affix types.
- Crafting systems that layer on top of drops (temper, masterwork) give agency, but each RNG step with a bricking risk adds frustration. Show odds and allow recovery.
- Deterministic unlocks (Codex) and pity crafting (Sparks) fix the "never saw it" problem for ultra-rares.

Sources: https://www.icy-veins.com/d4/news/diablo-4-season-4-loot-reborn-patch-notes/ ; https://maxroll.gg/d4/resources/season-guide ; https://www.windowscentral.com/gaming/diablo-4-campfire-chat-loot-reborn ; https://www.dexerto.com/diablo/diablo-4-itemization-2338349/ ; https://mein-mmo.de/en/why-does-the-game-insist-on-being-so-boring-items-frustrate-players-in-diablo-4,1087697/ ; https://www.dexerto.com/diablo/fans-call-diablo-4-season-4-a-new-beginning-2689792/ ; https://dotesports.com/diablo/news/diablo-4-tormented-bosses-how-to-summon-difficulty-and-loot ; https://www.gamesradar.com/diablo-4-aspects ; https://maxroll.gg/d4/resources/purveyor-of-curiosities-gambling ; https://www.wowhead.com/news=380356/set-bonuses-return-to-diablo-with-lord-of-hatred-talisman-and-charm-system

---

## 4. Path of Exile 1 and 2

### PoE1 mechanics
- **Item level (ilvl) and affix tiers**: every modifier has tiers (T1 is best) gated by ilvl. An ilvl-84+ base can roll top tiers, and some influence mods need 86. ilvl is the hidden "potential" of an item. Experienced players read affix tiers through an advanced item description (Alt-hover), so tiers are visible but take skill to read.
- **Prefix/suffix limits**: rares hold up to 3 prefixes and 3 suffixes (magic items 1+1). Prefixes are mostly life and flat damage, suffixes mostly resistances, attack speed and crit. The limit is what turns crafting into a puzzle: "blocking" a slot, "open prefix", "prefixes cannot be changed" metacrafts.
- **Currency as crafting (orbs)**: no gold at all in PoE1. Transmutation, Alteration, Augmentation, Regal, Alchemy, Chaos, Exalted, Divine, Annulment, Scouring and others each change an item in a specific way. Because each orb is *useful*, it holds value and works as money. This is the key innovation: currency sinks are built into crafting, and inflation is fought by consuming the currency.
- **Essences** (guarantee one specific mod and reroll the rest) and **Fossils** (bias the mod pool by tag, with Resonators holding 1 to 4 fossils) are deterministic or weighted crafting layered on random rolls. Also Harvest (reforge with a chosen tag) and the crafting bench (pay to add a chosen mod into an open slot).
- **Build-defining uniques**: items whose effect enables a build (Headhunter, Mageblood, Shavronne's Wrappings, Aegis Aurora). Many leveling uniques make early play fun. Ultra-rare chase uniques (Mirror of Kalandra, Headhunter) anchor the excitement at the top of the economy.
- **Loot filters**: a text-based filter language (show, hide, recolour, resize, sound, minimap icon, light beam). **NeverSink's filter** (and the FilterBlade web tool) is used by most of the player base and updates the economy tiers every league. GGG treats filters as part of the game. Chris Wilson has said he dislikes "colour equals value", preferring that players sometimes find a blue better than a yellow so they read everything. Filters then hide most of the screen.
- **Trade vs SSF**: PoE has an official trade site but deliberately keeps friction (no auction house; you must whisper and visit). The game is balanced around trade being available, and SSF leagues exist as an opt-in. Long-running debate: trade lets players bypass the loot loop, and the friction annoys everyone, but GGG has argued the friction stops trade from fully replacing drops. They later added a currency exchange and asynchronous trade features in some areas.

### PoE2 changes (early access December 2024 onward)
- **Fewer currency drops early, especially Chaos and Exalted**. A bigger drop table of low-tier transmutes and augments. Gold returns as a separate vendor/respec currency.
- **Crafting redesigned for "craft early and often"**: Exalted adds a random mod, Chaos removes one random mod and adds one random mod (instead of rerolling everything), and Regal/Alchemy are central. Jonathan Rogers said the aim was more mid-game crafting and fewer interacting systems at launch, not top-end perfect-item projects.
- **Salvage bench**: destroy quality items for quality currency and socketed items for Artificer's Shards (which combine into an Orb to add sockets). This gives junk drops a use.
- **Sockets now hold runes and soul cores** (single augment mods such as +resistance, added damage, spirit) instead of skill gems. Skill gems moved to a separate menu. Sockets became "fixed-value item tuning", the job the PoE1 crafting bench used to do.
- **Reception**: early complaints about currency scarcity ("crafting is gambling and I can't afford to gamble"), very rare uniques, and SSF players feeling locked out of upgrades without trade. GGG responded with several drop-rate increases (for example Divine Orbs made "more common" in a later update, partly so league-versus-core rates couldn't be compared directly), plus more crafting determinism through Omens and Essences.

### What players loved
- Deep crafting with high skill ceiling, chase uniques, economy-driven leagues, a filter that lets you shape loot to your own eye.
### What players hated
- Screen clutter (PoE1), required external tools (filter, trade site, crafting simulators), trade friction, and the feeling that "the economy plays the game". In PoE2's early period, too little currency to engage with the new crafting.

### Design lessons
- Make your currency the crafting material, so the sink is automatic and every drop is a decision.
- Hard slot limits (3/3) produce crafting puzzles from a small rule.
- If you produce PoE-scale loot volume, filters are mandatory. Ship one in-game, with good defaults.
- Tuning "scarce, gambly" crafting needs enough raw input. Players hate a crafting system they can't afford to use.

Sources: https://maxroll.gg/poe/news/wudijo-path-of-exile-2-interview-with-jonathan-rogers ; https://www.pcgamesn.com/path-of-exile-2/return-of-the-ancients-divine-orbs ; https://maxroll.gg/poe2/resources/path-of-exile-2-crafting-overview ; https://maxroll.gg/poe2/resources/runes-and-soul-cores ; https://poe2wiki.net/wiki/Salvage ; https://gamebanshee.com/xfwfq ; https://maxroll.gg/poe2/news/filterblade-launch-for-path-of-exile-2 ; https://www.sportskeeda.com/mmo/things-path-exile-2-needs-fix-next-major-update ; https://jp.pathofexile.com/forum/view-thread/3784163

---

## 5. Last Epoch (1.0 in February 2024)

### Mechanics
- **Rarities**: Normal, Magic, Rare (up to 4 affixes, 2 prefix and 2 suffix), **Exalted** (a rare with at least one T6 or T7 affix, shown in purple), Unique, **Set**, **Legendary** (a unique merged with an exalted item's affixes).
- **Crafting with Forging Potential (FP)**: each item has an FP pool. Applying a glyph or shard to add or upgrade an affix (T1 to T5 craftable; T6 and T7 drop-only) costs a random amount of FP. When FP runs out the item is finished. Glyphs modify the process (Glyph of Hope: chance to use no FP; Glyph of Stability: protect against fracture, from older versions; Glyph of Chaos: reroll an affix; Glyph of Order: keep values). Runes remove affixes or duplicate items. The crafting screen shows tiers, ranges and FP cost ranges, so the system is open about everything except the exact roll.
- **Legendary Potential (LP)**: uniques drop with 0 to 4 LP. In the **Temporal Sanctum** (a key-gated dungeon off Monolith timeline bosses), a unique with N LP and an exalted item with affixes are combined, and N random affixes transfer. Later, "Weaver's Will" (a separate crafting-only pool on some uniques) was added for crafting variance. A 4LP chase unique is the top chase item.
- **Item Factions**: on reaching the endgame, each character picks one of two factions:
  - **Merchant's Guild (MG)**: trading through the Bazaar (an auction house) and player trade, costing Favor (a separate earned currency). Rank gates which rarities you can trade. Crafting materials are never tradable.
  - **Circle of Fortune (CoF)**: no trading, but much better drops (Prophecies for targeted loot, more Legendary Potential, double "Unique with LP" chance at rank 6, more exalted chances). Items found under CoF need CoF rank to equip.
  The developers framed this as serving both the "earn it myself" and "I like trading" crowds instead of forcing one compromise.
- **In-game loot filter**: rule-based (show/hide/recolour/emphasize by type, class, affix, tier, LP), with import and export. Shipped as a first-party feature, widely praised.
- Set items exist (fixed affixes, 2+ piece bonuses) but were widely seen as weaker than uniques/exalteds at 1.0. Later patches reworked them; check current patch notes for specifics.

### What players loved
- Transparent, deterministic-ish crafting ("I know exactly what I am working toward").
- CoF made self-found viable. In-game filter from day one. Exalted items as a clear "pick this up" signal. Seeing affix tiers on the ground.
### What players hated
- FP RNG ("bricked on the second craft"). Later endgame was thin and LP chase was very grindy. Some felt the MG Favor costs were punitive. Set items were underwhelming.

### Design lessons
- Showing everything (ranges, tiers, costs) builds trust and makes crafting decisions skill-based.
- Making "trade vs self-found" a per-character choice with real payoff on both sides avoids balancing the whole game around trade.
- A visible "potential" number (FP, LP) on drops turns "is this good?" into a quick, readable check.

Sources: https://forum.lastepoch.com/t/trade-development-update-introducing-merchants-guild-and-circle-of-fortune-factions/51994 ; https://www.icy-veins.com/last-epoch/trade-and-item-factions-overview ; https://www.icy-veins.com/last-epoch/crafting-guide ; https://maxroll.gg/last-epoch/resources/loot-filter-guide ; https://forum.lastepoch.com/t/loot-filters-in-last-epoch/24302 ; https://maxroll.gg/last-epoch/news/item-factions-preview

---

## 6. Grim Dawn (Crate Entertainment, 2016 and later)

### Mechanics
- **Components**: crafting materials found in pieces (for example 3 fragments make 1 component) that slot into specific gear types for fixed bonuses, sometimes granting a skill. **Completed components** gain a random bonus when assembled. One component per item. The Inventor can remove components (keeping the item or the component).
- **Augments**: purchased from faction vendors, applied to gear (one per item) for skill-based or stat bonuses. They tie reputation progress directly to build power.
- **Blueprints**: recipes found or bought that let the Blacksmith craft specific items or components. Crafted items get a bonus stat picked from a blacksmith-specific list (offence, defence, etc.).
- **Factions/reputation**: killing faction enemies and doing bounties raises standing, unlocking vendors with augments, blueprints and faction-only gear.
- **Monster Infrequents (MIs)**: green items that drop only from specific monster types (for example a particular undead hero), with a fixed "signature" stat (often a skill modifier) plus random affixes. This gives "farm this monster for that item" targeting without being a unique.
- **Sets** with 2 to 5 piece bonuses that often change skill behaviour. Several build-defining sets, and later expansions added more "item skill modifiers" on sets and uniques.
- **Item affixes**: prefix and suffix name-based ("Of the Inquisitor"). Players hunt "double rares" (rare prefix and rare suffix).

### What players loved
- Lots of layered customisation (component, augment, crafted bonus, transmutes), MI target farming, reputation-gated power that rewards questing, and huge build variety.
### What players hated
- Heavy stash management (many component pieces, tiered materials). Tooltip density: dozens of stat lines on an item. Some MI and faction gear is required for resistance capping, which feels like chores.

### Design lessons
- Fixed-source items (MIs) are a cheap, very effective target-farm mechanism.
- Faction reputation that pays out in itemization (augments) connects world content to gearing.
- Multiple small slot-in upgrades (component plus augment) give steady incremental progress between big drops.

Sources: https://www.grimdawn.com/guide/items/components/ ; https://www.grimdawn.com/guide/items/crafting ; https://forums.crateentertainment.com/t/items-color-and-rarity-full-explanation/35245 ; https://grimdawn-archive.fandom.com/wiki/Blueprints

---

## 7. Other games

### Torchlight / Torchlight II (Runic)
- **Enchanting**: a town Enchanter adds random enchantments to an item, with a stacking chance of failing and wiping all enchants (TL1), or an increasing cost (TL2). An extra enchanter can remove gems or enchants. This is a "push your luck" item gamble.
- **Pets as itemization**: your pet has its own gear slots (collars, tags), can learn spells, and can run back to town to sell junk, which famously removed town trips. Feeding fish transforms the pet temporarily.
- **Lesson**: automate the tedium (selling) through fiction. Players remember the pet more than any item.
- Sources: https://torchlight.fandom.com/wiki/Pets_(T2)?oldid=7354 ; https://steamcommunity.com/app/200710/discussions/0/34096318946583799

### Titan Quest (Iron Lore, 2006; Titan Quest II in early access 2025)
- **Relics and charms**: drop as shards. Collect N shards (often 3 to 5) to complete one, gaining a random **completion bonus**, and socket it into gear. Artifacts are crafted by combining relics/charms with an arcane formula.
- **Lesson**: shard collection gives steady progress and a completion moment. Random completion bonuses add a reroll chase. TQ2 brings back socketable charms.
- Sources: https://lparchive.org/Titan-Quest/Mechanics 3 ; https://massivelyop.com/2025/12/01/titan-quest-ii-previews-the-forge-mastery-skill-and-socketable-charms-arriving-in-its-next-update

### Lost Ark (Smilegate)
- **Honing**: gear item level rises through upgrade attempts that consume materials and gold. Success chance drops at higher levels (single-digit percent at high T3), and failed attempts consume materials. **Artisan's Energy** is a pity bar that guarantees success at 100% and resets on success.
- **Engravings and accessories**: build identity comes from engraving books and accessories with engraving rolls, plus ability stones you "facet" (a 10-tap RNG minigame for engraving nodes). It is a build system on items, but with heavy RNG.
- **Player sentiment**: honing was the most cited frustration (long fail streaks, unrecoverable materials, monetised boosters). The pity bar softened but didn't fix it. Later updates reduced honing difficulty and added more "advanced honing" with determinism.
- **Lesson**: failure that destroys inputs feels much worse than "nothing happened". If you add pity, make it visible and generous, and don't make the main progression gate a coin flip.
- Sources: https://maxroll.gg/lost-ark/resources/gear-honing-system ; https://upcomer.com/smilegate-is-killing-lost-ark-through-its-unfair-honing-system

### Hades (Supergiant, 2020)
- **Boons as itemization**: each room reward is a choice of 3 boons from one Olympian god. Each god "owns" a status (Zeus jolt, Ares doom, Poseidon knockback) and a slot (attack, special, cast, dash, call). Rarity (Common, Rare, Epic, Heroic) scales the numbers, so the *effect* is the identity and rarity is magnitude.
- **Duo boons**: unlocked by holding prerequisites from two specific gods. They create synergy goals within a run and characters talk about the pairing. **Legendary boons** need prerequisites from a single god.
- **Pom of Power** raises the level of an existing boon. It is the "invest in what you have" choice versus breadth. **Daedalus hammers** modify weapon behaviour.
- **Keepsakes**: equipped before each region, they bias which god appears or improve rarity. This gives a meta lever over randomness. Mirror upgrades (for example rerolls through Fated Authority) add a bad-luck valve.
- **Lesson**: a short list of choices, each with one clear effect and an obvious synergy tag, is better than random stat drops for build-crafting within a run. Prerequisite-based combos (duos) are the "aha" moment.
- Sources: https://en.wikipedia.org/wiki/Hades_(video_game) ; https://primagames.com/tips/hades-what-are-duo-boons-how-get-duo-boons ; https://butwhytho.net/2021/08/13/interview-developing-hades-with-supergiant-games-greg-kasavin/

### Vampire Survivors (poncle, 2021 and later; most relevant to a survivors-like)
- **Weapon and passive slots** (6 each). Level-ups give 3 to 4 random choices, with Reroll, Skip and Banish as player-earned meta resources to shape randomness.
- **Evolutions**: a max-level weapon plus its paired passive (usually just *owned*, at any level; a few require max level or several passives), then opening a **treasure chest** from a boss (normally after the 10-minute mark on most stages) evolves the weapon. The passive is generally kept. "Unions" merge two weapons into one (freeing a slot).
- **Chests** have 1, 3 or 5 items with a slot-machine reveal animation and music. Higher counts come from Luck and chance. The reveal is a big part of the fun.
- **Arcanas** (run-wide modifiers) and character-specific starting weapons add meta itemization.
- **Lesson**: pairing rules turn every level-up into a planning decision ("I need Spinach for Fire Wand"). The chest reveal is pure presentation, but it carries a lot of the excitement. Discovery of recipes (the in-game collection) drives early hours.
- Sources: https://vampire-survivors.fandom.com/wiki/Evolution ; https://rogueranker.com/vampire-survivors-evolution/

### Elden Ring / Dark Souls (FromSoftware)
- **Item descriptions as lore**: nearly every item has a short flavour paragraph that pieces together world history. Players reconstruct the story from items (VaatiVidya and others). Items have narrative value beyond stats.
- **Upgrade materials**: regular weapons use Smithing Stones (+25), unique and boss weapons use Somber Stones (+10). Material scarcity gates power, and Bell Bearings later make materials buyable. It is deterministic: upgrades never fail.
- **Ashes of War and affinity**: Ashes (found or bought) replace a weapon's skill and set its affinity (Heavy, Keen, Quality, Fire, etc., changing stat scaling). They are not consumed and can be swapped freely at a Site of Grace (Elden Ring). This separates "moveset" from "skill" and "scaling". Dark Souls used one-way infusion with gems.
- **Low drop volume, hand-placed items**: most gear is placed in the world, so exploration *is* the loot system.
- **Lesson**: fewer, authored items with flavour text give each item identity. Upgrades that never fail feel fair. Modular, freely swappable components support experimentation.
- Sources: https://eldenring.fandom.com/wiki/Ashes_of_War ; https://www.windowscentral.com/elden-ring-how-upgrade-weapons ; https://pcgamer.com/best-elden-ring-ashes-of-war

### Darkest Dungeon (Red Hook)
- **Trinkets**: 2 slots per hero. Most trinkets have a clear upside and an explicit downside (for example +accuracy, −speed; +bleed resist, −dodge). Some are class-specific, some come from sets (Crimson Court), and rarity rises with dungeon length and difficulty (Common to Ancestral). Ancestral trinkets are named and come with lore.
- **Lesson**: built-in downsides force fitting items to a role or formation, making "is this good?" contextual instead of strictly better. A few slots plus a large pool of quirky trinkets supports theorycrafting without stat bloat.
- Sources: https://darkestdungeon.wiki.gg/wiki/Trinkets_(Darkest_Dungeon) ; https://darkestdungeon2.wiki.fextralife.com/Trinkets

---

## 8. Cross-cutting themes

### 8.1 What drives "the chase"
- **Readable rarity tiers with a known top end**: a Zod rune, a Mirror of Kalandra, a 4GA item, a 4LP unique, a Primal. Players need to know the jackpot exists and what it looks like, even if they never get it.
- **Build-enabling effects, not numbers**: Headhunter, Kanai powers, D4 aspects, Hades duos. A drop that opens a new way to play beats a +8% upgrade.
- **Intermediate goals**: runeword recipes, component shards, codex unlocks, evolution pairs. These let progress happen between jackpots.
- **Near-miss and "almost perfect" items** give a reason to keep rolling (Mystic, Divine Orbs, masterwork), and players will chase optimisation forever if the steps are transparent.
- **Social proof**: trade value and streamer clips make rare items recognisable.

### 8.2 What causes loot fatigue
- **Volume without value**: D4 at launch, D3 at launch, PoE without filters. When most drops are salvage, players stop looking and loot turns into noise. The usual fix is fewer drops, each more likely to matter (D3 Loot 2.0, D4 S4).
- **Unreadable items**: many conditionals, stacked additive/multiplicative buckets, numbers in the billions. When players can't judge an item in about 2 seconds, they offload judgement to external tools.
- **Upgrades too small to feel**: "+2% damage to Chilled" doesn't register.
- **Over-saturation of rarity**: if legendaries are routine (late D3), "legendary" stops meaning anything, which is why top-end markers (Ancient, Primal, GA) were added.
- **Power bloat**: when every season adds multipliers, items go obsolete fast and a squish follows (D3 never squished. D4 squished in 2024–2025, as did WoW multiple times).

### 8.3 Inventory tedium
- Fixed grids with odd shapes (D2 Tetris) are nostalgic but tedious. Common fixes: auto-sort, salvage-all by rarity, auto-pickup for currency and materials (D3/D4/LE), material bags that don't use slots (D3 2.x, D4 Season 2 or later, LE crafting stash), the Torchlight pet selling junk, and loot filters to stop pickup in the first place.
- Stash limits push players to mule characters and alt accounts. Generous, searchable stashes, sorted by tabs, are now expected.
- Town trips should be optional or seamless (portals, pet selling, salvage anywhere).

### 8.4 Bad-luck protection and pity
- Examples: Hearthstone (legendary guaranteed within 40 packs), WoW Legion legendaries (rising chance per kill, which caused controversy when protection stopped after a cap, so Blizzard removed the cap), Lost Ark Artisan's Energy, D3 Kadala bad-luck protection, D4 Resplendent Sparks (craft a chosen Mythic), LE CoF Prophecies, Hades Fated Authority rerolls, Vampire Survivors Reroll/Banish.
- Principles: pity should be **visible** (a bar or counter), **stack across failures**, and ideally **convert failure into currency** (salvaging duplicates or failures into a token that buys the target). Hidden pity helps statistically but doesn't reduce anxiety. Pity caps that switch off (Legion) feel like betrayal.

### 8.5 Target farming
- Mechanisms: **fixed-source drops** (Grim Dawn MIs, D4 boss-specific unique tables, D2 Mephisto/Andariel quest drops, LE unique drop locations), **slot-based gambling** (Kadala, Obols, D2 gambling), **currency-bought specific outcomes** (Essences, Harvest, Codex imprinting, PoE crafting bench), **prophecy-style modifiers** (LE CoF), and **in-run biasing** (Hades keepsakes, VS banish).
- Trade-off: target farming lowers the "anything could drop" excitement but greatly raises perceived fairness. Most modern games mix the two: random drops for excitement plus deterministic routes for the specific item you need.

### 8.6 Trade vs self-found
- Open, efficient trade (D3 AH) replaces playing the game, and the designer then has to make drops scarce to keep the market going, which punishes non-traders. D3 removed trade, D2 had informal trade (and bots/dupes), and PoE has deliberately frictional trade plus SSF. LE puts the choice per character (MG vs CoF), and D4 has limited trade (only some items; legendaries with GAs have been untradeable at times).
- Lesson: decide whether the game is balanced around trade. If not, gate trade heavily, offer a self-found boost, or make the best items account-bound.

### 8.7 Loot presentation (beams, sounds, colour)
- Rarity colours (white, blue, yellow, orange/gold, green) are a cross-genre language. Don't re-invent them without reason.
- Light beams and pillars (D3/D4 orange/brown beams, PoE filter beams, LE emphasis), unique drop sounds (D3's legendary chime, D2 rune drop sound in D2R, Vampire Survivors chest music). These are low-cost, high-dopamine features that train players to recognise value instantly.
- Minimap icons for valuable drops, and on-ground labels (with "ancient/GA" markers) so players don't need to pick up and hover.
- Chris Wilson's counterpoint: don't make colour a perfect proxy for value, or players stop reading. But too much reading causes fatigue. Ideal: colour gives the *band*, a marker gives the *exception*.

### 8.8 Power creep and stat squish
- D3's multipliers (sets, cube, paragon) produced GR150 and later numbers no one could read. D4 hit 1e10+ damage numbers by Season 5 and squished. Each "Season X adds a new power layer" pattern compounds.
- Mitigations: cap layers (one set, one legendary power per slot), use additive buckets where possible, add *new verbs* instead of new multipliers, budget a squish at expansion boundaries, and keep enemy scaling legible (difficulty tiers instead of infinite GR levels where possible).

### 8.9 Few affixes/legibility vs depth
- **Legible end** (Hades, Darkest Dungeon, Vampire Survivors, Elden Ring): few stats, each item has a distinct identity. Depth comes from *combinations* and situational downsides.
- **Deep end** (PoE, Grim Dawn): many mods, tiers, and crafting layers. High mastery ceiling, but needs external tools and alienates newcomers.
- **Middle** (D4 after S4, Last Epoch): 2–4 affixes, consolidated pool, explicit tier/quality markers, layered optional crafting. The D4 S4 result suggests most players prefer cutting affix count and conditionals and moving depth into a few systems (aspects, tempering, GA), instead of more affix types.
- Heuristic: each affix should change a decision. If two affixes differ only by which multiplier bucket they hit, merge them.

---

## 9. Closing list: concrete design lessons

1. **Value per drop beats drop count.** Tune for fewer drops, each more likely to matter (D3 Loot 2.0, D4 S4).
2. **An item must be judgeable in about 2 seconds.** Limit affixes (2–4), prefer unconditional affixes, and show the comparison delta.
3. **Effects over numbers for the top tier.** Uniques and legendaries should change *how you play* (Kanai powers, Hades boons, VS evolutions), not only add damage.
4. **Few multiplier buckets, documented clearly.** Stacked multipliers lead to unreadable damage and constant re-balancing (D3 sets, D4 S5).
5. **Small sets, or behaviour-changing set bonuses.** Avoid 6-piece "skill X +5000%" lock-in. Prefer 2–3 piece bonuses that add mechanics.
6. **Give players a known jackpot.** A recognisable top-end item (Zod, Mirror, Primal, 4GA) sustains long-term interest even if rare.
7. **Mark exceptional rolls visibly on drop.** GA star, Primal border, LE exalted purple, filter beam.
8. **Pair random drops with deterministic routes.** Recipes (runewords), collection unlocks (Codex/Cube), crafted mythics (Sparks).
9. **Make duplicates useful.** Salvage into currency, extract into a collection, upgrade an existing copy (Pom, Codex max-roll upgrade).
10. **Make visible pity that turns failure into progress.** Counters, tokens, guaranteed-after-N. Never silently switch protection off.
11. **Never destroy inputs on a failed upgrade without strong reason.** Lost Ark honing shows the cost. Elden Ring's never-fail upgrades feel fair.
12. **Show crafting odds and ranges.** LE-style transparency turns RNG into informed risk. D4 added result screens for this reason.
13. **Avoid hidden bricking.** If a craft can ruin an item, show the risk beforehand and offer a recovery path (masterwork reset).
14. **Currency should have a use.** Orbs-as-crafting (PoE) build the sink into the economy and make every currency drop a choice.
15. **Hard slot limits generate puzzles.** PoE's 3/3 prefix/suffix and VS's 6/6 weapon/passive slots create meaningful trade-offs from simple rules.
16. **Pairing/recipe rules turn levelling choices into planning** (VS evolutions, Hades duos). Teach recipes through discovery, then show them in a codex.
17. **Built-in downsides make items contextual** (Darkest Dungeon trinkets, D2 ethereal). "Strictly better" items flatten choice.
18. **Base types add a cheap, readable progression axis** (D2 normal/exceptional/elite). A good base can make a white item exciting.
19. **Fixed-source drops are the simplest target farming** (Grim Dawn MIs, D4 boss tables). Players accept low odds when they know where to look.
20. **Diminishing returns on loot-find stats** create gear trade-offs instead of mandatory stacking (D2 MF).
21. **Decide on trade early.** Either balance around it with friction (PoE), make it a per-character choice with self-found compensation (LE), or make it account-bound (D3). An efficient open AH replaces the game (D3).
22. **Presentation is half the reward.** Colour bands, beams, distinct sounds, chest reveals (VS), minimap icons. Cheap to make and very effective.
23. **Ship a loot filter or auto-handling when drop volume is high.** In-game, with good defaults and import/export (LE, PoE + NeverSink).
24. **Remove inventory tedium.** Auto-pickup for materials, separate material storage, salvage-all, junk-selling pets, generous stash. Town trips should be optional.
25. **Budget power creep.** Plan stat squishes, add new *verbs* instead of new multiplier layers, and avoid infinite multiplicative progression (Paragon) dwarfing item choice.
26. **Meta-levers over randomness** (Hades keepsakes, VS reroll/banish/skip, D3 Kadala slot choice) let skilled players shape luck without removing it.
27. **Flavour text gives items identity.** Even small authored items with lore (Souls, DD ancestral trinkets) are remembered longer than procedural rares.
28. **For short-run games (survivors-likes, roguelites), in-run itemization should be choice-based (pick 1 of 3), and meta itemization should be collection-based.** Use persistent unlocks that widen the pool instead of raising raw power, to avoid creep that trivialises runs.

### Master source list
- https://www.pcgamer.com/diablo-3-auction-house-jay-wilson
- https://diablo.fandom.com/wiki/Loot_2.0
- https://www.shacknews.com/article/83266/diablo-3-patch-201-deploys-with-loot-20
- https://www.icy-veins.com/d3/kanais-cube-guide
- https://diablo2.diablowiki.net/Magic_find_diminishing_returns
- https://diablo2.diablowiki.net/Stone_of_Jordan
- https://maxroll.gg/d2/resources/trade-guide
- https://www.icy-veins.com/d4/news/diablo-4-season-4-loot-reborn-patch-notes/
- https://www.windowscentral.com/gaming/diablo-4-campfire-chat-loot-reborn
- https://www.dexerto.com/diablo/diablo-4-itemization-2338349/
- https://www.dexerto.com/diablo/fans-call-diablo-4-season-4-a-new-beginning-2689792/
- https://wp-prod.icy-veins.com/talismans-in-diablo-4-a-new-system-with-old-risks/
- https://maxroll.gg/poe/news/wudijo-path-of-exile-2-interview-with-jonathan-rogers
- https://www.pcgamesn.com/path-of-exile-2/return-of-the-ancients-divine-orbs
- https://maxroll.gg/poe2/resources/runes-and-soul-cores
- https://poe2wiki.net/wiki/Salvage
- https://gamebanshee.com/xfwfq
- https://forum.lastepoch.com/t/trade-development-update-introducing-merchants-guild-and-circle-of-fortune-factions/51994
- https://www.icy-veins.com/last-epoch/crafting-guide
- https://maxroll.gg/last-epoch/resources/loot-filter-guide
- https://www.grimdawn.com/guide/items/components/
- https://forums.crateentertainment.com/t/items-color-and-rarity-full-explanation/35245
- https://maxroll.gg/lost-ark/resources/gear-honing-system
- https://upcomer.com/smilegate-is-killing-lost-ark-through-its-unfair-honing-system
- https://vampire-survivors.fandom.com/wiki/Evolution
- https://primagames.com/tips/hades-what-are-duo-boons-how-get-duo-boons
- https://eldenring.fandom.com/wiki/Ashes_of_War
- https://darkestdungeon.wiki.gg/wiki/Trinkets_(Darkest_Dungeon)
- https://mein-mmo.de/en/wow-legion-bad-luck-protection-legendary,125904
- https://esports.gg/news/hearthstone/hearthstone-pity-timer/
