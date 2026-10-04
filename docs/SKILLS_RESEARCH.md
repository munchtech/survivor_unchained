# Skills, offers and synergies: what the genre's best games do

Research for the skill and upgrade design of Survivor Unchained
(`docs/SKILLS_DESIGN.md` is what we do with it). Game by game first, then
the lessons that cut across them, then the numbers side by side. Figures
are from the games' wikis and data-mined pages where those could be read
(sources at the end); where a page could not be reached and the figure is
from the community's common knowledge, it says "about".

---

## Part one: game by game

### Vampire Survivors (poncle, 2022) — the template

**The draft.** Each level-up offers 3 unique cards drawn from weapons and
passive items, sometimes 4. The fourth card's chance is
`1 − 1/Luck` (Luck 1.0 = 0%, 1.3 = 23%, 2.0 = 50%). Each item has a rarity
weight from 1 to 100; an item's chance in a slot is `rarity / pool weight`
(the whole pool now weighs about 9,500: 8,130 weapons, 1,370 passives).
The common starters (Whip, Knife, Magic Wand, Axe, Santa Water) weigh 100;
joke and novelty items (Bone, Cherry Bomb, Carréllo, La Robba) weigh 1.

**Owned-item bias.** While the inventory is not full the game makes extra
checks that favour items already owned: `ownedChance = 1 + 0.3x − 1/Luck`,
with x = 2 on even levels and 1 on odd ones. In plain terms: on even
levels the game leans hard toward ranking what you have, on odd ones less.
That alternation is a quiet piece of design: it stops the draft from
either spamming new weapons (dilution) or only ever offering ranks
(autopilot).

**Slots.** 6 weapons and 6 passives. Weapons rank to 8, passives to 5.
Once full, nothing new is offered; once everything is maxed, the draft
offers gold or a Floor Chicken (heal). That dead end was felt as a flaw;
**Limit Break** was added so a finished build keeps choosing (per-weapon
stat increments with no cap on Might).

**Evolutions.** A rank-8 weapon plus its partner passive (rank varies,
usually just held) evolves when you open a **treasure chest** that rolls an
evolution, and chests come from bosses that spawn from the 10th minute
(some stages earlier). Examples: Whip + Hollow Heart = Bloody Tear, Magic
Wand + Empty Tome = Holy Wand, Knife + Bracer = Thousand Edge, Fire Wand +
Spinach = Hellfire, Garlic + Pummarola = Soul Eater, King Bible + Spellbinder
= Unholy Vespers. **Unions** fuse two max weapons into one and free a slot
(Peachone + Ebony Wings = Vandalier). The game never teaches a recipe: the
community wiki did. The collection screen shows a recipe only after it has
been done once.

**Chests.** 1, 3 or 5 items (base 50 / 10 / 3% for a boss chest, the
chance multiplied by Luck). An earned evolution comes first; the rest rank
what you own. The first six chests of a save are fixed at 1-1-3-1-1-5 so a
new player sees the big chest early (bad-luck protection for the most
memorable moment in the game).

**Economies.** Reroll, Skip and Banish are bought between runs as
PowerUps: 2 uses per rank, up to 5 ranks each (10 per run at most). Skip
gives a little experience back. **Seal** removes items from the pool
before a run starts, permanently. Rerolls and skips stop working once the
inventory is maxed.

**Pressure.** Enemy waves are authored per minute per stage. Bosses carry
`HP × Level`: their health is multiplied by the player's level when they
spawn, so a strong build meets a sturdier boss (a soft rubber band).
**Curse** (+10% per PowerUp rank) raises enemy health, speed, quantity and
spawn frequency, and players buy it voluntarily for more experience and
gold. At 30:00 the Reaper (Death) arrives with 655,350 HP × level: the run
is over by design.

**Arcanas.** One card at the start and from boss chests at 11:00 and
21:00, chosen from 4 (6 once 23+ are unlocked, with a free reroll). Each
rewrites a rule for a family of weapons or stats (Slash lets every weapon
crit with doubled crit damage; Heart of Fire makes projectiles explode).
They are our great blessings almost exactly.

**What fails.** Some passives are near-dead (Clover is weak once Luck is
not needed; Crown and Stone Mask are taken for their evolutions only); a
handful of evolutions define the meta; and late in a run a full build is
on autopilot until Limit Break. The power fantasy is the point: by 20
minutes the player should be untouchable, and the game sells that as the
reward.

### Brotato (Blobfish, 2022) — the shop instead of the draft

