> Research notes for `docs/bosses/`, kept as written. Where the **Verification** section at the end corrects a claim, the correction stands; `RESEARCH.md` uses the corrected version.

# D: Readable bosses — research for a survivors-like

**Brief:** how bosses in bullet-heaven and top-down roguelites teach readable patterns, and how they cope with builds ranging from weak to absurd. Covers Enter the Gungeon, Nuclear Throne, The Binding of Isaac and Hyper Light Drifter in depth, then Cuphead, Touhou, Returnal, Furi, Dead Cells, Hollow Knight/Silksong, Tunic, Cult of the Lamb, Slay the Spire, Risk of Rain 2 and the survivors-likes themselves (Vampire Survivors, Brotato, HoloCure, Halls of Torment, Rogue: Genesia, Soulstone Survivors, Deep Rock Galactic: Survivor, Vampire Hunters, Picayune Dreams). It closes with cross-cutting research on damage caps, health gating, armour, telegraph colour language and accessibility, plus concrete recommendations.

Sources are cited inline. Wiki figures were read directly from the wikis (some via the MediaWiki API, because the fandom HTML pages block scrapers). A few points come only from search-engine summaries of reviews or Steam threads; these are marked *(secondary)*.

---

## 0. Ten-line summary

1. **Every serious roguelite caps or meters boss damage.** Gungeon uses a per-floor DPS cap over a 3-second window. Isaac uses an "armour" soft cap with a 9% floor. Slay the Spire's Heart is "Invincible" past 300 damage per turn. Risk of Rain 2 has Adaptive Armour. Nuclear Throne and Vampire Survivors scale boss HP instead. All of these exist so the boss is on screen long enough to show its patterns.
2. **The cap number is really a minimum fight length.** In Isaac, armour = HP ÷ soft-cap DPS, so the armour value is literally the floor on fight duration in seconds (Hush: 140). Gungeon's caps work out to roughly 23–35 seconds per boss phase.
3. **Caps cost goodwill.** Gungeon *raised* its caps in its final update so that synergies "feel appropriately powerful" ([Outerhaven](https://www.theouterhaven.net/?p=154935)), and it removes them entirely in Boss Rush.
4. **Rewarding speed works better than punishing it.** Examples: Nuclear Throne's Big Bandit opens a secret area if killed in under 10 seconds, Isaac's timed Boss Rush and Hush doors, and Vampire Hunters' kill-the-egg-before-it-hatches.
5. **Phase triggers should be "HP % *or* time, whichever comes first"** (Brotato's bosses). Weak builds still see the whole fight, and strong builds just see it faster.
6. **Reward clean play, not only damage.** Gungeon's Master Rounds give a heart container for a no-hit boss. Isaac adds +35% devil-deal chance for no red-heart damage in a boss fight.
7. **Named, timed attack cards** (Touhou spell cards) turn a pattern into a learnable unit: it has a name, a timer, a capture bonus, a practice mode and sometimes a pure "survive the timer" card.
8. **A telegraph needs more than one channel: shape, colour *and* sound.** HoloCure pairs a "!!" icon with an audio cue. Returnal reserves purple for "cannot dash through". Accessibility guidance says never rely on colour or sound alone.
9. **Bosses fail when they are stat checks or when they hide behind clutter.** Rogue: Genesia bosses "melt within seconds" at high scaling; Isaac's Delirium is criticised as an unreadable remix; Soulstone's lingering zones litter the arena.
10. **Survivors-likes need bosses that make you move, not just bosses that soak.** Big Dog's gapped spirals, Big Bandit's line-of-sight charge, Brotato's Invoker circles and the Vampire Survivors Directer's time- and level-gated phases all do this.

---

## 1. Enter the Gungeon (Dodge Roll, 2016)

### 1.1 The roster and what each boss teaches

Each floor draws one boss from a small pool ([Bosses](https://enterthegungeon.wiki.gg/wiki/Bosses)):

| Floor | Bosses |
|---|---|
| Keep of the Lead Lord | Bullet King, Gatling Gull, Trigger Twins |
| Gungeon Proper | Ammoconda, Beholster, Gorgun |
| Black Powder Mine | Cannonbalrog, Mine Flayer, Treadnaught |
| Hollow | High Priest, Kill Pillars, Wallmonger |
| Forge | High Dragun |
| Bullet Hell | Lich |

- **Gatling Gull** (700 HP) was the team's first boss and "has had the most refinement" (Dave Crooks, [Game Developer Q&A](https://www.gamedeveloper.com/design/q-a-the-guns-and-dungeons-of-i-enter-the-gungeon-i-)). Its kit is a primer in reading:
  - cardinal spreads
  - side-to-side sweeps
  - a large bullet that splits
  - leaping off-screen and landing near you
  - missiles whose landing spots are **marked by red crosshairs on the floor** (the leap can be interrupted with enough damage)
  - a melee swing if you hug it

  It comes with five arena variants with different cover: pillars, pits, chandeliers and tables, bushes and barrels ([Gatling Gull](https://enterthegungeon.wiki.gg/wiki/Gatling_Gull)). Its intro animation was the first one made and is the longest.
- **Bullet King** (950 HP) has Spin Shoot, an 8×8 Bullet Cluster that can be shot before it splits, an accelerating Bullet Ring ("dodge straight through"), Quickshot, Radial Lines and a Goblet Throw whose flammable pools can be shot out of the air ([Bullet King](https://enterthegungeon.wiki.gg/wiki/Bullet_King)). Each attack is easy alone. Danger comes from combinations, such as the cluster orb overlapping another pattern ([Steam guide thread](https://steamcommunity.com/app/311690/discussions/0/135508031951057688)). The Chancellor is a small character beat: leave him undamaged and he becomes harmless and tearful.
- **Trigger Twins** (2 × 400 HP) share charges, hops and summons, and each has one signature attack. When one dies the other enrages with new patterns **and heals to 50% if it was below that**. Killing both together skips the enraged phase ([Trigger Twins](https://enterthegungeon.wiki.gg/wiki/Trigger_Twins)). This is an anti-focus-fire rule that skilled play can bypass.
- **Beholster** (1,072.5 HP) carries six guns, and each gun is its own readable attack: a machine-pistol spread then a ring, three fast Void Marshal lasers, shootable homing Com4nd0 missiles, an eye shot that spawns a Beadie, and a rotating Eye Beam you beat by rolling back and forth ([Beholster](https://enterthegungeon.wiki.gg/wiki/Beholster)). Crooks calls it "the easiest symbol for our game… D&D meets bullet hell". Readability comes from *the weapon you can see is the attack you get*.
- **High Dragun** has two phases:
  - **Phase 1 (2,767.8 HP):** sweeping and aimed fire breath, edge-of-room pistol and Uzi streams, rockets that burst into rings, homing skulls, and knives stuck in the walls that keep firing until destroyed.
  - **Phase 2 (500 HP):** the Dragun is invulnerable and "completely fills the room with moving bullets. The player must dodge between circular safe zones". The heart is briefly exposed between waves ([High Dragun](https://enterthegungeon.wiki.gg/wiki/High_Dragun)).

  This makes the finale a survival puzzle rather than a DPS race.
- **Lich** has three phases and two arena changes ([Lich](https://enterthegungeon.wiki.gg/wiki/Lich)):
  - **Phase 1 (1,995 HP):** an open graveyard. He fires rings, spirals and bouncing rings and summons Tombstoners.
  - **Phase 2 ("Megalich", 2,100 HP):** a hand drags the player down into a smaller arena, where a huge stationary Lich pounds the floor and opens his ribcage to release concentric rings.
  - **Phase 3 ("Infinilich", 2,100 HP):** a free-floating boss with rotating lines, boomerangs, gun-shaped bullet formations and **rotating cone-shaped safe zones**.

### 1.2 The boss DPS cap

From the [Bosses page](https://enterthegungeon.wiki.gg/wiki/Bosses):

- "Every boss has a DPS cap… so guns with high fire rate or high damage can't destroy bosses in seconds."
- It is "applied across a 3-second window", and "the most damage a single shot can deal is equal to triple the floor's DPS cap".
- Caps by floor, *A Farewell to Arms* (2019) value with the original "classic" value in brackets: Keep 30 (25), Proper 42 (35), Mine 60 (50), Hollow 70 (58), Forge 78 (65), Bullet Hell 80 (70).
- Co-op raises the cap by 70%.
- Exceptions: no cap in Boss Rush; Glass Cannon, Makeshift Cannon, Yari Launcher, the Boxing Glove's 3-star punch and High Kaliber ignore it; so does any single projectile of 1,000+ damage.

**Implied minimum fight length** at the current caps (HP ÷ cap):

| Boss | Minimum length |
|---|---|
| Gatling Gull | ≈23 s |
| Bullet King | ≈32 s |
| Trigger Twins | ≈27 s |
| Beholster | ≈26 s |
| Dragun phase 1 | ≈36 s |
| Each Lich phase | ≈25–26 s |

So the cap's real job is to guarantee that **every boss gets roughly 25–35 seconds per phase to show its kit**, however broken the build.

**What it cost.** The final update raised the caps "so item combos and synergies will feel appropriately powerful during boss fights" ([Outerhaven, Apr 2019](https://www.theouterhaven.net/?p=154935)). The wiki notes that Boss Rush's lack of a cap "allows for extremely powerful gun/item combinations which may be less noticeable against normal capped bosses" ([Boss Rush](https://enterthegungeon.wiki.gg/wiki/Boss_Rush)). Players treat breaking the cap as a goal in its own right: Steam threads and mods such as "PushingTheLimits"/"MetaLimits" catalogue cap-breaking combos ([Steam](https://steamcommunity.com/app/311690/discussions/0/1743346190274433318), [Thunderstore](https://thunderstore.io/c/enter-the-gungeon/p/Bassforte/PushingTheLimits/)). **Lesson:** a hidden cap can feel like the game cheating you. Making the cap legible, with exceptions you can earn, turns it into content.

### 1.3 No-hit rewards, intros, curse and the panic button

- **Master Rounds.** Beating a main-floor boss without taking damage drops a Master Round worth +1 heart container. *Any* damage disqualifies, including pits and armour loss ([Master Round](https://enterthegungeon.wiki.gg/wiki/Master_Round)). This is the main reason a capped fight still feels worth mastering: the reward scales with skill, not DPS.
- **Intro cards.** Every boss gets an animated portrait card with a pun subtitle, for example Bullet King's "A Blast of Bullets" ([Bullet King](https://enterthegungeon.wiki.gg/wiki/Bullet_King)). The card is a breather and a "this is an exam" signal.
- **Jammed bosses.** At high Curse, bosses can spawn Jammed (crimson shader, black smoke) with HP × 1.2 + 100, and their bullets deal a full heart ([Jammed](https://enterthegungeon.wiki.gg/wiki/Jammed)). It is an opt-in difficulty layer with an unmistakable visual tag.
- **Blanks.** Blanks erase all enemy bullets, briefly stop firing and push enemies back. You always restock to two per floor ([Blank](https://enterthegungeon.wiki.gg/wiki/Blank)). A guaranteed panic button means dense patterns can be authored without every overlap becoming a death sentence.
- **Crooks on fairness:** the team hand-designed rooms because "the game was going to be more fun and more fair". He also said it is possible to beat the game "even with the starting gun" ([Game Developer](https://www.gamedeveloper.com/design/q-a-the-guns-and-dungeons-of-i-enter-the-gungeon-i-)). The bosses are tuned for a baseline build, and the cap protects that tuning from the top end.

---

## 2. Nuclear Throne (Vlambeer, 2015)

Nuclear Throne's bosses are few, short and aggressive. It copes with power through **loop scaling** and **IDPD pressure**, not caps.

- **Big Bandit** (Desert 1-3, 100 HP) bursts out of a wall after about 10% of the level's enemies die ([Big Bandit](https://nuclear-throne.fandom.com/wiki/Big_Bandit)).
  - He has two attacks: a fast barrage that does *not* re-aim while firing, and a wall-breaking charge.
  - The charge triggers **if you get too close or break line of sight behind a thin wall**. His behaviour is governed by readable spacing rules.
  - **Killing him in under 10 seconds opens a portal to the secret Oasis.** This openly rewards a burst build.
  - On loops he multiplies: 2, 4, 6… Big Bandits, each more aggressive.
- **Big Dog** (Scrapyard, 300 HP) sleeps until you get close, keep line of sight for 5 seconds, deal 30 damage, or leave fewer than 3 enemies alive ([Big Dog](https://nuclear-throne.fandom.com/wiki/Big_Dog)).
  - It cycles randomly between walking (no contact damage), spinning and missiles.
  - It always opens with **Spin**: six spiralling lines of slow red projectiles "with randomly placed gaps". This is the classic teach-the-gap pattern.
  - Its homing missiles can be shot back and damage it.
  - On loops: two more spiral lines per loop, firing missiles, and **+80% HP per loop**.
- **Lil' Hunter** (Frozen City, 140 HP) dives in about 7 seconds after the level starts. On loop L the delay is 7 ÷ (1 + L/2) seconds ([Lil' Hunter](https://nuclear-throne.fandom.com/wiki/Lil'_Hunter)).
  - **Landing telegraph:** "Watch for a shadow on the ground to indicate where he will land."
  - He summons IDPD portals by **health gate**: he may summon only while current/max HP < (6 − portals spawned)/6. If you "rapidly deplete his health", he chain-spawns reinforcements. This counter to burst damage falls naturally out of the formula.
  - He doesn't attack while calling backup, which opens a deliberate damage window.
  - He was reworked in update 61 to use his gun more and his stomp less.
- **The Nuclear Throne** (Palace 7-3, 1,500 HP) has beam, orb (two large orbs that burst into lines), tri-shot and walk phases ([The Nuclear Throne](https://nuclear-throne.fandom.com/wiki/The_Nuclear_Throne)).
  - **Walking on the red carpet baits the beam.** The player can deliberately trigger the "safest" attack to thin the screen.
  - Statues it tramples spawn Guardians.
  - **Destroying all four generators removes half its remaining HP** and guarantees a loop portal. This is an arena-interaction shortcut that rewards curiosity over DPS.
  - On loops the orbs and tri-shots gain extra rows and the generator shortcut no longer cuts HP.
- **The Captain** (IDPD HQ, 1,540 HP, more than the Throne) has fist charges, teleport-and-orb (reflectable) and stationary patterns. Her fight ends a looped run ([Captain](https://nuclear-throne.fandom.com/wiki/Captain)).

**Scaling.** Each loop multiplies normal enemy HP by (1 + 0.05L) and boss HP by **(1 + 0.05L)(1 + 0.33L)**. Bosses also "gain new attacks and become more aggressive", and IDPD portals open at random points between 20% and 80% of kills ([Other Game Features](https://nuclear-throne.fandom.com/wiki/Other_Game_Features)). IDPD units are "the equivalent of the player, but using tech… rather than mutations" ([I.D.P.D.](https://nuclear-throne.fandom.com/wiki/I.D.P.D.)), and they also hurt enemies. Pressure scales with how far you push, not with how hard you hit.

**Feedback.** The death screen changes from "You did not reach the Nuclear Throne" to "You almost reached…", and after looping to "The struggle continues". It is a progress bar written in prose. Each boss also has a trash-talk death line ("You lost, dead weakling").

**Lessons:** spacing-rule behaviour (charge if close or hidden) is as readable as any bullet pattern. Health-gated summons punish pure burst without a hard cap. Optional speed-kill rewards and arena shortcuts let strong builds and clever players *both* feel clever.

---

## 3. The Binding of Isaac: Rebirth → Repentance (Edmund McMillen / Nicalis)

Isaac's 700+ items ([VICE](https://vice.com/en/article/10-years-after-release-edmund-mcmillen-cant-stop-working-on-binding-of-isaac)) guarantee absurd builds. Its bosses lean on four tools against them: **armour, stage HP, health gates and timers**.

### 3.1 Damage scaling ("armour")

From the [Damage Scaling](https://bindingofisaacrebirth.wiki.gg/wiki/Damage_Scaling) page:

- "The entity's base HP is divided by its armor value to create a soft cap on damage per second." DPS under the cap is untouched; DPS above it is pulled down.
- The boss tracks unmodified damage taken over the last 4 seconds.
- A single hit larger than 4× the cap is pre-emptively reduced.
- Freshly spawned entities take 99% reduced damage, fading over 4 seconds.
- **"No matter what, each individual attack cannot have its damage reduced below 9% of its original damage, allowing the armor to be overwhelmed."**
- Side effect: "slow, high-powered attacks are less effective than rapid, lower-damage ones."

| Boss | HP | Armour | Soft cap (DPS) | ≈ minimum seconds |
|---|---|---|---|---|
| Satan | 600 | 12 | 50 | 12 |
| Isaac | 2,000 | 20 | 100 | 20 |
| The Lamb | 2,000 | 25 | 80 | 25 |
| Mega Satan P1 / P2 | 5,000 / 2,000 | 90 | 55.6 / 22.2 | 90 / 90 |
| Ultra Greed | 3,500 | 85 | 41.2 | 85 |
| Hush (P2) | 6,666 | 140 | 47.6 | 140 |
| Mother P1 | 2,222 | 90 | 24.7 | 90 |
| The Beast | 10,000 | 60 | 166.7 | 60 |

Because armour = HP ÷ cap, **the armour number is the designer's intended minimum fight length in seconds**, with the 9% floor as a relief valve for truly broken builds. It is a clean, tunable model.

**Stage HP.** Ordinary enemies and bosses also get HP = BaseHP + (min(4, Stage) + 0.8·bound(0, Stage−5, 5)) × StageHP. Health grows with depth and stops after stage 10 ([Stage HP](https://bindingofisaacrebirth.wiki.gg/wiki/Stage_HP)). Bosses also get temporary status-effect immunity after each status ([Bosses](https://bindingofisaacrebirth.wiki.gg/wiki/Bosses)).

### 3.2 Notable bosses

- **The Lamb** ([wiki](https://bindingofisaacrebirth.wiki.gg/wiki/The_Lamb)): rings, rotating waves, homing spreads and Attack Flies. At 50% the body detaches and becomes stationary while the head keeps fighting with charges and four-way rotating Brimstone. One health pool becomes two targets, and killing order matters: the body spawns 25 flies if the head dies first.
- **Mega Satan** ([wiki](https://bindingofisaacrebirth.wiki.gg/wiki/Mega_Satan)), 5,000 HP:
  - **Hands** (600 HP each, regrowing after 30 seconds) open when you approach and close when you retreat. Destroying one deals 100 to the boss.
  - **Health gates:** at 750, 1,500 and 2,250 damage he turns invulnerable and summons waves that must be cleared.
  - His hands always spread fully while charging the Mega Blast, which is a body-language telegraph.
  - **Phase 2** is a handless skull firing multi-coloured patterns.
  - A 50% chance to continue to the Void instead of the ending.
- **Hush** ([wiki](https://bindingofisaacrebirth.wiki.gg/wiki/Hush)), 6,666 HP:
  - **Gated by time:** the Blue Womb is open only if you reach it within 30 minutes.
  - Phase 1 copies the ??? fight. Phase 2 is a huge face at the top of the room cycling five sub-phases of rings, U-salvos, spirals, lasers with creep trails, and fly and gaper summons.
  - The **room darkens with ceiling veins as Hush loses health**, so the arena itself acts as the health bar.
  - It periodically sinks into the floor, invulnerable.
  - In Repentance it regenerates if you stop damaging it, which counters stalling.
  - Hush is the canonical "DPS-limited sponge". The armour figure above means about 140 seconds at the cap.
- **Delirium** ([wiki](https://bindingofisaacrebirth.wiki.gg/Delirium)), 10,000 HP, in the Void (a quadruple-size room that changes visual theme mid-fight):
  - It teleports and **shape-shifts into bosses you met this run**, keeping its own HP and entering multi-phase bosses at the matching HP %.
  - Burst damage makes it "attack, teleport, and transform at extreme speeds" and turn red, so it **escalates in response to burst**.
  - It only has armour while transformed.
  - Players criticise it heavily: "0 pattern or telegraphing", and instant transformations mid-attack (a Mom's Foot shadow becoming a fast boss) produce unavoidable hits ([Steam 1](https://steamcommunity.com/app/250900/discussions/0/3191362948572009860), [Steam 2](https://steamcommunity.com/app/250900/discussions/0/3104647961262642680)) *(secondary)*.
  - **Lesson:** a remix boss must finish or cancel the current tell before it changes form, and must not carry hitboxes across the change.
- **Ultra Greed** ([wiki](https://bindingofisaacrebirth.wiki.gg/wiki/Ultra_Greed)), 3,500 HP, armour 85:
  - Cannot be damaged until it lands from its noose (an intro window).
  - Stomps spawn Keepers. A slot-machine eye spins up coins: Key coins open four gold doors that release hordes, Bomb coins explode, and Heart coins heal him. He also heals by walking over coins.
  - **Lesson:** the arena economy is the pressure. Kill the coins or the fight snowballs.
  - In Greedier mode he turns into a gold statue that revives as Ultra Greedier.

### 3.3 Timers and no-hit incentives

- **Boss Rush:** reach Mom within 20 minutes (25 in Repentance's alternative path) and you unlock a room with 15 waves of 2 bosses each and an extra item reward ([Boss Rush](https://bindingofisaacrebirth.wiki.gg/wiki/Boss_Rush)). Isaac's answer to strong builds is "**go faster and earn extra content**", not "hit less hard".
- **Devil-deal odds:** "Taking no Red Heart damage against the boss +35%" ([Devil Room](https://bindingofisaacrebirth.wiki.gg/wiki/Devil_Room)). Clean boss play feeds directly into build power.
- McMillen has noted that players "want to know how to break it" ([VICE](https://vice.com/en/article/10-years-after-release-edmund-mcmillen-cant-stop-working-on-binding-of-isaac)). The bosses are tuned on the assumption that they will be.

---

## 4. Hyper Light Drifter (Heart Machine, 2016)

HLD has no dialogue text. Bosses teach through **body language, floor marks, colour contrast and sound**.

- **Visual grammar.** Kyle Nguyen's analysis ([Mechanics of Magic](https://mechanicsofmagic.com/?p=5948)) notes:
  - warm player colours against cool ground
  - "'Good guys'… share a reddish palette, while enemies are a consistent green-brown"
  - "size to roughly approximate the difficulty of enemies"

  Judgement and the disease are always black and pink, with diamond motifs ([Judgement](https://hyperlightdrifter.fandom.com/wiki/Judgement)). The final boss's colour has been seeded all game.
- **Judgement** (final boss):
  - **Charge**: once at full HP, then twice at 2× speed under 50%, then three times at 3× under 30–40%.
  - **Bullet Barrage** from each corner, followed by a **Hyper Laser** whose direction is shown in the first frames ("Judgement will crouch down and fire its laser in a straight line. This will then signal which side Judgement will swipe").
  - **Arm Stab** from the centre.
  - **Light Explosion**: the screen goes black and four drifting lights later detonate in diamond shapes.
  - Every attack speeds up at fixed HP thresholds, so the phases are the same moves played faster. **Reflecting the barrage back can skip a phase entirely**, which rewards skill, not DPS.
- **The Hierophant** ([wiki](https://hyperlightdrifter.fandom.com/wiki/The_Hierophant)) attacks the floor:
  - a *trail* of detonating tiles that follows you
  - ✕/＋ detonations at your feet
  - full-width striped sweeps

  The moveset narrows at 40% to spamming the sweep. He always pauses in the centre before calling Vultures, a reliable punish window.
- **The Archer** ([wiki](https://hyperlightdrifter.fandom.com/wiki/The_Archer)): deflectable arrows and proximity mines that build up in square or diamond formations. The arena slowly clutters, and grenades or dashes can clear it, which is a player-controlled clean-up tool.
- **The Emperor** ([wiki](https://hyperlightdrifter.fandom.com/wiki/The_Emperor)): jars, ground pound and exploding Plant Beastlings. **Detonating the Beastlings stuns the boss**, so the adds are the damage window. Toad leaps end in a three-second shaking crouch, a "hit me now" pose.
- **The Hanged Man** ([wiki](https://hyperlightdrifter.fandom.com/wiki/The_Hanged_Man)): crystals on the arena edge hold Crystal Knights. Baiting his slashes into the crystals destroys them before he can release the knights. You can pre-empt the arena hazards.
- **Sound.** Akash Thakkar layered "up to 20 different sounds" so every weapon is identifiable by ear, and kept sounds "grounded a little bit in reality and then stylised" ([Thumbsticks, GDC 2017](https://www.thumbsticks.com/gdc-17-creating-disturbing-soundscapes-of-hyper-light-drifter/); [GDC Vault](https://gdcvault.com/play/1023778/The-Sound-of-Hyper-Light)).
- **Difficulty fallout.** Post-launch patches added dash i-frames. Preston: "We want this game to feel as fair and fluid as possible". Heart Machine rolled back health-kit refills after a split community reaction ([Kotaku](https://kotaku.com/the-contentious-debate-over-whether-to-make-hyper-light-1772125287)). It later added a **Newcomer mode and a Boss Rush** ([Cliqist](https://cliqist.com/2016/09/30/ready-publish-new-hyper-light-drifter-update-adds-60fps-boss-rushing/)).

**Lessons:** wordless readability needs strict faction colours, size as a threat cue, first-frame directional tells and floor-based previews. A practice mode (Boss Rush) is the natural partner of hard bosses.

---

## 5. Other reference games

### 5.1 Cuphead: phase design and progress feedback

- "Every attack on every boss in the game is telegraphed" ([Epilogue Gaming](https://epiloguegaming.com/cupheads-boss-design/)). The Root Pack teaches one skill per vegetable: jump and shoot, then movement, then aiming at shootable projectiles.
- GMTK's "How Cuphead's Bosses (Try to) Kill You" ([Amara transcript page](https://amara.org/v/C3BEq)) argues the attacks exist to *make you move*. It praises controlled randomness: a bull rears back, but the delay before it lunges varies *(secondary)*.
- Jeff Vogel: "just about every attempt against a boss… plays out differently". Randomness keeps the game "unpredictable and tough but still fair" ([Game Developer](https://www.gamedeveloper.com/design/cuphead-cruelty-and-selling-unfairness-to-you-)).
- The **death-screen progress bar with a hash mark per phase** turns repeated failure into visible progress ([Critics at Large](https://www.criticsatlarge.ca/2017/10/victory-vindication-studio-mdhr-cuphead.html), [GamingTrend](https://gamingtrend.com/reviews/once-more-unto-the-drink-cuphead-review/)).

### 5.2 Touhou: spell cards as named, timed units

- Enemy bullet patterns get official names, "probably the first known instance of a shooting game's bullet patterns being given official, personalized names" ([Touhou Wiki (fandom)](https://touhou.fandom.com/wiki/Spell_Card)).
- The open-source Touhou-like *Taisei* documents the grammar ([GAME.rst](https://github.com/taisei-project/taisei/blob/master/doc/GAME.rst)):
  - **Normal** attacks are "a break between the other, more fierce attacks".
  - **Spell Cards** change the background and are *captured* by "shooting down the HP within the time limit without getting hit or using bombs".
  - **Survival Spells** make the boss "completely invincible… Try to survive somehow until the timer runs out".
  - **Spell Practice** lets you replay any card you have met.
- In the official games survival cards show a blue health bar ([Imperishable Night](https://en.wikipedia.org/wiki/Imperishable_Night)). In Mountain of Faith, timing out costs resources ([Giant Bomb](https://giantbomb.com/wiki/Games/Touhou_10_Mountain_of_Faith)) *(secondary)*.
- **Why this matters for a survivors-like:** the card is the right unit for a boss attack. Name, timer, capture reward and practice entry all hang off it. A timeout guarantees that a weak build still progresses. A survival card is DPS-proof by design.

### 5.3 Returnal: colour as a rule system in 3D

- Housemarque's "bullet ballet" relies on "keeping things simple and consistent" when moving arcade bullet patterns into 3D ([Game Developer](https://www.gamedeveloper.com/marketing/a-third-person-action-roguelike-bullet-hell-arcade-thriller-the-making-of-returnal)).
- **Purple means you cannot dash through it.** Selene's dash ignores almost everything, and "the things she can't weave out of are all coloured purple" ([Android Central](https://www.androidcentral.com/returnal-ps5-tips-and-tricks-beginners)) *(secondary)*. Ophion's dark purple shockwaves are jump-only ([Push Square](https://pushsquare.com/guides/returnal-all-bosses-and-how-to-beat-them)).
- Orange and blue mark ordinary dodgeable fire, and red glowing spots mark weak points.
- Bosses have **three health bars, one per phase**, and add attacks per bar. Arenas change between phases: Nemesis moves to new platforms and a free-fall, and Ophion physically transforms.
- **Lesson:** reserve one colour for one *rule*, not one *attack*.

### 5.4 Furi: phases as lives

Each pip under the boss's bar is a phase. Clearing a phase refills the player's health and gives back a life; dying resets only the current phase ([Use a Potion](https://useapotion.com/2016/07/review-furi), [Button Musher](https://buttonmusher.substack.com/p/furi-review-gameplay-perfected)) *(secondary)*. Phase count is legible at a glance and progress is safely banked.

### 5.5 Dead Cells: telegraph clarity and difficulty tiers

- The Concierge's stab has "a long, clear telegraphed wind-up". By contrast, its Aura of Laceration gives "the only hint… little red particles", which is a cautionary under-telegraph ([wiki](https://deadcells.wiki.gg/wiki/The_Concierge)).
- At 1+ Boss Stem Cells, "the Concierge goes straight to the second phase". Higher tiers rewrite bosses' early phases instead of only adding HP, and progressively remove healing ([BSC](https://deadcells.wiki.gg/wiki/BSC)).
- Sébastien Bénard describes "about 30–40 such small techniques" to make the game feel fair ([80.lv](https://80.lv/articles/dead-cells-hidden-tricks-that-make-the-game-feel-fair)).

### 5.6 Hollow Knight → Silksong: telegraph lessons only

Team Cherry's William Pellen says Hollow Knight bosses chose attacks reactively from player position. Silksong bosses "decide what they want to do and then move into the correct position to do it" ([Military.com](https://www.military.com/off-duty/games/silksong-devs-explain-how-bosses-were-designed-differently-those-hollow-knight.html)). **Repositioning becomes a telegraph in itself.** That suits a survivors-like, where the player is always moving.

### 5.7 Tunic and Cult of the Lamb

- **Tunic**'s bosses "hit like a runaway train". Its **No Fail** toggle can be switched at any time. Shouldice: "If you don't like combat, or just want to get past a particularly tricky encounter… turn on No Fail mode" ([Inverse](https://inverse.com/gaming/tunic-andrew-shouldice-interview), [Can I Play That](https://caniplaythat.com/2022/04/06/indie-spotlight-tunic/)).
- **Cult of the Lamb**'s bishops have "obvious tells", and some feel "like a bullet hell at times" ([Prima](https://primagames.com/featured/cult-of-the-lamb-review-pc), [MP1st](https://mp1st.com/reviews/cult-of-the-lamb-review-the-sacrificial-lamb-pc)) *(secondary)*. It shows readable bullet-hell bosses in a mass-market, beginner-friendly roguelite.

### 5.8 Build-breaking counters outside the genre

- **Slay the Spire, Corrupt Heart.** *Invincible* caps damage and HP loss at **300 per turn (200 at A19+)**, so you need at least three turns (four at higher ascension). *Beat of Death* deals 1–2 damage to you per card played ([slaythespire.gg](https://slaythespire.gg/bosses/The_Corrupt_Heart), [HighGround](https://www.highgroundgaming.com/?p=98743)). It is "the ultimate check on deck building".
- **Slay the Spire, Time Eater.** It ends your turn after 12 cards, a direct counter to infinite combos ([Steam](https://steamcommunity.com/app/646570/discussions/0/1692659135905591438)).
- **Risk of Rain 2, Mithrix** ([wiki](https://riskofrain2.wiki.gg/wiki/Mithrix)):
  - Adaptive Armour in phases 1 and 3.
  - Phase 4 **steals your items** and **returns them in proportion to damage dealt**.
  - Hopoo addressed the backlash: "Our intent was not for players to avoid good items… If that seems to be the best strategy, we will be changing the last phase" ([Rogueranker](https://rogueranker.com/mithrix-ror2/)) *(secondary)*.
  - **Lesson:** a counter that makes players *avoid* power is a design failure.

---

## 6. Survivors-likes and bullet heavens

- **Vampire Survivors** ([Enemies](https://vampire.survivors.wiki/wiki/Enemies)):
  - Most "bosses" are just tougher wave members with resistances and a chest drop. They teleport back on screen rather than despawn. This is the genre's default HP-sponge boss.
  - **The Reaper** ([wiki](https://vampire.survivors.wiki/wiki/The_Reaper)) is a timer enforcer, not a fight. It spawns at the time limit and every minute after, has **655,350 × player level HP** ("HP x Level"), deals 65,535 damage and resists freeze/instant-kill (only Clock Lancet, Orologion and the like freeze it). Killing it is a secret unlock: hubris is rewarded, not expected.
  - **The Directer** ([wiki](https://vampire.survivors.wiki/wiki/The_Directer)) is VS's real pattern boss:
    - **Phase 2 requires 30 more seconds *and* player level ≥ 7.** The heads become breakable after 60 seconds *and* level ≥ 14. Phase 3's core requires level ≥ 19 and ≥ 60 seconds.
    - Attacks use explosion zones and "circular yellow zones" for incoming eyes.
    - The arena opens up and its background cycles through the earlier stages.
  - **Lesson:** gating phases on *time and level* together, with invulnerable parts that become breakable, makes DPS irrelevant to pacing.
- **Brotato** ([Enemies](https://brotato.wiki.spellsandguns.com/Enemies)):
  - Wave-20 bosses Predator and Invoker have 29,250 base HP. On Danger 5 **both** appear at 75% HP ×1.4.
  - Predator mutates at **50% HP *or* 45 s** (dash with orbiting shots → omnidirectional fire).
  - Invoker mutates at **75% / 30 s** and **40% / 60 s** (circles around the player, then +150% speed).
  - Elites scale +750 HP and +1.5 damage per wave.
  - **"HP *or* time" triggers are the single most transferable pattern here.**
- **HoloCure:**
  - Fubuzilla (8,000 HP at 10 minutes) fires lasers "indicated by the marker" ([Samurai Gamers](https://samurai-gamers.com/holocure/stage-1-grassy-plains-enemy-list/)).
  - The Area 15 trio uses **"an !! indicator along with an audio cue"** for Moontato's lunge, a **cone-shaped warning** for Risusaurus's fire breath, and circular bullet patterns for UFOFI ([HoloCure wiki](https://holocure.wiki.gg/wiki/Area_15_(Bosses))).
  - This is a model of icon + sound + shape redundancy in a survivors-like.
- **Halls of Torment:** four bosses per stage that "almost feel like bullet hell at times", although "you're often so tough when you reach them that they feel like battles of attrition" ([GodisaGeek](https://godisageek.com/reviews/halls-of-torment-review)) *(secondary)*. Players report the first boss is the only one you cannot dodge without enough move speed, and at low HP it outruns you ([Steam](https://steamcommunity.com/app/2218750/discussions/0/3803903461249040332)) *(secondary)*. An unannounced stat check feels unfair.
- **Rogue: Genesia:** bosses add bullet-hell dodging, but "once you hit high-level scaling, even the toughest bosses melt within seconds… nothing more than stat-checks". Players also complain of visual clutter ([Checkpoint Gaming](https://checkpointgaming.net/reviews/2025/03/rogue-genesia-review-unlimited-power/), [Vaporlens](https://vaporlens.app/app/2067920/rogue_genesia)) *(secondary)*. This is the textbook uncapped failure.
- **Soulstone Survivors:** red ground zones "are only dangerous once they are filled and trigger", so a well-timed dodge lets you stand in them. One boss leaves permanent damage zones until "the entire arena will be littered" ([Steam](https://steamcommunity.com/app/2066020/discussions/0/603029004750948981)) *(secondary)*. The fill-up telegraph is good; un-expiring clutter is bad.
- **Deep Rock Galactic: Survivor:** the three-stage Dreadnought "stop[s] and wiggl[es] briefly before jumping at your last known location" every 7–12 seconds. It also has spike-ring traps and egg sacs that burst into adds ([Prima](https://primagames.com/tips/how-to-defeat-dreadnought-boss-in-deep-rock-galactic-survivor)) *(secondary)*. That is a classic wiggle-then-commit tell aimed at your last position.
- **Vampire Hunters** (first-person survivors-like): bosses range from wasp-hive clusters to a sandworm. The Kappa "comes in two stages where you can actually prevent it from hatching by destroying the egg" ([Gaming Pastime](https://gamingpastime.com/vampire-hunters-review/)) *(secondary)*. A strong build skips a phase as a reward, like Big Bandit's Oasis.
- **Picayune Dreams:** "bullet hell bosses who spew out elaborate attacks" ([Rogueliker](https://rogueliker.com/picayune-dreams-review/)). Players praise the Touhou × Vampire Survivors blend but criticise boss and weapon balance and a dominant meta ([Vaporlens](https://vaporlens.app/app/2088840/picayune_dreams)) *(secondary)*. This is proof that genuine danmaku bosses can work inside a bullet heaven.

---

## 7. Cross-cutting: tools for coping with build variance

| Tool | Example | What it protects | Failure mode |
|---|---|---|---|
| **DPS cap (windowed)** | Gungeon 3 s window, per-floor caps | Guarantees ~25–35 s of each phase | Feels like cheating if invisible. Gungeon raised its caps after feedback. |
| **Armour / soft cap with floor** | Isaac (HP ÷ armour, 9% floor) | Minimum fight length; still lets absurd builds win | Penalises slow, heavy hitters more than fast ones |
| **Per-turn or per-window cap** | StS Heart *Invincible* 300 | Forces multi-turn fights | Can feel arbitrary unless shown on the HUD |
| **Adaptive armour** | RoR2 Mithrix | Blunts one-shots | Opaque |
| **Health gates (invulnerable at thresholds)** | Mega Satan 750/1,500/2,250; Dragun phase 2; Hush submerging | Guarantees each phase is seen | Dead time if the gate lasts long |
| **Burst-reactive escalation** | Lil' Hunter IDPD gate; Delirium speeding up; Trigger Twins heal-to-50% | Punishes burst without a cap | Unreadable if escalation is instant (Delirium) |
| **HP or time phase triggers** | Brotato bosses; VS Directer (time + level) | Weak builds still see every phase | Strong builds may see phases overlap |
| **Scaling HP** | NT loops (1+0.05L)(1+0.33L); VS Reaper HP × level; Isaac Stage HP; Gungeon Jammed ×1.2+100 | Keeps up with progression | Pure scaling creates HP sponges |
| **Survival / timeout segments** | Touhou survival cards; Dragun phase 2 | DPS-proof skill test | Boring if too long or too easy |
| **Speed rewards** | Big Bandit <10 s → Oasis; Isaac Boss Rush/Hush timers; Kappa egg | Turns power into content | Strong builds get stronger |
| **No-hit rewards** | Gungeon Master Round; Isaac +35% devil chance | Rewards reading over DPS | Players restart runs to farm them |
| **Power theft / counters** | RoR2 item steal; StS Time Eater / Beat of Death | Hard counter to degenerate builds | Players avoid power, which is the worst outcome |

**Key observation:** the best-liked approaches *convert* excess power into something rather than nullifying it. They give speed rewards, open secret areas, raise caps you can see, and remove caps in an opt-in mode (Gungeon Boss Rush). The worst-received approaches either let power erase the fight (Rogue: Genesia) or take power away (Mithrix phase 4).

---

## 8. Telegraph colour language and accessibility

- **Telegraph theory.** Mike Stout calls an attack a question the enemy asks: "If players don't know how to play your game, they can't actually play your game". Projectile attacks should combine "animation, sound effects, voice-over, visual effects, and sometimes even force-feedback" ([Game Developer](https://gamedeveloper.com/design/enemy-attacks-and-telegraphing)).
- **Reserve a colour per rule.** Returnal uses purple for "cannot dash", red glow for weak points, and orange or blue for ordinary fire. Gungeon uses crimson plus smoke for Jammed (double damage). HLD uses warm for friends, green-brown for foes and pink/black for Judgement.
- **Ground decals for area attacks.** Gatling Gull's red crosshairs, Lil' Hunter's shadow, Soulstone's filling red zones, HoloCure's cones and markers, and the VS Directer's yellow circles.
- **Body-language tells and first-frame direction.** Judgement's crouch shows the side of its sweep, Mega Satan's hands spread for the blast, and the Dreadnought wiggles before it leaps.
- **Colour alone is not enough.** The Game Accessibility Guidelines say "Ensure no essential information is conveyed by a fixed colour alone". Red or green deficiency affects about 8–10% of males. Use colour as a backup to "text, symbols, patterns, or shapes", and offer per-element colour presets rather than whole-screen filters ([GAG colour](https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-colour-alone/)).
- **Sound alone is not enough either.** The guideline: "Ensure no essential information is conveyed by sounds alone". Test by playing muted ([GAG sound](https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-sounds-alone/)).
- **Players ask for shapes.** Rabbit and Steel labels its mechanic circles with symbols ([Steam](https://steamcommunity.com/app/2132850/discussions/0/4357873276728761798)). ESO players ask for configurable telegraph colours ([ESO forums](https://forums.elderscrollsonline.com/en/discussion/comment/3951447/)). The consensus is that "shape patterns, icons, and texture overlays are essential" ([bugnet QA note](https://bugnet.io/blog/qa-testing-for-colorblind-modes)) *(secondary)*.
- **Red is the riskiest warning colour.** It is the genre default, yet hardest for protanopes and deuteranopes. Pair it with a shape and an animation: a filling ring, a hatched fill or a pulsing outline.

---

## 9. Recommendations for our survivors-like

**Fight structure**

1. **Author bosses as decks of named attack cards.** Each card is one pattern with a name, a 1–2 line telegraph, a duration and a timeout (Touhou, Gungeon intros). Show the name as a banner when it is declared. Log cards the player has seen into a practice or bestiary mode (Taisei Spell Practice, HLD Boss Rush).
2. **Use HP-or-time phase triggers** (Brotato). Phase N+1 starts at X% HP *or* T seconds, whichever comes first. Optionally also require a level, as the VS Directer does, for scripted finales.
3. **Use a soft DPS cap expressed as a target fight length** (Isaac model):
   - cap = phaseHP ÷ targetSeconds
   - smooth it over a 3–4 second window
   - keep a floor of roughly 10%, so absurd builds still win faster
   - target about 20–30 seconds per phase early and 40–60 seconds for finales
   - **Show it**: for example, the boss bar gains a visible "guard" sheen when you exceed the cap, plus a "cap broken!" flourish for the 1,000-damage or synergy exceptions (Gungeon).
   - Remove the cap in an opt-in Boss Rush.
4. **Include at least one DPS-proof segment per major boss:** a survival card or safe-zone dance like the Dragun's phase 2. During it the boss is clearly invulnerable (blue or crystalline bar, as Touhou does) with a visible timer.
5. **Convert surplus power into rewards.** Add speed-kill bonuses (Big Bandit's Oasis), egg-before-hatch phase skips (Vampire Hunters), timed bonus rooms (Isaac) and arena shortcuts (Nuclear Throne's generators). Never take items away.
6. **Reward reading as well as damage.** Give a no-hit bonus per boss (Master Round) and a "capture" bonus per card (Touhou).

**Telegraphs and readability**

7. **Use a telegraph grammar with three channels:**
   - a shape on the ground (circle, cone or line, with a fill showing time to impact)
   - a colour that encodes a *rule* (for example amber means dodge or outrun, violet means it cannot be dashed through or must be left)
   - a distinct sound per attack family

   Make sure every rule is still readable in greyscale and muted.
8. **Keep player VFX below boss threats.** Boss bullets and decals should always draw above player weapon effects, with a high-contrast outline. Consider dimming player effects during a declared card. Rogue: Genesia and Soulstone show how clutter ruins readability.
9. **Make spacing rules part of the language:** charge if the player is too close or out of sight (Big Bandit), lunge at the last known position after a wiggle (Dreadnought). Have bosses reposition *before* acting (Silksong) so movement is the tell.
10. **Teach one attack at a time, then combine them** (Cuphead's Root Pack, Bullet King). Open with a pattern that has gaps, like Big Dog's spiral. Overlaps should only appear in later phases. Randomise *timing* slightly within a tell (Cuphead), but never the *meaning* of a tell.
11. **Don't let lingering hazards build up indefinitely.** Give them lifetimes or player-side clean-up (HLD's Archer mines can be detonated). Learn from Soulstone's ever-growing zones.
12. **Remix bosses must finish their current tell before transforming** and must not carry hitboxes across the change (the Delirium complaint).

**Feedback and accessibility**

13. **Show progress clearly:** phase pips on the bar (Furi), a death-screen progress line (Cuphead, Nuclear Throne's "almost reached"), and arena changes as health cues (Hush's darkening room).
14. **Ship accessibility toggles:** per-element colour presets, shape overlays and telegraph-duration scaling. Consider an assist or "no fail" option (Tunic, HLD Newcomer).

---

## 10. Source reliability

- **High:** wiki figures, read directly from the wikis (enterthegungeon.wiki.gg, bindingofisaacrebirth.wiki.gg, nuclear-throne and hyperlightdrifter fandom wikis via API, vampire.survivors.wiki, brotato wiki, holocure.wiki.gg, deadcells.wiki.gg, riskofrain2.wiki.gg).
- **Medium:** developer statements, read directly from Game Developer, Kotaku, Military.com and Thumbsticks.
- **Lower:** points marked *(secondary)*, which come from search-engine summaries of reviews or forum threads that could not be opened directly.
- **Not retrieved:** GMTK's Cuphead video transcript and the Touhou Wiki (touhouwiki.net). Their points come from search snippets and secondary sources.

---

## Verification

Adversarial check, 2026-10-03. Wiki pages were read as raw wikitext through the MediaWiki API. Verdicts: **confirmed**, **confirmed with correction**, **partially supported**, **unsupported** (could not be confirmed from the cited source).

| # | Claim | Verdict | Notes / correction |
|---|---|---|---|
| 1 | Gungeon DPS cap: 3 s window, max single shot = 3× floor cap, +70% in co-op, none in Boss Rush, listed exceptions (Glass Cannon, Makeshift Cannon, Yari, Boxing Glove 3-star, High Kaliber, ≥1,000-damage projectile) | confirmed | Wording matches [Bosses](https://enterthegungeon.wiki.gg/wiki/Bosses) Notes. |
| 2 | Gungeon caps by floor 30/42/60/70/78/80 (classic 25/35/50/58/65/70) | confirmed | Same page. The Keep/Proper/Mine/Hollow values also apply to Oubliette, Abbey, Rat's Lair and R&G Dept. |
| 3 | Boss HPs (Gull 700, Bullet King 950, Twins 2×400, Beholster 1,072.5, Dragun 2,767.8 + 500, Lich 1,995/2,100/2,100) and the minimum-length table | confirmed | Infobox values match. Arithmetic re-checked: 23.3, 31.7, 26.7, 25.5, 35.5, 24.9 and 26.3 s. |
| 4 | Outerhaven, Apr 2019: caps raised "so item combos and synergies will feel appropriately powerful during boss fights" | confirmed | Article dated 9 Apr 2019; quote is verbatim. The source does **not** say the caps were raised "after feedback", so the §7 table wording overstates it. |
| 5 | Trigger Twins: survivor heals to 50% if below it; killing both together avoids this | confirmed | [Trigger Twins](https://enterthegungeon.wiki.gg/wiki/Trigger_Twins). |
| 6 | Master Round: any damage disqualifies, including pits. Jammed bosses: HP×1.2+100, full-heart bullets | confirmed | [Master Round](https://enterthegungeon.wiki.gg/wiki/Master_Round), [The Jammed](https://enterthegungeon.wiki.gg/wiki/The_Jammed). Bosses also drop doubled Hegemony Credits on a no-hit kill. |
| 7 | Crooks quotes ("most refinement", "easiest symbol… D&D meets bullet hell", "more fun and more fair", "even with the starting gun") | confirmed | All verbatim in the [Game Developer Q&A](https://www.gamedeveloper.com/design/q-a-the-guns-and-dungeons-of-i-enter-the-gungeon-i-). |
| 8 | Isaac damage scaling: HP ÷ armour soft cap, 4 s window, 4× single-hit pre-emptive cut, 99% spawn armour fading over 4 s, 9% floor quote, "slow, high-powered…" quote | confirmed | Verbatim on [Damage Scaling](https://bindingofisaacrebirth.wiki.gg/wiki/Damage_Scaling). Caveat: most explosive damage and some other sources bypass the scaling in Repentance, so the armour value is not a hard floor on fight length. |
| 9 | Isaac armour table (Satan, Isaac, Lamb, Mega Satan, Ultra Greed, Hush, Mother, Beast) | confirmed | All values match. Hush's armour of 140 is the Repentance value; it was 160 (cap 41.66) in Afterbirth/Afterbirth+. |
| 10 | Boss Rush: "reach Mom within 20 minutes (25 alt path)", 15 waves × 2 bosses | confirmed with correction | You must **beat** Mom within 20 minutes (Depths/Necropolis/Dank Depths), or within 25 minutes in Mausoleum/Gehenna; reaching her is not enough. [Boss Rush](https://bindingofisaacrebirth.wiki.gg/wiki/Boss_Rush) |
| 11 | Devil deal +35% for no red-heart damage against the boss | confirmed | This is the Repentance/Rebirth value; Afterbirth used +17.5%. [Devil Room](https://bindingofisaacrebirth.wiki.gg/wiki/Devil_Room) |
| 12 | Mega Satan: hands 600 HP, respawn 30 s, 100 damage on destruction; gates at 750/1,500/2,250; "50% chance to continue to the Void" | confirmed with correction | Gates and hands are confirmed. The 50% Void chance is **outdated**: it applied in Afterbirth+, and in Repentance+ the portal appears 100% of the time. [Mega Satan](https://bindingofisaacrebirth.wiki.gg/wiki/Mega_Satan) |
| 13 | NT: Big Bandit kill in <10 s opens Oasis; loop boss HP ×(1+0.05L)(1+0.33L); Big Dog +80%/loop; IDPD portals at 20–80% of kills; "almost reached" death text | confirmed | [Big Bandit](https://nuclear-throne.fandom.com/wiki/Big_Bandit), [Other Game Features](https://nuclear-throne.fandom.com/wiki/Other_Game_Features). "Almost reached" appears specifically when you die to the Throne. |
| 14 | Lil' Hunter: ~7 s dive, 7/(1+L/2) on loops, summon gate (6−portals)/6, update 61 rework | confirmed | [Lil' Hunter](https://nuclear-throne.fandom.com/wiki/Lil'_Hunter). Update 61 also doubled his HP. |
| 15 | Throne: generators remove half remaining HP and guarantee loop portal; no HP cut on loops | confirmed | [The Nuclear Throne](https://nuclear-throne.fandom.com/wiki/The_Nuclear_Throne). |
| 16 | StS Heart: Invincible 300/turn (200 at A19+), Beat of Death 1–2 | confirmed (cited source weak) | The cited slaythespire.gg page does not state the values. They are confirmed on the [fandom wiki](https://slay-the-spire.fandom.com/wiki/Corrupt_Heart). |
| 17 | Hopoo quote on Mithrix ("Our intent was not for players to avoid good items… we will be changing the last phase") | unsupported by cited source | The cited [Rogueranker](https://rogueranker.com/mithrix-ror2/) page does not contain the quote. A search summary gives a longer version ("…avoid good items, destroy their own build, or to feel bad for picking up powerful items… It is not intended to be the most challenging phase"), likely from Hopoo patch notes, but no primary source was opened. |
| 18 | Brotato: Predator/Invoker 29,250 HP, D5 both at 75% ×1.4; Predator 50%/45 s; Invoker 75%/30 s and 40%/60 s | confirmed (with wiki inconsistency) | Matches [Enemies](https://brotato.wiki.spellsandguns.com/Enemies) (29,250 = 15,000 + 750×19 after patch 1.0.0.3; D5 30,712). The individual [Invoker](https://brotato.wiki.spellsandguns.com/Invoker) page still says 60%/30 s and 29,900 HP (pre-1.0 figures), so treat the 75% figure as likely-current but contested. |
| 19 | VS Reaper 655,350 × level HP, 65,535 damage; Directer phase 2 at +30 s and level ≥7, heads breakable at 60 s and level ≥14, phase 3 at level ≥19 and ≥60 s | confirmed with correction | [The Reaper](https://vampire.survivors.wiki/wiki/The_Reaper), [The Directer](https://vampire.survivors.wiki/wiki/The_Directer). Phase 3 also requires **no Revivals left**, and phase 4 requires level 22 and 45 s. |
| 20 | HoloCure Area 15: "!! indicator along with an audio cue", cone-shaped warning, circular patterns | confirmed | Verbatim on [Area 15 (Bosses)](https://holocure.wiki.gg/wiki/Area_15_(Bosses)). |
| 21 | Taisei GAME.rst quotes (normal attacks, capture condition, survival spells, Spell Practice) | confirmed | Verbatim in [GAME.rst](https://github.com/taisei-project/taisei/blob/master/doc/GAME.rst). |
| 22 | GAG colour guideline title, 8–10% of males, back-up via text/symbol/pattern/shape, presets over whole-screen filters | confirmed | [GAG colour](https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-colour-alone/). The source reads "text or a symbol, pattern or shape"; the notes' list is a light paraphrase. |
| 23 | Pellen: Silksong bosses "decide what they want to do and then move into the correct position to do it" | confirmed | [Military.com](https://www.military.com/off-duty/games/silksong-devs-explain-how-bosses-were-designed-differently-those-hollow-knight.html). |
| 24 | HLD: dash i-frames added, Preston "fair and fluid" quote, health-kit refills rolled back | confirmed | [Kotaku](https://kotaku.com/the-contentious-debate-over-whether-to-make-hyper-light-1772125287). The rollback was partial: warp-pad refills were removed and the healing window was tightened, but the i-frames stayed. |
| 25 | Thakkar "up to 20 different sounds", "grounded a little bit in reality and then stylised" | confirmed | [Thumbsticks](https://www.thumbsticks.com/gdc-17-creating-disturbing-soundscapes-of-hyper-light-drifter/). The 20-sound figure refers to specific weapon sounds (e.g. diamond shotgun), not "every weapon". |
| 26 | Mike Stout telegraph quote and channel list | confirmed | [Game Developer, 2015](https://gamedeveloper.com/design/enemy-attacks-and-telegraphing). |
| 27 | Returnal: "purple = cannot dash through" as a global rule | partially supported | Android Central pages would not render. Independent search confirms that purple lasers and shockwaves cannot be dashed and must be jumped. The broader "everything un-dashable is purple" generalisation remains *(secondary)*. |

**Implausibility skim:** nothing else looked wrong. Delirium's burst escalation ("attack, teleport, and transform at extreme speeds") is verbatim on the Isaac wiki, and the Hush 30-minute Blue Womb limit is confirmed on the Hush page.

**Net corrections to apply in the body:**
- §3.3: Boss Rush requires *beating* Mom within the limit.
- §3.2: Mega Satan's Void portal is 100% in Repentance+, not 50%.
- §6: the Directer's phase 3 also needs zero Revivals.
- §5.8: cite a primary source for the Hopoo quote, or mark it *(secondary)*.
- §7 table: drop "after feedback" for Gungeon's cap raise.
- Brotato: the Invoker's 75%-vs-60% threshold is contested between wiki pages.
