# Research: how other games build enemy variety and counterplay

The sources behind the bestiary. Each finding names the game, the fact and
where it came from; the lessons drawn for this game are at the end and are
cited from the other files as "RESEARCH.md, lesson N". Researched in October
2026 from wikis, patch notes, developer interviews and player discussion.
Wiki numbers drift with patches; anything not confirmed by a source fetched
here is marked *(unverified)*. Game-feel research (impact, sound, reward
pacing) is in `docs/feel/RESEARCH.md` and is not repeated; loot and
itemization research is in `docs/items/RESEARCH.md`.

## 1. Survivors-likes

### Vampire Survivors
- Enemies come in **waves, one a minute**; each wave sets a minimum count
  and a spawn interval, and the game tops the field up to the minimum.
  Periodic spawning stops at **300 alive**. [wiki](https://vampire-survivors.fandom.com/wiki/Enemies)
- **Curse** (base 100%) raises wave frequency and size and enemy speed and
  health by its percentage, with no cap; it is a dial the player turns for
  more experience and gold (Skull O'Maniac, cursed items). [wiki](https://vampire.survivors.wiki/w/Curse), [wiki](https://vampire-survivors.fandom.com/wiki/Curse)
- Ordinary enemies only walk at the player. The challenge is density and
  the clock, not individual enemies. *(design reading)*

### Brotato
- Roles are explicit in the roster: chasers (Baby Alien, Charger, Bruiser,
  Helmet Alien), ranged (the Spitter, which "runs away from the character if
  too close"), and support. [wiki](https://brotato.wiki.spellsandguns.com/Enemies)
- The **Buffer** gives other enemies +150% health, +25% damage and +50%
  speed: the priority target. The **Healer** walks among enemies healing
  them. The **Spawner** releases three Junkie Aliens on death. The
  **Looter** flees and drops a crate and materials when killed: a "chase me
  for reward" enemy. The **Slasher Egg** is stationary and hatches after
  5 s: kill it before the timer. [wiki](https://brotato.wiki.spellsandguns.com/Enemies)
- Elites (Rhino, Butcher, Monk, Mother...) come on set waves and drop
  legendary loot. [wiki](https://brotato.wiki.spellsandguns.com/Enemies)
- **Danger levels** are cumulative, and the first step is *new enemy
  types*, not stats: D1 new enemies; D2 elites or hordes on wave 11 or 12;
  D3 +12% health and damage; D4 +26% and elites on three waves; D5 +40% and
  two bosses at once. Variety is treated as difficulty. [wiki](https://brotato.wiki.spellsandguns.com/Dangers)

### Halls of Torment
- **Blue-outlined elites** spawn at the same time every run on a level and
  always drop gold and a scroll: predictable milestones. **Yellow-outlined
  champions** spawn at fixed times but with random type, loot and
  **modifiers**. [Steam](https://steamcommunity.com/app/2218750/discussions/0/4360121922350543981/?l=english)
- Champion abilities are out of type (summoning skeletons, dashing across
  the screen leaving fire). [Prima](https://primagames.com/gaming/halls-of-torment-what-is-agony-mode)
- **Agony** fills faster the faster the player kills; each level raises
  enemy count, health and experience: a self-balancing rubber band.
  [Prima](https://primagames.com/gaming/halls-of-torment-what-is-agony-mode)

### 20 Minutes Till Dawn
- Elites are **red-outlined**, with much more health, otherwise behaving as
  normal. **Darkness** levels each add one legible modifier (D1 small
  enemies spawn more often; D2 they have more health). [wiki](https://20-minutes-till-dawn.fandom.com/wiki/Enemies)

### Soulstone Survivors
- Opt-in **curses** for more reward: Lifeless Void (−12% healing), Reckless
  Goblins (explosive goblins earlier), Unholy Reinforcements (elites 10% more
  often), Revenge of the Void (10% chance on a kill of a meteor near you),
  Clone Army (+1 elite at once). The on-death punisher exists only as an
  opt-in. [Steam](https://steamcommunity.com/app/2066020/discussions/0/4522261213595113793)

### Deep Rock Galactic: Survivor
- Five hazard levels per biome; **mutators** in four flavours: environment
  ("The Floor is Lava", "Dark Caves"), enemy buffs ("Omega Elites": +50%
  health, +33% damage, +25% speed), player debuffs ("Slow Healer") and shop.
  [wiki](https://deeprockgalactic.wiki.gg/wiki/Survivor:Biome)
- In the DRG universe elites are larger, wear a red aura and an "Elite" tag,
  and arrive with an explicit "Elite Threat" warning. [wiki](https://deeprockgalactic.wiki.gg/wiki/Enemies)

### Death Must Die
- Difficulty is chosen at the Star Crux; modifiers raise item rewards. The
  community says reward stops scaling around difficulty 30 of 100, and calls
  "−60% movement speed after attacking" the most build-dependent modifier
  (it punishes melee hardest). [Prima](https://primagames.com/?p=210769),
  [Steam](https://steamcommunity.com/app/2334730/discussions/0/4355620416673301532)
- Threat waves are scripted at fixed times (skeleton floods at 0:00, large
  enemies at 10:00, flyers at 11:00). [Steam](https://steamcommunity.com/app/2334730/discussions/0/4355620416673301532)

### HoloCure, Megabonk
- HoloCure mixes fodder with "Mega" variants at set times; hard stages make
  the same enemies stronger and faster. [wiki](https://holocure.wiki.gg/wiki/Stage_1)
- Megabonk's run-wide **Difficulty** raises spawn rate, group size and
  damage **and** experience and coin; players raise it on purpose at Greed
  Shrines to farm. [Dexerto](https://www.dexerto.com/wikis/megabonk/what-does-difficulty-do)

## 2. ARPGs

### Diablo II
- Champion packs are two to four; one may be Berserker, Fanatic, Ghostly or
  Possessed. Each type is **one readable verb**: Berserker hits far harder,
  Fanatic is very fast, Ghostly resists 80% of damage, Possessed has ×12
  health. [PureDiablo](https://www.purediablo.com/d2wiki/Champion)
- Unique monster abilities include Extra Fast, Fire Enchanted (a death
  explosion), **Lightning Enchanted** (bolts released *when hit*, notorious
  against fast attackers), Multishot, Stone Skin and **Aura Enchanted**
  (Might, Holy Freeze, Conviction, Fanaticism). [Battle.net](https://classic.battle.net/diablo2exp/monsters/bonus.shtml)
- **Immunity** is resistance above 99%; in Hell nearly every monster is
  immune to something. Conviction and Lower Resist work at a fifth against
  immunes; magic immunity cannot be broken. Diablo II Resurrected (2.5)
  added **Sunder Charms** that set an immunity to 95%, two decades later, to
  rescue single-element builds. [Maxroll](https://maxroll.gg/d2/resources/immunities),
  [PureDiablo](https://purediablo.com/?p=7262)

### Diablo III
- Elite affix count grows with level: one, then two at 30, three at 50,
  four at 60. Champion-only affixes are pack-wide (Avenger, Health Link);
  rare-only include Horde, Missile Dampening and Juggernaut.
  [Maxroll](https://maxroll.gg/d3/resources/elite-affixes)
- **Molten** leaves a fire trail and explodes three seconds after death: a
  telegraphed on-death effect. **Waller** is "one of the worst affixes";
  **Jailer** roots for 2.5 s; **Vortex** pulls the player.
  [Maxroll](https://maxroll.gg/d3/resources/elite-affixes)
- **Invulnerable Minions** was removed in patch 1.0.4. [Gameranx](https://gameranx.com/updates/id/8493/article/diablo-3-patch-1-0-4-brings-significant-improvements-to-skills-runes-weapons-witch-doctors-and-changes-to-difficulty/)
- **Reflects Damage** was reworked from a flat to a percentage reflect in
  2.0.1 and later reduced to a weak returning projectile. [Blizzplanet](https://blizzplanet.substack.com/p/diablo-iii-reaper-of-souls-2-0-4-v2-0-2-23119-patch-notes),
  [GameBanshee](https://www.gamebanshee.com/k83h4)
- **Torment** rewards scale steeply and openly: T1 +300% experience and
  gold and +15% legendaries; T6 +1600% / +131%; T13 +8200% / +625%.
  [wiki](https://diablo.fandom.com/wiki/Torment_(difficulty))
- The treasure goblin flees, sheds loot as it runs and escapes through a
  portal if not killed; its cackle "sparks a Pavlovian response" and players
  drop everything to chase it. [PC Gamer](https://www.pcgamer.com/au/crushing-diablo-3s-treasure-goblins)

### Diablo IV
- **Suppressor** put a dome on an elite that blocked all ranged damage,
  originally with no timer, and was hated by projectile builds; **Vampiric**
  healed the elite and was hated by low-burst builds.
  [AFK Gaming](https://afkgaming.com/gaming/diablo-4/nightmare-sigil-affixes-and-why-players-hate-the-suppressor-affix-in-diablo-4)
- Patch 1.3.1 time-boxed Suppressor (6 s up, at least 6 s down) and halved
  Vampiric's heal. [Wowhead](https://www.wowhead.com/news=337450/major-changes-to-suppressor-and-vampiric-affixes-in-patch-1-3-1-diablo-4)
- Patch 1.1.1 removed three Nightmare Dungeon affixes after feedback,
  including **Backstabbers** (up to +150% damage from behind).
  [Sportskeeda](https://www.sportskeeda.com/mmo/diablo-4-patch-1-1-1-set-remove-three-nightmare-dungeon-affixes)
- **Teleporter** lands on the player after a 0.33 s cue: "visually and
  acoustically barely counterable, a real reaction trap". **Waller** traps
  the player in a U of walls for 7 s. [GameStar](https://www.gamestar.de/artikel/diablo-4-monster-affixe-guide-tipps,3394762.html),
  [vhpg](https://www.vhpg.com/diablo-4-elite-affixes/teleporter.html)

### Path of Exile 1 and 2
- Players reroll or skip maps with **Reflect**, **Cannot Leech**, **no
  regeneration** or **−max resistances**: the mods make no gameplay, only
  avoidance. [Maxroll](https://maxroll.gg/poe/getting-started/how-to-roll-maps)
- Reflect punishes success (more damage, more self-damage) and is invisible
  until the survivor dies; the developers had to post a PSA on the
  arithmetic. [devtrackers](https://devtrackers.gg/pathofexile/p/c041739c-psa-do-not-run-reflect-maps-with-less-than-130-reduced-reflected-damage-taken)
- Chris Wilson's **Archnemesis** postmortem (3.17): mods were too strong,
  **too many stacked on one rare**, misunderstood (Mana Siphoner's
  donut-shaped area: "If you get close enough, it doesn't apply to you"),
  and some unfairly punished specific builds. [devtrackers](https://devtrackers.gg/pathofexile/p/fcf91244-what-s-next-for-archnemesis-modifiers-part-3-and-list-of-modifiers)
- In Path of Exile 2, **Proximal Tangibility** (only hurt from close range)
  together with a mana-siphon aura was reported as broken: a mod that forces
  melee paired with one that punishes melee. [Steam](https://steamcommunity.com/app/2694490/discussions/0/598514944991864195)

### Last Epoch
- **Corruption** is the difficulty and reward dial: enemy health and damage
  up, experience, rarity and unique chances up, without limit.
  [Maxroll](https://maxroll.gg/last-epoch/monolith/empowered-guide)
- At corruption 850 a hit is about 4,500 against ~30% more player health
  than at 200; the reply: "you aren't meant to be able to handle high
  corruption. It's a scaling difficulty bar that the player has full control
  over." [forum](https://forum.lastepoch.com/t/how-high-corruption-removes-the-desire-to-play/47806)

### Grim Dawn
- Killing a faction raises **infamy**: Despised brings more champions,
  Hated more heroes, Nemesis an ultra-boss. Play style escalates the
  roster. [Grim Dawn](https://www.grimdawn.com/guide/character/factions/)
- Nemeses are themed against builds (Kubakabra resists 96% vitality).
  [Steam](https://steamcommunity.com/app/219990/discussions/0/3811786028490673097)
- Hero monsters drop **infrequents** tied to them: a reason to hunt a named
  elite. [Crate](https://forums.crateentertainment.com/t/grim-dawn-version-1-1-8-0/103853)
- Ultimate's resistances were cut about 5% so resistance walls stop
  hard-gating. [Crate](https://forums.crateentertainment.com/t/grim-dawn-version-1-1-7-0/100418)

## 3. Action games and roguelites

### Hades: the Pact of Punishment
- Fifteen conditions, each a single legible rule with ranks and a heat
  cost: **Hard Labor** (+20% enemy damage a rank, 5 ranks), **Lasting
  Consequences** (−25% healing a rank), **Jury Summons** (+20% enemies a
  rank), **Calisthenics Program** (+15% health), **Benefits Package**
  (armoured enemies gain a perk, 2 and 3 heat), **Middle Management** (+1
  elite), **Forced Overtime** (+20% speed, 3 heat a rank), **Heightened
  Security** (traps +400%), **Damage Control** (enemies gain a shield that
  absorbs one hit), **Approval Process** (one fewer boon choice), **Tight
  Deadline** (a timer per region), and others. [RPG Site](https://www.rpgsite.net/feature/10287-hades-pact-of-punishment-heat-modifiers-and-how-to-maximize-your-rewards),
  [Prima](https://primagames.com/gaming/hades-guide-pact-of-punishment-modifiers-heat)
- Each new heat total earned re-pays the bosses' rare currencies, so
  rewards follow *new* heat, not repeated heat. [RPG Site](https://www.rpgsite.net/feature/10287-hades-pact-of-punishment-heat-modifiers-and-how-to-maximize-your-rewards)
- Heat costs are not proportional to the stat change: +20% speed costs 3,
  +20% damage costs 1. The cost is priced by *how much harder it plays*, not
  by its number. *(design reading of the table)*

### Doom Eternal
- Demons are **fodder, heavy and super heavy**; fodder dies in a couple of
  shots, super heavies are near-bosses. [Red Bull](https://www.redbull.com/ie-en/doom-eternal-beginner-tips)
- Hugo Martin calls the combat "a hardcore, fast-paced game of chess".
  [GameSpot](https://www.gamespot.com/articles/doom-eternal-will-have-intense-boss-fights-heres-a/1100-6474375/)
- **Weak points** (the Mancubus's arm cannons, the Arachnotron's turret)
  can be shot off with the precision bolt, removing an attack.
  [Doom Wiki](https://doomwiki.org/wiki/Destructible_demons),
  [Doom Wiki](https://doomwiki.org/wiki/Mancubus_(Doom_Eternal))
- Martin wants players "to think about which weapon they're using at all
  times", but also: "We don't want you constantly going point blank,
  because that gets repetitive. Sometimes, opportunistically, hanging back,
  using the scope, and popping a head can add that kind of variety."
  [PCGamesN](https://www.pcgamesn.com/doom-eternal/demons-video)
- The Marauder, a hard skill check that demands one answer, divided players
  enough that the director defended it publicly. [PC Gamer](https://www.pcgamer.com/uk/doom-eternals-director-says-the-marauder-is-good-actually/)

### Risk of Rain 2
- Difficulty rises with **time**: stronger and more numerous enemies; Drizzle
  scales at 50% of the pace, Monsoon at 150%. [wiki](https://riskofrain2.wiki.gg/wiki/Difficulty)
- **Elites** are one verb each: Blazing (a fire trail, hits burn), Glacial
  (hits slow; dies into a freezing blast), Overloading (hits drop delayed
  bombs, half health as shield). Tier 2 elites come later: **Malachite**
  (hits disable healing, throws urchins), **Celestine** (cloaks allies, hits
  slow 80%). [GameWith](https://gamewith.net/riskofrain2/article/show/8695),
  [Steam](https://steamcommunity.com/app/632360/discussions/0/4764333224357680685)
- Celestine's cloak makes allies immune to auto-targeting items though not
  to area: an anti-auto-aim affix with an area answer. [Steam](https://steamcommunity.com/app/632360/discussions/0/4764333224357680685)

### Enter the Gungeon
- Hit detection was pixel-perfect, but many projectiles had custom offsets
  so that anything that *looked* like a hit was one; the sequel shrank
  hitboxes for more forgiving overlap. Readability is an agreement between
  what is drawn and what hurts. [Game Developer](https://gamasutra.com/design/building-i-enter-the-gungeon-i-s-dungeon-climbing-spin-off-i-exit-the-gungeon-i-)

### Dead Cells
- At five Boss Stem Cells, **Malaise** rises over time: enemies grow faster
  and stronger and more of them turn elite; killing lowers it (a mob 1.8, an
  elite 25, a boss 250). The pressure rewards killing quickly rather than
  avoiding. [wiki](https://deadcells.fandom.com/wiki/Malaise)

### Left 4 Dead
- Each special infected is one role: the Boomer (bile that summons the
  horde), the Smoker (drags a survivor away), the Hunter (pounces and pins),
  the Tank (overwhelming force), the Witch (punishes disturbing her).
  [Dread Central](https://www.dreadcentral.com/editorials/493467/monster-mania-left-4-deads-special-infected-are-perfected-simplicity/)
- Each has a **sound before it acts**: the Hunter's growl, the Smoker's
  cough, the Boomer's gurgle, the Charger's roar. [Dread Central](https://www.dreadcentral.com/editorials/493467/monster-mania-left-4-deads-special-infected-are-perfected-simplicity/)
- Mike Booth's **AI Director** paces the experience, sending hordes or
  specials into lulls. [Wikipedia](https://en.wikipedia.org/wiki/Mike_Booth),
  [Game Developer](https://www.gamedeveloper.com/design/the-discomfort-zone-the-hidden-potential-of-valve-s-ai-director)

### Vermintide 2 and Darktide
- Every special has a clear, loud audio cue whenever it is near; Darktide
  players complained when the Trapper's and Bomber's cues were missing or
  their direction was wrong. [Steam](https://steamcommunity.com/app/1361210/discussions/0/4148446452673336842)
- Vermintide 2 patch 1.04 removed the higher chance of **disabler**
  specials on the top difficulties and lengthened the gaps between specials.
  [GameWatcher](https://www.gamewatcher.com/2018-20-03-warhammer-vermintide-2-patch-notes-patch-1-04-released)

### StarCraft: hard and soft counters
- A hard counter is an interaction one side practically cannot win; a soft
  ("muddy") counter is an advantage the other side can still overcome.
  Dustin Browder: StarCraft has both; Archons, Ultralisks and Firebats were
  hard counters, Dragoons, Hydralisks, Zealots and Marines muddy ones.
  [GameStar](https://www.gamestar.de/interviews/2313674/starcraft_2_p5.html),
  [Wayward Strategy](https://waywardstrategy.com/2021/07/27/hard-counters/)
- In an RTS, hard counters are tolerable because the player *chooses* what
  to build after scouting. In a survivors game the build is drafted at
  random, so a hard counter there punishes a choice the player did not
  make. *(design reading)*

### Attention
- People can track about **four** moving objects at once (Pylyshyn and
  Storm's multiple-object-tracking task, 1988, and the studies after it);
  with slower, more distinct objects the number rises to eight or nine.
  [Wikipedia](https://en.wikipedia.org/wiki/Multiple_object_tracking),
  [Alvarez and Franconeri 2007](https://visualcognition.psych.northwestern.edu/publications/AlvarezTracking2007.pdf)

## 4. Themes across the sources

**Roles.** Every game with memorable enemies gives each enemy *one* job and
one tell: Diablo II's champion types, Risk of Rain's elites, Left 4 Dead's
specials, Brotato's buffer and looter. Doom's fodder/heavy/super-heavy is a
role by toughness; Left 4 Dead's is a role by verb. Both are needed.

**Readability.** Outlines and colour mark elites in nearly every
survivors-like (Halls of Torment's blue and yellow, 20 Minutes Till Dawn's
red, DRG's red aura and "Elite Threat"). Sound marks specials in the
co-op shooters, and players notice at once when a cue is missing. The
failures are short or invisible telegraphs (Diablo IV's 0.33 s Teleporter)
and effects that do not match what hurts (Gungeon's offsets were the fix).

**Hard and soft counters.** The hard counters players hate are the ones
aimed at a whole build: Diablo II's immunities, Diablo IV's Suppressor
(ranged) and Vampiric (low burst), Path of Exile's reflect and cannot-leech.
Every one of them was later softened, time-boxed or removed. The soft
counters that survive (armour, resistances, Celestine's area answer) slow a
build without stopping it.

**Build checks and skill checks.** A build check asks "did you bring X?";
a skill check asks "can you do X now?". Players accept build checks they
chose (a Hades heat condition, a Last Epoch corruption level, a Soulstone
curse) and resent ones imposed on them (reflect maps, immunities). Skill
checks are accepted when the tell is fair (Doom's weak points) and resented
when it is not (Diablo IV's Teleporter).

**Opt-in difficulty.** Almost every game here lets the player turn the
dial and pays openly for it: Vampire Survivors' Curse, Megabonk's
Difficulty, Hades' heat, Diablo III's Torment table, Last Epoch's
corruption, Brotato's Danger, Soulstone's curses. The best ones price each
condition by how much harder it plays (Hades), pay for *new* difficulty
rather than repeats (Hades' re-earned currencies), and say plainly that the
top is not meant to be beaten (Last Epoch).

**Tedium and thrill.** Tedium: invisible on-death effects, reflect,
immunity phases and invulnerable minions, enemies that flee while shooting,
walls that trap, long-healing elites, stacked affixes on one monster.
Thrill: the treasure goblin's chase, a champion's random affix read at a
glance, a weak point shot off, a perfect dodge through a telegraphed blow, a
horde that melts.

## 5. Lessons for Survivor Unchained

1. **One verb a creature, one tell a verb.** Every creature and every
   champion Sign does one readable thing (Diablo II, Risk of Rain 2,
   Left 4 Dead).
2. **Variety is difficulty.** Brotato's first danger level adds kinds, not
   numbers. New kinds and Signs should be how tiers feel harder before any
   stat multiplier does.
3. **No immunities on the horde.** Every hard immunity in the genre was
   walked back (Diablo II's Sunder Charms, Diablo III's invulnerable
   minions, Diablo IV's Suppressor). Cap resistances at 50% and guards at
   80%.
4. **No reflect, ever.** It punishes success and makes no play (Path of
   Exile, Diablo III's rework).
5. **On-death effects are opt-in or telegraphed.** Soulstone keeps its
   meteor-on-kill as a chosen curse; Diablo III's Molten waits three
   seconds. The oath of ruin is opt-in and fused: keep it so.
6. **A telegraph shorter than a human can react to is a trap.** Diablo IV's
   0.33 s Teleporter is the cautionary number; the deft bot's 0.6–0.75 s
   lunges are the floor here.
7. **Counters by area, not by build.** Celestine's cloak beats auto-aim but
   not area; Suppressor beat all ranged and was hated. A Sign that hampers a
   damage type must leave another way in.
8. **Never force a style and punish it in the same creature** (Path of
   Exile 2's Proximal Tangibility with a mana siphon).
9. **Never stack many mods on one monster.** Path of Exile's Archnemesis
   postmortem; Diablo III capped affixes by level. Two Signs at most,
   three on a herald.
10. **Price risk by how much harder it plays, not by its number** (Hades:
    +20% speed costs three times +20% damage).
11. **Pay for new difficulty, not repeated difficulty** (Hades' re-earned
    currencies), and show the reward table (Diablo III's Torment).
12. **Say the top is not meant to be beaten** (Last Epoch). The endless
    play past the half hour is that bar; its reward should be glory and
    history, not required power.
13. **A chase is a gift** (the treasure goblin, Brotato's Looter): an enemy
    that costs nothing to ignore and pays to pursue is the purest opt-in
    risk.
14. **Priority targets must show why they matter** (Brotato's Buffer, Doom's
    weak points): the buff glows, the banner is visible.
15. **Sound before action** for every special (Left 4 Dead, Vermintide): a
    champion's Sign and every telegraphed blow should have a voice.
16. **Mark elites by outline and colour** (Halls of Torment, 20 Minutes
    Till Dawn, DRG), and announce them ("Elite Threat").
17. **Predictable milestones and random modifiers can coexist** (Halls of
    Torment: fixed-time elites, random champion mods). Heralds at 10 and 20
    are the milestones; Signs are the surprise.
18. **Self-balancing pressure rewards fast killing** (Halls of Torment's
    Agony, Dead Cells' Malaise). Pressure that falls when the player kills
    quickly makes aggression the safe play.
19. **Let play style escalate the roster** (Grim Dawn's infamy): the people
    you hunt most could field more champions, and better spoils.
20. **Hard counters belong where the player chose** (StarCraft scouting,
    Hades' pact). The Wayfinder's table, which shows who holds an arena
    before it is entered, is that scouting step here.
21. **Remove the player's crutch only as an opt-in** (Death Must Die's
    move-speed-after-attack and Risk of Rain's Malachite healing disable hit
    some builds far harder than others). The oaths of blight and winter are
    this, and must stay oaths, never base behaviour.