**Two separate choices.** Levelling up offers 4 stat upgrades (primary
stats only), with guaranteed tiers at fixed levels: level 5 always tier 2,
levels 10, 15 and 20 always tier 3, level 25 and every fifth level after
always tier 4. Between waves a shop of 4 items mixes weapons and items.

**Tiers by time and luck.** Tier 2 appears from wave 2, tier 3 from wave
4, tier 4 from wave 8; each tier's chance is
`(chancePerWave × (wave − minWave − 1) + baseChance) × (1 + Luck%)`.
At wave 10 with no luck the shop rolls about 46% tier 1, 40% tier 2, 13%
tier 3, 0.7% tier 4.

**Reroll economy.** Rerolls cost gold: the first costs
`floor(wave × 0.75) + increase`, and each further reroll in the same shop
adds `increase = max(1, floor(0.4 × wave))`. Locking an item is free and
keeps it (and its price) to the next shop. Gold is also experience
(materials do both), so every reroll is a real trade.

**Character bias.** Each character has tags; any item in the shop has a
5% chance to be drawn from the tagged pool (about 3% per slot). Weapons in
the shop come 20% from your own weapons (to make combining possible), 15%
from your weapon classes, 65% from everything. That is a small, legible
lean, never a lock.

**Slots and combining.** 6 weapon slots (some characters fewer or more);
two identical weapons of the same tier combine into the next tier, up to
tier 4. Items are unlimited. Class set bonuses reward owning several
weapons of one class.

**Pressure.** 20 waves of 20–60 s. Enemies gain flat health and damage per
wave; danger levels 1–5 add up to +40% health and damage (not stacking:
danger 5 is +40% in total), elites from danger 2, a boss at wave 20.

**What fails.** Economy builds (harvesting, interest) can dominate if
early waves are too forgiving; some characters are traps for new players
by design (and labelled as such).

### Halls of Torment (Chasing Carrot, 2023) — abilities from the world, traits from the level

**Two channels.** Level-ups offer **traits** (stat ranks and ability
traits). **Abilities** (up to 6) come from Tomes and Scrolls of Mastery
that lie at fixed places in each hall and drop from some elites: the
player goes and gets them, so a new weapon is a decision about the map, not
a card.

**Pool unlocking by level.** Base traits appear from hero level 0, 5, 15,
30 and 50 (tiers I–V); ability traits rank I from level 8 up to rank X by
level 80. A trait rank caps at V, elevated traits at III, ability traits
at X; ranks IX and X double some ability traits' effects.

**Branching upgrades.** Each ability has 3 upgrades and a run may take 2:
the first after its ability trait reaches rank III, the second after rank
VI (an Ability Signet, an item, opens the third). The upgrade is picked
from a scroll pickup, not from the level-up. Upgrades change behaviour
(Ring Blades into Cyclone), which is the HoT equivalent of an evolution
with the branch chosen by the player.

**Pressure.** A 30-minute timer; elites on a schedule (a Lich around
minute 8 in the first hall); the Lord at 30:00. Items (rings, amulets,
armour) are found in the run and some can be extracted to the meta,
which is the game's long tail.

**What works.** The split means the level-up is never a choice between a
new weapon and a stat: weapons come from walking somewhere. Ability
upgrades are gated by investment (trait ranks), which makes them
predictable and plannable.

### 20 Minutes Till Dawn (flanne, 2022) — trees and visible synergies

**Choices.** 5 upgrades per level (4 at the highest darkness levels); some
characters see one more. At level 20 a choice of three upgrades unique to
the starting gun.

**Upgrade trees.** 25 trees, 100 upgrades. Each tree: one tier-1 upgrade,
two tier-2 upgrades, one tier-3. Taking tier 1 unlocks tier 2; either
tier-2 upgrade unlocks tier 3. Investment opens the deep picks; the pool
grows with the build.

**Synergies.** 12 synergies, each needing two (one needs three) specific
upgrades: Frost Fire (Intense Burn + Frostbite: freezing also burns),
Overload (Electro Mastery + Fire Starter: lightning on burning enemies
explodes), Summon Mastery (a trade: +35% summon damage and speed, −35%
bullet damage). They are **listed in the pause menu** from the start, and
drawn with red icons and borders in the draft, so the player can plan.

**What works.** Visible recipes turn the draft into planning instead of
gambling; the trade synergies (Summon Mastery) commit a build rather than
just adding numbers.

### Soulstone Survivors (Game Smithing, 2022) — rarity weights and tag chains

**Rarity first, then card.** A Power's rarity is rolled first on weights
**Common 50, Uncommon 25, Rare 12, Epic 4, Legendary 1** (2%), then a card
of that rarity is drawn. Many cards exist at several rarities with larger
numbers.

**Synergy cards.** Some powers need a combination of skill types to roll
at all (two Swing skills can roll a Swing–Thrust chain); skills carry
damage-type and shape tags that items and powers key off.

**Economies.** Reroll, Banish (removes every rarity of that card for the
run) and **Lock** (keep a card for the next level-up) are unlocked meta
charges.

**What fails.** With dozens of tags, players report not knowing which
numbers apply to which skill; deep runs end in screen-filling builds where
choices stop mattering.

### Deep Rock Galactic: Survivor (Funday, 2024) — overclocks with a way out

**Slots.** 4 weapons. Each weapon adds its own 4 upgrades to the pool.
Level-up cards roll a rarity (common, uncommon, rare, epic, legendary) and
luck lifts it.

**Overclocks.** At weapon levels 6, 12 and 18 the next level-up for that
weapon offers overclocks, two at a time, that rewrite it (elemental
effects, piercing, new behaviour). The **Salvage** button turns down both
and gives an Epic upgrade for that weapon instead. Evolution is therefore
never a forced trap: there is always a strong alternative.

**What works.** Evolution moments land on predictable levels (6/12/18),
the player always sees them coming, and the opt-out keeps agency.

### HoloCure (Kay Yu, 2022) — collabs, eliminate and hold

**The draft.** 4 options per level from weapons, items and stat-ups, by
weight (1–4: weight 4 appears twice as often as weight 2). Stat-ups have
their own weights (SPD Up 4, ATK Up 3, Haste Up 2). When the inventory is
full, food and coins appear instead.

**Economies.** Reroll (up to 10 per run, bought in the shop), Eliminate
(up to 10, once per level-up) and Hold (keep an option for the next
level). **After a reroll, the weights of what was just offered are
reduced**, so a reroll actually shows something new.

**Collabs.** Two max-level basic weapons fuse into a collab weapon at a
**Golden Anvil**. Golden Anvils only start dropping once two weapons that
have a collab are at level 7 or higher (base 1/100 per drop, +1/2000 per
minute). The collab takes one slot and the two ingredients leave the pool
for good: fusion frees a slot (5 free weapon slots, so at most 4
collabs). Super Collabs fuse a collab with a specific item. A collab list
in the menus shows what exists.

**What works.** The anvil appears only once the recipe is nearly done, so
the reward is never offered before it can be used, and never missed once
it can.

### Death Must Die (Realm Archive, 2023) — gods with a cap

**Offers.** On a level-up or chest, a god offers a new power, a level of
one held, or a rarity increase (Novice → Adept → Expert; Master needs
other blessings or items first). A stat on gear, "blessing level-up
chance", shifts offers toward powers already held, which lets the player
tune breadth against depth.

**The cap.** Only 3 gods per run. Once three are met, the pool closes to
them. That forces a build identity by mid-run and stops the end-game draft
being a soup.

**Pressure.** Hand-built bosses and an act structure; gear with affixes
that shift blessing rarity odds (some reach 90–100% legendary chance late),
which is a strong meta lever.

### Rogue: Genesia (Huyogames, 2022) — requirements and nested recipes

**Cards.** 3 Soul Cards per level and after some events; cards include
weapons, mods, enhancements and evolved weapons. A card's rarity scales its
numbers. Banish and reroll exist; an automatic mode takes the rarest card.

**Evolutions.** An evolved weapon needs 2–4 ingredient cards, every
weapon ingredient at max level, and some ingredients need cards of their
own first (Divine Smite needs Absolute Focus and Analysis). The evolved
card then appears in the normal draft; the ingredients leave the pool.
**Soul card level** (the number of cards held) gates stronger cards.

**Structure.** A branching map of fights, shops and events between
stages (Slay the Spire's map in a survivors game).

**What fails.** Deep nested recipes are unreadable without a wiki.

### Magicraft (Wave Game, 2024) — composition, not numbers

Wands with slots and mana; spells are read left to right, so modifiers
(Volley, Multi-Cast) placed before a spell change it and spells can trigger
spells. Spells come from room rewards, chests and shops, with Hades-style
door choices showing the reward type of the next room. The genre's
furthest point toward "the build is a program": late builds that fill the
screen are praised, and balance complaints centre on a few relics that
dominate.

### Spirit Hunters: Infinite Horde (Mattias Nilsson, 2022)

14 base abilities, each with 2 modifiers that change how it behaves
(branching evolution in miniature), 8 heroes with their own passives and
hero ability, and the Divinity Web, a large meta tree with resource and
kill requirements. Builds are defined by which two modifiers you pick on
which abilities; the hero ability makes each hero play differently even
with the same weapons.

### Army of Ruin (Milkstone, 2023)

A Vampire-Survivors structure with evolutions delivered from chests. One
telling patch: chests from the last special boss went from 3 to 5
upgrades, and **a chest that granted an evolution in place of an upgrade
now grants an extra standard upgrade too**: the evolution must not cost
the chest's other rewards, or getting it feels like a loss.

### Boneraiser Minions (Fireblade, 2022) — a summoner's whole game

The player raises minions with bones and souls dropped by enemies; minion
types have roles (melee, missile, hexer, augur) and level into branching
forms. Relics push toward mono-type armies (Deboning Cutlery: every
boneraise has a 4% chance of a free skelly). The player can **bolster the
heroes' forces** for more resources: a chosen curse, like our Dark
Bargain or VS's Curse.

### Vampire Hunters (Gamecraft, 2024)

First-person; up to 14 weapons at once. Level-ups offer weapons, weapon
upgrades, relics and **contracts**: a bonus with a price attached (more
boss health). Contracts put risk and reward into the draft itself.

### Nordic Ashes: Survivors of Ragnarök (Lightning Games, 2023)

Focus on the main weapon; per-character constellation ability trees; 150+
relics with ascensions; a meta tree (Yggdrasil) and character masteries.
Shows the cost of a meta that does too much: reviews call it tame because
power arrives from the meta rather than from in-run choices.

### Megabonk (vedinad, 2025) — the latest large success

4 weapons and 4 tomes; level-up cards carry a rarity (common to
legendary) that scales the size of the upgrade, and Luck shifts the
odds. Shrines in the map offer stat choices. Rarity as **magnitude**
(the same card, bigger) rather than as a separate pool is now the common
pattern (Halls of Torment, Soulstone, Rogue: Genesia, Megabonk).

### Hades (Supergiant, 2020) — the best offer architecture in the field

**Offers.** A god's boon reward offers 3 boons (sometimes fewer). Boons in
the **slots** (Attack, Special, Cast, Dash, Call) are exclusive: one god
per slot, so taking Zeus's attack is turning down Ares's attack forever
this run (a slot is a commitment). Other boons are passive and stack.

**Rarity.** Common, Rare, Epic, Heroic: rarity is magnitude (True Shot
does 70 / 80 / 90 damage at common / rare / epic). Heroic needs an epic
tier-1 boon. Rarity chances are raised by keepsakes and Mirror talents.

**Duo and Legendary boons.** A Duo boon needs a prerequisite boon from each
of two gods (Zeus and Poseidon: Sea Storm); a Legendary needs specific
boons from its own god. Once eligible, they can appear in either god's
next offer. The Codex records each requirement as soon as the boon has
been seen. The rest of the time the boon list shows what a pick would
open ("prerequisite for ..."), which is the single best piece of synergy
communication in the genre.

**Guarantees and economy.** A keepsake guarantees the next god met and
raises rarity; Poms of Power level a boon; Fated Authority/Persuasion give
rerolls of boon offers; Chaos offers a curse now for a stronger blessing
later. Room doors preview reward types, so the player steers the run.

**What works.** Exclusive slots force identity early; duos make
two-god mixes the reward for committing to two; the preview of what a
boon opens makes every pick a plan.

### Diablo IV (Blizzard, 2023) — skill trees and the Codex

One skill point per level (plus renown); each skill ranks to 5 and then
offers an enhancement and a choice of upgrades (originally one of two, now
three major modifiers and further pairs: up to twelve combinations per
skill). A 6-slot action bar. **Aspects** (legendary powers) unlock in the
**Codex of Power** permanently by finishing dungeons or salvaging items,
and are then imprinted onto any suitable gear: acquisition (the codex) is
separate from loadout (what is imprinted). Skill tags (Basic, Core,
Ultimate; damage types) are what aspects and paragon glyphs key off.

### Path of Exile 1 and 2 (Grinding Gear) — skills anyone can use, if they can lift them

Every skill is a gem; anyone can socket any gem, but each has **attribute
requirements** (Strength, Dexterity, Intelligence by colour). Gems level
with experience while socketed. Support gems change the linked skill
(more projectiles, added fire, area) and raise its requirements. In PoE 2
gems drop **uncut** and the player chooses which skill to cut from the
tier's list, constrained only by attributes: the drop is a currency of
choice, not a random skill. The passive tree (1,300+ nodes) is where
archetype identity is built; Ascendancies give 8 points of signature
rules.

### Last Epoch (Eleventh Hour, 2024) — skills that grow with use

Five **specialisation slots** (matching the five-key action bar) open as
the character levels. A specialised skill gains experience as it is used
and levels to 20, each level a point in its own tree. Newly specialised
skills start at a **minimum skill level** that rises at character levels
10, 15, 20, 30 ... 80 and get bonus experience to catch up, so swapping
late is not punished by starting from nothing. Respecing a skill costs its
levels.

### Slay the Spire (Mega Crit, 2019) — the draft as the whole game

**Rewards.** 3 cards after each fight. Rarity: normal fights 60% common,
37% uncommon, 3% rare; elites 50/40/10; bosses always rare. **Pity:** a
rare-chance offset starts at −5% and rises 1% each time a common is
rolled, back to −5% on a rare, capped at +40%: a long run of commons makes
a rare increasingly likely without ever guaranteeing it.

**Skip.** Every reward can be skipped, and skipping is often right (deck
dilution: each card added makes your best cards rarer). Shops sell card
removal. A finished deck is protected by saying no; the game rewards the
discipline (Singing Bowl turns a skip into +2 max HP).

**Archetypes.** Each character's card pool has three or four archetypes
(Ironclad: strength, exhaust, block); key cards appear at uncommon or rare
so an archetype is something you find and commit to, not something you
start with. Relics bend the rules (Snecko Eye) the way great blessings
should.

### Balatro (LocalThunk, 2024) — economy as the choice

5 Joker slots. Shop rerolls cost $5 and +$1 for each further reroll in the
same shop, reset next shop; vouchers lower it. Jokers are about 70% common,
25% uncommon, 5% rare in the shop; legendaries only from one spectral card.
A Joker held never appears again unless you hold Showman (duplicate
prevention). Interest on banked money makes every purchase and reroll a
trade against future income. Booster packs offer 1 of 3 or 5. Slot order
matters (Blueprint copies the joker to its right). The game shows its
whole Joker collection with descriptions, so planning is possible from the
first run.

---

## Part two: what cuts across them

### 1. The offer: how cards are chosen

- **Two dimensions: what, and how much.** The modern pattern rolls a card
  and a rarity separately and lets rarity scale magnitude (Hades,
  Soulstone, Halls of Torment, Megabonk, Rogue: Genesia, DRG: Survivor).
  Vampire Survivors uses rarity only as frequency. Magnitude rarity makes
  a rank-up card exciting without new content.
- **Weights, never locks.** Every game weights; none hard-locks a
  character out of anything except by explicit design (DMD's three-god
  cap, Hades slots). Brotato's character lean is 5% per item; Vampire
  Survivors' owned-item checks alternate between levels. Leans in the
  single-digit to ×2 range are felt over a run without being felt on any
  one card.
- **Owned items get extra weight**, but with care: VS alternates strong
  and weak lean by level; DMD makes it a stat. Without it, a 6-weapon pool
  never maxes anything (dilution); with too much, the draft is autopilot.
- **Breadth closes over time.** Slots fill and the pool narrows (VS,
  HoloCure); a cap on families (DMD's 3 gods) narrows it on purpose. The
  late draft should be about depth (ranks, rarities, evolutions), the early
  draft about breadth (identity).
- **Gate deep cards behind investment**, not behind luck: 20MTD tiers,
  HoT trait ranks, Rogue: Genesia's soul-card level, Hades duo
  prerequisites. The card that completes a plan should appear because the
  plan is nearly complete.

### 2. Guarantees and bad-luck protection

- **Pity counters** (StS: −5% offset, +1% per miss, cap +40%) let rare
  things stay rare on average while bounding droughts.
- **Fixed beats** (Brotato's tier at levels 5/10/15/20/25; DRG overclocks
  at weapon levels 6/12/18; VS's first chests 1-1-3-1-1-5; Arcanas at
  0:00, 11:00, 21:00) make the big moments predictable so players plan
  toward them.
- **Never offer the reward before it can be used; never miss it once it
  can** (HoloCure's Golden Anvil drops only after two eligible weapons
  reach level 7; VS evolutions take priority in a chest).
- **A guaranteed useful card:** most games quietly guarantee at least one
  card that advances the build (VS ranks owned items; Brotato always shows
  a weapon you can combine 20% of the time).

### 3. Reroll, banish, skip, lock

| Game | Reroll | Banish | Skip | Lock / Hold | Cost model |
|---|---|---|---|---|---|
| Vampire Survivors | up to 10 | up to 10 | up to 10 (gives XP) | Seal (pre-run) | meta PowerUps, 2 per rank |
| HoloCure | up to 10 (reduces shown weights) | Eliminate 10, once per level | — | Hold | meta shop |
| Soulstone Survivors | charges | removes all rarities of a card | — | Lock | meta |
| Brotato | gold, rising per reroll and per wave | — | — | Lock (free) | in-run currency |
| Balatro | $5, +$1 each, resets per shop | — | skip blinds for tags | — | in-run currency with interest |
| Slay the Spire | — | removal at shops (paid) | always free | — | — |
| Hades | Fated Persuasion (meta) | — | — | keepsakes steer | meta |

The lesson is not one number but a principle: **the tools should be scarce
enough to be decisions and plentiful enough to be used.** Ten per run is
the genre's comfortable ceiling for free charges; an in-run currency makes
every reroll a trade. A skip that returns something (VS: experience; StS
Singing Bowl: health) is the only way skipping is used by players who are
not experts. Rerolls must show new cards (HoloCure lowers the weights of
what was just shown).

### 4. Slots and the weapon/passive split

| Game | Active | Passive | Notes |
|---|---|---|---|
| Vampire Survivors | 6 | 6 | unions free a slot |
| HoloCure | 6 (5 free) | 6 | collabs free a slot |
| Halls of Torment | 6 abilities | traits unlimited | abilities from the world |
| DRG: Survivor | 4 | stats unlimited | overclocks per weapon |
| Megabonk | 4 | 4 tomes | |
| Brotato | 6 (varies) | unlimited | |
| Hades | 5 slot boons | unlimited | slot exclusivity |
| Balatro | 5 jokers | — | order matters |
| Diablo IV / Last Epoch | 6 / 5 | trees | |

Six active and six passive is the genre's default because a 30-minute run
yields 60–100 level-ups, enough to max six weapons (48 ranks) and fill the
passives, then evolve. Fewer slots (4) mean each pick matters more and
evolutions come sooner; more (14) mean breadth over depth.

### 5. Evolutions and synergy discoverability

- **Recipe shapes:** weapon + passive (VS), weapon + weapon fusion
  (HoloCure collabs, VS unions), multi-ingredient (Rogue: Genesia),
  investment-gated branch (HoT, DRG overclocks), cross-family (Hades duos),
  pairs of upgrades (20MTD synergies).
- **Branching beats destiny**: HoT (2 of 3), DRG (1 of 2 or salvage),
  Spirit Hunters (2 modifiers), Hades (which god's duo). A choice at the
  evolution is a second decision on top of the recipe.
- **Discoverability spectrum:** hidden (VS: wiki-driven, magic on the
  first run, homework after) → recorded once seen (VS collection, Hades
  codex) → shown from the start (20MTD pause menu, HoloCure collab list,
  Balatro collection). Players of 2024–25 expect at least "recorded once
  seen" plus a hint on the card that would complete a recipe. Hades's
  "this opens ..." line on a boon is the gold standard.
- **Timing:** VS gates evolutions behind chests after 10 minutes, so the
  first half of a run is building and the second is cashing in. DRG puts
  them at fixed weapon levels. Both make the moment predictable.
- **Never cost the player:** Army of Ruin's patch (an evolution should not
  replace a chest's upgrade) and DRG's Salvage show that the evolution must
  be pure gain or have a clean alternative.

### 6. Build archetypes and their counters

Archetypes in every game in this list group by **shape** (projectile,
area, melee, summon, aura, beam/chain) and by **status** (burn, bleed,
frost, poison, shock, mark), with **defence** (armour, regen, block,
thorns) and **economy** (pickup, luck, experience) as support. The counter
side is the enemy roster: shields that stop frontal projectiles, fast
flankers against slow area, ranged enemies against melee, swarms against
single-target, bosses against crowd damage. Good games make sure each
archetype has a weak matchup and an answer to it (Hades: a cast for range,
a dash for melee).

### 7. In-run against meta progression

The run should carry the fantasy; the meta should widen choice and
smooth the floor. VS's PowerUps and Brotato's characters mostly widen;
Nordic Ashes and some others let the meta carry the power, and are called
tame for it. The meta's best levers are the ones that change the draft
(rerolls, banish, seal, a fourth card, rarity) rather than raw stats.

### 8. Scaling against the horde

- VS: authored waves and bosses with HP × level (a soft rubber band);
  Curse as voluntary difficulty; a hard stop at 30:00.
- Brotato: linear health per wave plus a danger multiplier.
- HoT: hall levels and a Lord at 30:00; elites on a schedule.
- Everywhere: the player's power curve must outrun the horde's in the
  middle (the fantasy) and meet it at the end (the tension). The usual
  shape is a horde that grows roughly linearly in count and polynomially
  in health, and a player whose damage grows exponentially through ranks,
  passives and evolutions until the build is complete, then flattens.

### 9. Time to kill and decision density

- The genre's rhythm: a fodder enemy dies to one or two hits for most of
  the run (time to kill under half a second), elites take seconds, a boss
  takes 30–90 seconds. When fodder starts taking several seconds, the
  run is failing.
- **Decision density**: VS gives about 2–3 level-ups a minute early and
  under 1 late; StS gives a reward every fight; Hades gives a boon every
  room or two. Above about 3 a minute, choices blur into clicking; below
  about 0.5, the build stalls.
- **Choice quality**: a good offer has at least one card that advances the
  current plan and at least one that tempts a change of plan. Three cards
  of which one is obviously right is autopilot; three cards of which none
  fits is a feel-bad. Skip and reroll exist to fix both.

### 10. Failure modes seen across the genre

1. **Dilution**: too many new weapons offered, nothing reaches rank 8,
   no evolutions (the most common complaint about bad survivors-likes).
2. **Autopilot**: a complete build, and a draft that offers only gold or
   heal (VS before Limit Break).
3. **Dead picks**: cards nobody takes (pickup radius, luck) unless they
   evolve something; they waste a slot in the offer and train the player
   to ignore a category.
4. **Traps**: cards that look good and do nothing for the build (projectile
   count on a melee build; area on single-target). Tag-aware offers and
   text that says what it affects in this build fix most of these.
5. **Dominant strategies**: one evolution or one blessing that beats all
   others (Hades: Aspect of Guan Yu for a while; VS: a handful of
   evolutions); a defence stat that makes the player unkillable.
6. **Invisible synergies**: recipes nobody can find without a wiki.
7. **Forced evolutions**: an evolution offered with no opt-out, or one that
   removes something the player liked.
8. **Rubber band too tight**: if enemy health scales with player power,
   choices stop mattering (VS limits HP × level to bosses for this reason).
9. **Same run every time**: a calling or character that always ends in the
   same build because the draft funnels it.

### 11. Keeping the 20th run fresh

- Characters with different starts and rules (VS, Brotato, Spirit
  Hunters' hero abilities).
- Run-level rule changes chosen at the start (Arcanas, Hades keepsakes,
  Balatro decks and stakes).
- Map conditions and difficulty dials chosen by the player (Brotato
  danger, VS Curse, HoT's hall levels, our oaths).
- A collection to complete (VS evolutions found, Hades codex, Balatro
  collection), and secrets (VS unlocks).
- Branching evolutions so the same weapon can end two ways.

---

## Part three: the numbers side by side

| | Choices | Rarity tiers and odds | Pity / guarantees | Rerolls etc. per run | Active / passive slots | Max rank |
|---|---|---|---|---|---|---|
| Vampire Survivors | 3, 4th at `1 − 1/Luck` | weight 1–100 per item | first chests 1-1-3-1-1-5; evolutions first in chests | ≤10 reroll / skip / banish | 6 / 6 | 8 / 5 |
| Brotato | 4 | tiers 1–4, by wave × (1 + luck) | tier 2 at lv 5; tier 3 at 10/15/20; tier 4 at 25+ | gold, rising | 6 / ∞ | tier 4 |
| Halls of Torment | 3 | rarity on traits | ability upgrades at trait rank III, VI | meta | 6 / ∞ | trait V, ability X |
| 20 Minutes Till Dawn | 5 (4 late) | — | tree tiers unlock by investment | — | 1 gun / ∞ | tree of 4 |
| Soulstone Survivors | 3+ | 50 / 25 / 12 / 4 / 1 | synergy cards need skill pairs | reroll, banish, lock | 6 / ∞ | — |
| DRG: Survivor | 3 | 5 tiers, luck | overclocks at weapon lv 6/12/18, salvage | meta | 4 / ∞ | 18+ |
| HoloCure | 4 | weights 1–4 | anvil only when collab is ready | ≤10 reroll, ≤10 eliminate, hold | 6 / 6 | 7 |
| Death Must Die | 3 | Novice / Adept / Expert / Master | Master needs prerequisites | reroll, alteration | per god slot, 3 gods | 5–10 |
| Hades | 3 | Common / Rare / Epic / Heroic | keepsake guarantees a god | Fated Persuasion | 5 slots / ∞ | Pom levels |
| Slay the Spire | 3 | 60 / 37 / 3 (elite 50/40/10) | rare offset −5%, +1% per common, ≤+40% | skip always | deck | upgrade 1 |
| Balatro | shop 2 + packs | ~70 / 25 / 5 | no duplicates | $5, +$1 each | 5 jokers | — |

---

## Sources

- Vampire Survivors wiki: [Level up](https://vampire.survivors.wiki/w/Level_up), [Evolution](https://vampire.survivors.wiki/w/Evolution), [Treasure Chest](https://vampire.survivors.wiki/w/Treasure_Chest), [PowerUps](https://vampire.survivors.wiki/w/PowerUps), [Arcana](https://vampire.survivors.wiki/w/Arcana), [Limit Break](https://vampire.survivors.wiki/w/Limit_Break), [Boss](https://vampire.survivors.wiki/w/Boss); [The Conversation on its reward design](https://theconversation.com/vampire-survivors-how-developers-used-gambling-psychology-to-create-a-bafta-winning-game-203613)
- Brotato wiki: [Shop](https://brotato.wiki.spellsandguns.com/Shop), [Upgrades](https://brotato.wiki.spellsandguns.com/Upgrades), [Dangers](https://brotato.wiki.spellsandguns.com/Dangers), [Enemies](https://brotato.wiki.spellsandguns.com/Enemies)
- Halls of Torment: [Traits](https://hot.fandom.com/wiki/Traits), [Abilities](https://hot.fandom.com/wiki/Abilities), [Steam guide](https://steamcommunity.com/sharedfiles/filedetails/?id=3005633351)
- 20 Minutes Till Dawn wiki: [Upgrades](https://20minutestilldawn.wiki.gg/wiki/Upgrades), [Synergies](https://20minutestilldawn.wiki.gg/wiki/Synergies)
- Soulstone Survivors: [wiki, Powers](https://soulstone-survivors.fandom.com/wiki/Powers) and Steam discussions
- Deep Rock Galactic: Survivor: [Prima Games on overclocks](https://primagames.com/gaming/how-to-get-and-use-overclock-weapons-in-deep-rock-galactic-survivor), Steam discussions
- HoloCure wiki: [Level Up](https://holocure.wiki.gg/wiki/Level_Up), [Collab](https://holocure.wiki.gg/wiki/Collab)
- Death Must Die: [Steam discussions](https://steamcommunity.com/app/2334730/discussions/0/4364628251563423885)
- Rogue: Genesia: [Destructoid on evolutions](https://www.destructoid.com/how-to-evolve-any-weapon-in-rogue-genesia/)
- Magicraft: [Wikipedia](https://en.wikipedia.org/wiki/Magicraft), [Rogueliker review](https://rogueliker.com/magicraft-review/)
- Spirit Hunters: Infinite Horde: [Game Developer press release](https://gamedeveloper.com/press-release/spirit-hunters-infinite-horde-out-now)
- Army of Ruin: [Early Access update #9](https://www.milkstonestudios.com/?p=4497)
- Boneraiser Minions: [Steam store page](https://store.steampowered.com/app/1944570)
- Vampire Hunters: [Games Asylum review](https://www.gamesasylum.com/2024/10/30/vampire-hunters-review/)
- Nordic Ashes: [GamingOnLinux](https://gamingonlinux.com/2023/02/nordic-ashes-survivors-of-ragnarok-norse-horde-survival-rogue-lite)
- Megabonk: [Dexerto, Luck](https://www.dexerto.com/wikis/megabonk/what-is-luck/)
- Hades: [Prima Games on heroic, legendary and duo boons](https://primagames.com/?p=313643)
- Diablo IV: [Icy Veins on the reworked skill trees](https://www.icy-veins.com/d4/news/diablo-4s-reworked-skill-trees-a-massive-upgrade/), [Prima on the Codex of Power](https://primagames.com/tips/diablo-4-codex-of-power-and-aspects-explained)
- Path of Exile 2: [poe2wiki, Skill gem](https://poe2wiki.net/wiki/Skill_gem), [Mobalytics on the gem system](https://mobalytics.gg/poe-2/guides/skill-gem-system)
- Last Epoch: [support, Skill Specialization](https://support.lastepoch.com/hc/en-us/articles/46363203944859-Skill-Specialization), [Maxroll](https://maxroll.gg/last-epoch/resources/passives-and-skills)
- Slay the Spire: [wiki, Card Rewards](https://slay-the-spire.fandom.com/wiki/Card_Rewards)
- Balatro: [wiki, Showman](https://balatrogame.fandom.com/wiki/Showman), [Pocket Gamer joker list](https://www.pocketgamer.com/balatro/joker-tier-list/)
