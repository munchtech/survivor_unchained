> Research notes for `docs/bosses/`, kept as written. Where the **Verification** section at the end corrects a claim, the correction stands; `RESEARCH.md` uses the corrected version.

# C2 — Boss fights in Risk of Rain 2, Hades and Hades II

Research strand for Survivor Unchained's boss-fight design document. Every factual claim carries a URL. "(secondary)" marks a claim seen only in a search-result summary, not on the page itself. "Not found" means I looked and could not verify a number.

## Lessons at a glance

1. **Make the boss part of the horde problem, not a replacement for it.** RoR2's Teleporter Boss spawns inside an ongoing horde, ignores the 40-monster cap and must be killed *while* the player holds a 90-second charging circle. Natural spawns stop at 99% charge. Survivor Unchained's 30:00 boss should arrive on top of the swarm, then thin it as the fight resolves.
2. **Protect against god-builds with per-hit taxes and phase gates, not bigger HP.** RoR2 uses adaptive armour (30 armour per 1% of max HP in a single hit, cap 400, decays 40/s). Hades and Hades II use invulnerable phase transitions and "boss damage limits between phases". Hades II adds hit-count barriers (Unrivaled Cerberus: 23 hits). A strong build shortens each phase but still sees every phase.
3. **Stealing the player's tools works only when it is proportional, visible and time-limited.** Mithrix's phase 4 item theft was hated until Hopoo made returns deterministic ("if you have him at 50% health, you will have 50% of your items back") and stated "We want this to be a fun phase, not a frustrating conclusion". Hades II's best inversions are short and readable: Hecate's sheep curse, Eris firing the first game's Rail, and Chronos turning Melinoë back into a child for one dodge-only phase.
4. **Every lethal attack needs a long, unique, multi-sensory tell and an unmistakable safe spot.** Voidling's black hole uses a 3.43 s rear-up and a "thunderous sound". Chronos's 999-damage Time Burst lights the safe numeral. Polyphemus has one glowing limb per move. RoR2's False Son rework added "Audio and Visual effects ... to every different False Son ability" to end "what just happened??" deaths.
5. **Remix bosses by changing the verb, the arena or the partner, not just the numbers.** Hades's Extreme Measures gives Theseus a minigun chariot, frees the Hydra's head and adds sister support casters. Hades II's Vow of Rivals adds Medea, Charybdis, Heracles or Chronos and a new location. Players accept these. They reject remixes that remove information (EM4 Hades's darkness phase: "you just make the screen dark so I can't actually see what's coming?").
6. **Let the arena show the phase.** Examples: Tisiphone's walls close in at 50% and 25%; False Son's arena loses rings; Chronos moves to a clock face; Typhon hides his HP bar but shows wounds on his body. A survivors arena can show phase by shrinking the ember ring, changing ground colour or breaking terrain.
7. **Music and voice can *be* the mechanic.** Scylla and the Sirens lose their instrument from the song when knocked out. Players called it "masterful". Bosses in both Supergiant games and Mithrix taunt, react to the player's tools and comment on loss streaks.
8. **Self-selected difficulty with matching reward is the best answer to the weak-to-absurd build range.** RoR2's Shrine of the Mountain doubles the boss budget and the drops. Hades Heat bounties and Hades II Fear Testaments are tracked per weapon. Survivor Unchained's endless post-30:00 play suits an opt-in "brand" that buffs the boss and the loot.
9. **Tedium kills spectacle.** Voidling is beautiful but "has committed the cardinal sin of being boring": three near-identical phases, very high HP and long gaps between attacks. Polyphemus is resented for punishing one build archetype (melee). The 30:00 boss must not invalidate any drafted weapon family.
10. **Make the win a moment, then a release.** Mithrix's death starts a 3-minute escape with your full build returned. Hades shows a "Boss Vanquished" banner and opens a safe stairway room. Hades II added vanquish presentations for each Guardian and a reward preview before the fight. This maps directly onto the post-win endless phase.

---

## 1. Risk of Rain 2 (Hopoo Games, 2019/2020)

### 1.1 The Teleporter event: a boss fight inside a charging circle

This is the format closest to an ember arena's 30:00 boss, because the boss arrives on top of an ongoing horde and the player is held to a zone.

**How it works** (all from https://riskofrain2.wiki.gg/wiki/Teleporter):

- The player chooses when to start the event by interacting with the Teleporter. Multiple monsters and the Teleporter Boss spawn "after a short delay". A transparent red dome "roughly 120 meters in diameter" marks the charging zone. All interactables outside it (except barrels and scrappers) lock until charging completes.
- Two conditions finish the event: **kill the Teleporter Boss and fully charge the Teleporter.** Charging needs all living players inside the radius. It takes at least **90 seconds** at full speed, scales down with the share of players inside (2 of 4 = 50% speed), and stops if nobody is inside.
- At **99% charge, natural monster spawns stop** on the stage, whether or not the boss is dead. The horde winds down as the objective nears completion.
- Teleporter Bosses and Elites have a **distinctive red health bar**, which marks the boss out from the swarm.
- Reward: one random Uncommon (green) item per player drops from the Teleporter when the boss dies. If the boss has a matching Boss item, each drop has a **15% chance** to be that yellow Boss item instead.

**The director behind it** (https://riskofrain2.wiki.gg/wiki/Directors):

- The Teleporter Boss Director activates **3 seconds** after the event starts and gets a one-off budget of `600 × sqrt(coeff) × (1 + shrineMountainStacks)` credits. Here `coeff` is the run's difficulty coefficient (§1.5).
- It first picks a card from the "Champions" (boss) category. If the budget is far too big or too small for any champion, it falls back to any monster. That gives a **"Horde of Many"**: a pack of elite non-boss monsters billed as the boss. The wiki notes that "in a very late run even Champion monsters will be deemed too cheap and only Scavengers will spawn."
- With a big budget, the director buys **elite tiers** before it buys more bodies. It can spawn up to 6 of the same card per wave.
- The boss **ignores the 40-monster cap** that blocks normal spawns, so it always arrives even in a saturated horde.
- A Teleporter Boss's HP multiplier is **multiplied by the number of living players**.
- Separately, a Teleporter Director spawns regular monsters for the whole charge and switches off when charging completes.

**Opt-in difficulty for reward.** A Shrine of the Mountain, activated before the event, gives the boss director +100% credits per shrine. It also adds an extra copy of each Teleporter drop: items = `players × (1 + shrines)`. Extra credits can turn "6 Imp Overlords" into "a single Overloading Worm" or one elite Overlord (https://riskofrain2.wiki.gg/wiki/Shrine_of_the_Mountain). The player bets on their own build. Strong players take more danger in exchange for more loot, so the shrine works as a self-selected difficulty dial.

**Eclipse 2** halves the radius of every holdout zone, "Note that this means that the ground area inside the radius is reduced by 75%" (https://riskofrain2.wiki.gg/wiki/Eclipse). The circle itself is the difficulty lever. The modifier makes the same boss harder by taking away space to kite the horde, without touching boss stats.

**Why it works:**

1. The **boss and the horde are one problem**. You cannot leave the circle to kite the boss without stopping the charge, so swarm control and boss dodging compete for the same space.
2. **Two clocks**: the 90-second minimum charge and the boss's HP. A strong build kills the boss in seconds but still has to hold the zone, so the event never becomes nothing. A weak build may finish charging and still face the boss, but natural spawns have stopped at 99%, so the arena calms down for the duel.
3. **The red bar** is the main readability tool for picking the boss out of a crowd.

### 1.2 Mithrix (final boss, Commencement)

Mithrix is a four-phase fight on a large circular arena at the top of the moon. All mechanics below are from https://riskofrain2.wiki.gg/wiki/Mithrix unless noted otherwise.

**Stats and build-proofing**

- Base health: 1000 (+300 per level) in Early Access. Raised to 1400 (+420) in the Anniversary Update, then lowered again in Survivors of the Void. The wiki marks that last change "(Undocumented)": 1400 (+420) ⇒ 1000 (+300) (https://riskofrain2.wiki.gg/wiki/Mithrix, Version History).
- In phases 1 and 3, Mithrix has **adaptive armour** and **unique scaling**:
  - **Adaptive armour.** Each hit grants temporary armour equal to `3000 × damage/maxHP`, i.e. "30 armor per 1% of the max HP dealt". It caps at **400** and decays at **40 per second**. Voidling, False Son and the Solus bosses share it (https://riskofrain2.wiki.gg/wiki/Armor). This is RoR2's main answer to one-shot builds. Burst damage is taxed heavily, sustained damage much less.
  - **Unique scaling.** Boss HP is `× round((1 + coeff/2.5) × sqrt(livingPlayers) × 10)/10` and damage is `× round((1 + coeff/30) × 10)/10`, "so these enemies will remain competitive even after reaching their level 99 cap, as the coeff keeps growing" (https://riskofrain2.wiki.gg/wiki/Difficulty).
- **Stagger.** The Anniversary Update added a stagger state on large hits. In phase 4, "any single instance of damage that deals more than 30% of his health will also stagger him."

**Phase 1: the duel.** Mithrix drops in. Attacks:

| Attack | Telegraph | Damage | Cooldown |
|---|---|---|---|
| Hammer Smash | Stops and winds up | 1200% direct + 1200% blast, 12 m radius with falloff | 4 s cooldown; the whole attack lasts 4 s, during which he is open to hits |
| Needle Barrage (while sprinting, >70 m away, <80% HP) | Sprint | 12 homing needles at 120 m/s, 60% each | 6 s |
| Hammer Swing | — | 200% plus knockback | 5 s |
| Dash | — | 0.3 s dash; 2 charges; cleanses timed debuffs | 3 s |
| Shock Wave (below 75% HP) | Crouches 1 s, leaps, airborne 3 s with invulnerability, then slams down at the arena centre | 12 concentric waves at 60 m/s for 3 s, 400% each, applies Cripple | 30 s |

Behaviour is distance-gated: smash within 35 m, needles beyond 70 m. Attack choice therefore depends on how the player positions.

**Phase 2: the boss leaves and the horde becomes the fight.** "Mithrix leaves the arena, and several stone pillars rise up around the arena". 2 Lunar Chimera Golems and 4 Lunar Chimera Wisps spawn, a dedicated Combat Director keeps spawning Lunar enemies, and "All spawned enemies must be defeated to complete this phase." The arena also changes: the pillars give cover (and a well-known cheese, since Mithrix cannot climb them).

**Phase 3: the boss returns powered up.** The hammer glows blue and Lunar enemies keep spawning. Hammer Smash now also sends 3 small shockwaves forward. It also leaves a **lingering blue fire pillar** at the impact point: 75% damage, ticking 6 times per second for **45 s**, 40 m tall, passing through terrain. The arena slowly fills with hazards Mithrix has placed himself. After each Shock Wave comes **"Big Spinny" / "Forbidden Pizza"**: 9 rotating flame spokes that deal 900% after 3 s, repeated 5 times with random rotation direction. The name is a running developer joke ("Developer Note: No, it isn't. Community Manager Note: Yes, it is." — v1.3.8 notes quoted on the same page).

**Phase 4: the inversion (item theft).** "Mithrix appears at the center of the arena and looks weakened with his armor broken and his hammer gone. He starts by stealing all players' and their allies' items, during which time he is invulnerable. Damaging him will release the items."

- Mechanics (wiki Notes):
  - Step 1 steals one item from every player and minion every 0.2 s for 9 s.
  - Step 2 steals one every 0.1 s until none are left.
  - In solo, he effectively uses up to **38** items, taken from step 1. Items on a blacklist (e.g. Tougher Times, Razorwire, and after a patch Mired Urn and Crowbar) are taken but not used.
  - Items return as damage accumulates. The threshold per item is capped at 1/100 of his max HP.
- Visual tell: "he will gain spikes on parts of his body, colored accordingly to the stolen item's rarity." The theft is shown on his body, in the item-rarity colours the player already knows.
- He moves slowly, uses only ranged attacks, and loses unique scaling, "his max HP will be significantly lower".
- Lunar Orbs: a 600% blast plus 8 orbs that spiral out, back in and out again, 9 s lifetime. Each cast also deals **8% of his current HP to himself**.
- Steal-specific interactions: he will use your Dio's Best Friend (extra life), Captain's Defensive Microbots, Medkits, and your Empathy Cores or Queen's Gland allies against you.

**How Hopoo responded to criticism.** The developer notes in PC Patch v1.0.1.1, quoted on the wiki's version history (https://riskofrain2.wiki.gg/wiki/Mithrix):

> "The goal with these changes is to make the final phase of the fight more consistent, fix a few softlock scenarios, and to remove a few cheeses. The expectation is that with these changes, the final phase (and only the final phase) will be much easier. We want this to be a fun phase, not a frustrating conclusion."

Concrete changes:

- **Removed unique scaling** from phase 4: "Expect him to have less than half of the current live build".
- Lunar Shard projectile cone narrowed from **20° to 0.5°** "to reduce the chance you randomly get hit by a stray shot".
- Energy Ball damage cut from 1000% to 700%, with a **stronger glow "to make it more visually noticeable, especially when swinging around corners"**.
- Immunity while channelling the steal.
- Some items blacklisted from his use "that can cause softlocks or impossible scenarios".

The Anniversary Update then made returns deterministic: items "Now consistently returns items as you deal damage, rather than randomly, i.e if you have him at 50% health, you will have 50% of your items back". Items now come back round-robin in multiplayer and in the order they were found.

The arc of the fixes is the lesson. Hopoo kept the "your own build turned against you" idea but made it **proportional and predictable**. They removed random returns, narrowed the projectile spread so damage felt fair, and boosted visibility.

**Player opinion.** Mixed for years. In a Steam thread on Voidling (4 March 2022), one player says "I still hate Mithrix final phase. So while Voidling isn't amazing I still prefer that boss fight to Mithrix." (https://steamcommunity.com/app/632360/discussions/0/3189116454990708305). Search summaries of other threads report players scrapping items such as Shurikens and Tesla Coils before the fight so Mithrix cannot use them, and the complaint that the phase "punishes you for doing well" (secondary: a search summary drawing on several Steam threads, including https://steamcommunity.com/app/632360/discussions/0/3183489348309127174 and https://steamcommunity.com/app/632360/discussions/0/4085282327474541899; the exact thread was not verified). The theft also visibly confuses players. The opening post of https://steamcommunity.com/app/632360/discussions/0/4085282327474541899, "if you have too many items Mithrix doesnt give any of them back (BUG)", came from a player who did not understand the damage-for-items return rule (fetched).

**Dialogue as a taunting layer.** Mithrix "speaks throughout his fight, with his quotes appearing in the chat box". Lines change by phase and situation:

- Spawn: "Pray." "Beg." "Die."
- Phase 4, in capitals: "WEAK, WITHOUT YOUR BAUBLES AND TRINKETS."
- On spotting a Halcyon Seed ally: "THE GUARDIAN...? IMPOSSIBLE...!"
- Death: "BROTHER... PERHAPS... WE WILL GET IT RIGHT... NEXT TIME..."

(https://riskofrain2.wiki.gg/wiki/Mithrix). The theme track is "You're Gonna Need a Bigger Ukulele" (same page).

**Victory moment: an escape sequence, not a loot shower.**

- Stolen items return.
- "the moon begins a detonation sequence with an on-screen countdown".
- The player jumps into one of 5 (of 12) floating portals and has **3 minutes** to reach the Rescue Ship and hold its zone for **1 minute**. Fire walls and Void Reavers and Chimeras chase you.
- The run awards 10 Lunar Coins.

(https://riskofrain2.wiki.gg/wiki/Mithrix). The win is followed by a short, frantic victory lap with your full build back. Survivor Unchained could borrow this for the post-30:00 "endless" transition.

### 1.3 Voidling (alternate final boss, Survivors of the Void)

Source for mechanics: https://riskofrain2.wiki.gg/wiki/Voidling

- **Three phases**, each adding one attack. Phase 1: homing swarm, 30 missiles over 5 bursts; laser burst, whose last shot leaves a void pool ticking for 45 s; sweeping beam, 8 s rotation, 400 m range, passes through terrain. Phase 2 adds the special.
- **Phase transitions are chases.** The Voidling retreats into a rift and the arena fills with strong Void Fog. The player follows through a short **platforming challenge** to a random arena themed after earlier stages (Titanic Plains, Distant Roost, Abyssal Depths and others). Passing the blue portal between phases heals you fully.
- **Horde interaction.** From phase 2, small monsters "captured in the Void" spawn. "these monsters are also hostile to the Voidling and vice versa, potentially drawing the Voidling's attention and luring away its homing attacks". The horde is a three-way faction, not just adds.
- **Nullifier Black Hole** (below 40% HP, 60 s cooldown):
  - Telegraph: it "rears up to nearly its full height for 3.43 seconds before opening up its entire body and emitting a telltale thunderous sound".
  - A 50 m sphere pulls the player in for 10 s and is "instantly fatal on contact". It ignores invulnerability and extra lives.
  - The long, loud tell is what justifies an instant kill.
- **Phase 3 arena change.** The fog stays and the Voidling projects a **150 m safe bubble around itself**. Anything outside takes suffocation damage, so you are forced to stay close.
- **Victory.** The air clears, a purple portal opens, and the "Fate Unknown" ending plays. The run awards 10 Lunar Coins.

**Player opinion** ("Thoughts on Voidling?", 4 March 2022, https://steamcommunity.com/app/632360/discussions/0/3189116454990708305):

- "Voidling has committed the cardinal sin of being boring, and i can not forgive him for that."
- "With a very repetitive, slow fight and harder path to reach him, I don't really see any point in going to fight him over Mithrix."
- "His homing missiles just feel bs, the death ball attack seems like a death sentence for a lot of survivors, mainly melee, and his hp scaling is absurd."
- "thing still had an exorbitant amount of health to the point that it just got more after each phase."
- Positive: "I really like seeing the enemies spawn in and try fighting the voidling in later phases which is kinda cool."

Lesson: a high-HP boss with three near-identical phases and long breaks between attacks reads as tedious, however good it looks. The one thing players single out as cool is the horde fighting the boss.

### 1.4 False Son (alternate final boss, Seekers of the Storm)

Source: https://riskofrain2.wiki.gg/wiki/False_Son_(Boss)

- **The arena shrinks by phase.** "the first of which starts with an extended arena and further phases remove successive parts of it." A fog floor teleports fallers back up.
- **Cleansing stations.** Up to 4 Aurelionite Geodes in the arena regenerate 30 s after use. They are needed to cleanse his debuffs.
- **Phase 1.** Fissure Slam: 0.5 s wind-up, then 5 fissure columns moving at 12 m/s for 7 s. Corrupted Paths: a 0.8 s coil, then a dash that chains straight into a slam. Tainted Offering: a 9-projectile shotgun that applies the Lunar Ruin damage-over-time.
- **Phase 2.**
  - 5 Stone Golems spawn and are kept topped up to 5.
  - **Lunar Rain**: "7 warning spots are highlighted on the ground", pillars land after **3.5 s**, and the pillars become cover. After **21 s** they glow for a **2-second warning** before exploding. The boss's attack builds cover that later turns into a hazard.
  - **Laser Gaze**: he leaps and the giant Providence statue in the background fires one beam per player. The beam tracks for 2 s, then locks on "with perfect precision and the only way to avoid it is to get behind cover". The arena itself attacks.
- **Phase 3.**
  - Golems die and the gaze is "charged" (blue, +150% damage).
  - **Prime Devastator** sends homing lightning that applies **Disable All Skills for 420 s**. It can only be cleansed at a Geode.
- **Inversion of Mithrix's theft.** "If the player has Halcyon Seed in their inventory, the False Son will steal it and summon Aurelionite as his ally, an inversion of the final phase with Mithrix where Aurelionite is summoned to aid you." Taking that harder fight improves the reward: item rarity rises from 80% Uncommon / 20% Legendary to 60% Boss / 40% Legendary.
- **Victory.** "the storm clears and northern lights can be seen in the sky". Each player gets a pick-one-of-three item fragment. A Shrine of Rebirth lets you either continue the run or end it.

**Developer rework (Dev Diary 8, https://devtrackers.gg/risk-of-rain/p/e20a61e8-dev-diary-8-seekers-of-the-storm-roadmap-phase-2-false-son-boss-fight).** After launch criticism the team stated these goals:

- "no more 'what just happened??' moments"
- Telegraphs that "will now better telegraph attacks across every phase of the fight. The goal of this change is to make his attacks a tad more predictable."
- "Audio and Visual effects have been added to every different False Son ability. Again this is to better communicate to players which of his abilities he has just used or is about to use."
- "The laser damage has also been re-balanced to ramp up quickly but still give you time to either get to - or move between - cover."
- Golem adds "capped at 5 maximum active at a time".
- Adaptive Armor added "so he should still be challenging pre-loop, but will no longer be one-shot-able after looping!"

This is a direct case study for Survivor Unchained. The fixes were per-ability audio/visual signatures, ramping (not instant) damage on unavoidable beams, a cap on adds, and burst protection against god-builds.

### 1.5 The difficulty timer and how bosses scale with it

From https://riskofrain2.wiki.gg/wiki/Difficulty:

- `coeff = (playerFactor + minutes × 0.0506 × difficultyValue × players^0.2) × 1.15^stagesCompleted`. difficultyValue is 1/2/3 for Drizzle/Rainstorm/Monsoon.
- The HUD bar passes through named tiers: Easy, Normal, Hard, Very Hard, Insane, Impossible, "I SEE YOU", "I'M COMING FOR YOU", "HAHAHAHA". The label itself becomes the menace cue.
- Enemy level is `1 + (coeff − playerFactor)/0.33`. Each level gives **+30% HP and +20% damage**, capped at level 99. Every level-up plays "a visual effect and a level-up sound similar to a player level-up, although with a lower pitch". The player is told the horde got stronger.
- Teleporter bosses scale through this level plus `sqrt(coeff)` boss credits, which buy elite tiers or extra bosses. Special bosses add unique scaling on top (above).

The time pressure is the enrage. RoR2 has no per-fight enrage timer. The whole run's clock makes every boss tougher the longer you dawdle, which also discourages farming. For Survivor Unchained, which already has a 30-minute clock, the parallel is to make the 30:00 boss's stats depend on the arena clock (endless play continues it) rather than a fixed value.

### 1.6 RoR2 takeaways for Survivor Unchained

| RoR2 mechanism | What it solves | Ember-arena translation |
|---|---|---|
| Boss spawns into the existing horde, ignores the monster cap, and has a red bar | Boss always arrives and stays findable in a crowd | 30:00 boss bypasses the enemy cap; give it a unique bar colour and an off-screen pointer |
| Holdout circle + 90 s charge + boss kill both required | Strong builds cannot skip the event entirely | Pair the 30:00 boss with a positional objective (e.g. keep a brazier lit) so god-builds still have something to do |
| Spawns stop at 99% charge | Gives the duel a calm finale | Thin the horde in the boss's final phase, or after a phase threshold |
| Shrine of the Mountain (opt-in: +100% boss budget, +1 drop each) | Self-selected difficulty with matching reward | Optional "ember brand" before 30:00 that buffs the boss and adds loot |
| Adaptive armour (30 armour per 1% max HP taken, cap 400, decays 40/s) | Burst/one-shot builds | A per-hit damage-share tax that sustained DPS barely feels |
| Mithrix P4 item theft, made proportional (50% HP = 50% items back) | Inverts the build in a readable, recoverable way | A "Thief of Embers" phase that borrows drafted weapons, returns one per HP chunk, and shows each stolen weapon on the boss's body |
| Developer fixes: narrower cones, stronger glow, per-ability SFX/VFX, capped adds | "What just happened??" deaths | Budget one unique sound and one unique ground decal per boss ability |

---

## 2. Hades (Supergiant Games, 2020)

Hades bosses are hand-authored duels at the end of each region. Unlike RoR2, their HP does not scale with time or with the player's build. Difficulty comes from the player-chosen **Heat** (Pact of Punishment), and in particular from **Extreme Measures**, which remixes each boss.

### 2.1 Boss roster: numbers, phases, adds

| Boss | Base HP (EM HP) | Phase thresholds | Adds / arena | Source |
|---|---|---|---|---|
| Megaera | 4,400 (4,800) | Volley and Flame unlock at 75%/50% (order random); summons at 75/50/25%, with brief invulnerability and a summoning animation at each | Thugs and Witches; pillars plus spike traps | https://hades.fandom.com/wiki/Furies |
| Alecto | 4,600 (4,900) | 75% Lightning Chase, 50% Whip Shot, 25% "Perma-Rage" | 1–2 Louts; **Rage meter** fills from damage taken or her own Build Rage, and a full meter unlocks all abilities briefly | same |
| Tisiphone | 5,200 (5,600) | 67% / 33% unlocks; walls **close in** at 50% and 25% after a fade to black | No adds; the arena shrinks | same |
| Bone Hydra | 6,000 main; support heads 820 (410 armour + 410 health) | At 66%: 3 support heads; at 33%: 6 support heads. The main head is **invulnerable until the support heads die** | 4 colour-coded main-head variants after 3 kills | https://hades.fandom.com/wiki/Bone_Hydra |
| Theseus | 9,000 (12,000) | 50%: calls **Olympian Aid** | Duo with Asterius; spectators | https://hades.fandom.com/wiki/Theseus/Combat |
| Asterius | 14,000 (16,000) | 50%: two new moves; as mid-boss he leaves at 20% | Starts the Stadium at 11,200 if beaten earlier in the run | https://hades.fandom.com/wiki/Asterius/Combat |
| Hades | 17,000 per health bar; EM4 22,000 for bars 1/2 and 17,600 for bar 3 | Summons Infernal elites at 70% and 40% lost; a second bar refills after a "defeat" | Urns/vases, cover pillars | https://hades.fandom.com/wiki/Hades/Combat (the HP figure comes from a Reddit post cited by the wiki) |
| Charon (secret) | 16,500 ("effectively 13,200") | Impervious at 75% and 45%; ends the fight at 20% | Triggered by **stealing** his 300-obol sack (22% shop chance); **same difficulty in every region** | https://hades.fandom.com/wiki/Charon/Combat |

**Phase gating as build protection.** Hades never scales boss HP to the player. It does gate phases. Every threshold above gives "brief invulnerability", and support heads make the Hydra invulnerable until they are cleared. An early-access patch note reads "Fixed rare cases where **boss damage limits between phases** could be bypassed at the start of fights" (Early Access Patch 043, https://store.steampowered.com/news/app/1145360/view/2698159409992734118). An overpowered build therefore shortens each phase but still sees every phase, transition and summon. Deliberate exceptions exist. Demeter's Winter Harvest execute got its own boss-kill presentation ("Added new visual presentation when vanquishing bosses with Winter Harvest (Demeter)", Patch 039, https://store.steampowered.com/news/app/1145360/view/2597949245066272359). Charon's flat difficulty also rewards fighting him late with a strong build (https://hades.fandom.com/wiki/Charon/Combat).

### 2.2 How each fight is built

- **Megaera** is the tutorial boss. She has two starter moves, then one new move per quarter of HP. The "Flame" circles "Sometimes ... do not cover Zagreus's current position in an attempt to trick him into dodging into the circles" (https://hades.fandom.com/wiki/Furies). This deliberately punishes panic-dashing.
- **Alecto** adds a visible **meter** as an enrage. Damage you deal fills her Rage, so aggression is risky. You can interrupt her Build Rage by hitting her. Below 25% she stays enraged permanently (same source). In The Long Winter Update, Supergiant "reworked her Rage Gauge (you can knock her out of her rage-building move, but watch out)" (https://store.steampowered.com/news/app/1145360/view/3690071589859860255).
- **Tisiphone** has no adds. The **arena itself shrinks** twice, with a fade-to-black transition (same Furies source). She was trimmed at v1.0: "this battle now has one fewer phases" (https://store.steampowered.com/news/app/1145360/view/3819572206267800157).
- **Bone Hydra** comes from myth: Eduardo Gorinstein cites "the Hydra's mythological trait of having to sever side heads" (secondary, https://digipen.edu/showcase/news/eduardo-gorinstein-delivers-challenge-and-fun-hades).
  - The support heads are colour-coded by role: yellow volley, white-blue slam, orange magma, green summoner, purple waves (https://hades.fandom.com/wiki/Bone_Hydra).
  - Once you have killed it three times, the main head can take one of those colours and gain that head's attack.
  - The Blood Price Update notes: "each type of head is more distinct" (https://store.steampowered.com/news/app/1145360/view/3384966595888900267).
  - The Long Winter Update made it "faster though deadlier to compensate; one fewer phase; removed urns containing health (the Hydra finally realized they were there and ate them)" (https://store.steampowered.com/news/app/1145360/view/3690071589859860255).
- **Theseus and Asterius** is a two-boss tag team with crowd theatre.
  - Theseus's frontal shield blocks attacks, so the player has to flank.
  - Asterius throws Theseus ("Bullhorn"), and Theseus's "Delta Strike" bounces Asterius's charge off his shield into a room-wide wave (https://hades.fandom.com/wiki/Theseus/Combat).
  - Killing one **enrages the survivor**: faster movement and attacks.
  - Gorinstein: "The thing I was proudest of was the Theseus and Minotaur boss fight ... each character has their own personality in their attack styles" (https://digipen.edu/showcase/news/eduardo-gorinstein-delivers-challenge-and-fun-hades).
- **Hades** is a two-bar fight.
  - Phase 1 uses Darkness: he turns invisible, and "his footsteps can be seen on the snow", so there is still a readable tell.
  - At "death" he "will pause as though defeated, before regaining his strength, refilling his health bar". Phase 2 adds rotating lasers blocked by cover and vases that become stun traps (https://hades.fandom.com/wiki/Hades/Combat).

### 2.3 Bosses that turn the player's own tools against them

Hades does this more subtly than Mithrix. Bosses borrow the *vocabulary* of the player's kit rather than the items themselves.

- **Hades fires the player's own Cast.** "Skull Cast: Similar to Zagreus' bloodstone ability". It sticks to Zagreus and applies Boiling Blood (+100% damage taken), and if not destroyed within 5 s it "will detonate" (https://hades.fandom.com/wiki/Hades/Combat). In phase 2 he gets a refill, much like the player's Death Defiance.
- **Theseus summons the player's patrons.** At 50% he calls a random Olympian, but "Theseus can only call for aid from an Olympian who has not yet given Zagreus a boon in the current run". His attacks then apply that god's curse (Weak, Doom, Chill, Jolted and so on) (https://hades.fandom.com/wiki/Theseus/Combat). The boon system is turned into an attacker. v1.0 added "each Olympian's aid also imbues his spear with special properties" (https://store.steampowered.com/news/app/1145360/view/3819572206267800157).
- **Theseus also comments on your tools.** If Zagreus uses a Greater Call, Theseus shouts "You cheat!" or "Deceiver!". He also has reactions to individual weapon aspects (https://hades.fandom.com/wiki/Theseus/Quotes).

### 2.4 Heat and Extreme Measures: the boss-remix dial

The Pact of Punishment has 15 conditions (16 in Hell Mode). Each adds Heat. **Extreme Measures** remixes one region's boss per rank and costs 1/2/3/4 Heat for ranks 1–4, 10 in total (https://hades.fandom.com/wiki/Pact_of_Punishment). Other Pact conditions that hit bosses directly are Hard Labor (+20% enemy damage per rank), Calisthenics Program (+15% HP per rank), Forced Overtime (+20% speed per rank, 3 Heat each), Damage Control (shield hits) and **Tight Deadline**. Tight Deadline gives 9 minutes per region, minus 2 per rank; once time runs out "Zagreus takes 5 damage every second ... cannot be reduced in any way". The timer **pauses after a region's boss is defeated** (same source). This is the closest Hades gets to an enrage timer.

| Rank | Boss | Extreme Measures remix |
|---|---|---|
| EM1 | Furies | HP up (Meg 4,800 / Alecto 4,900 / Tisiphone 5,600). One or two **undamageable "support sisters"** join and cast two signature moves each. Tisiphone's support also casts **fog that hides parts of the arena** (https://hades.fandom.com/wiki/Furies) |
| EM2 | Bone Hydra | New smaller arena split by magma streams, with breakable pillars. At 66% the head **"shatter[s] the neck"** and chases the player around the arena (https://hades.fandom.com/wiki/Bone_Hydra) |
| EM3 | Theseus & Asterius | Theseus (12,000 HP) rides a "Macedonian Tau-Lambda" chariot with **twin miniguns**, cluster bombs and a centre dive. At 33% the chariot breaks and he reverts to his normal moveset. His Olympian line becomes "Olympus, please avenge my chariot!" Asterius (16,000) wears bronze power armour, gets rocket-boosted Bull Rush and an Axe Spin that destroys pillars (https://hades.fandom.com/wiki/Theseus/Combat, https://hades.fandom.com/wiki/Asterius/Combat, https://hades.fandom.com/wiki/Theseus/Quotes) |
| EM4 ("Extremer Measures") | Hades | Added at v1.0: "can you withstand the full unbridled power of the Final Boss?" (https://store.steampowered.com/news/app/1145360/view/3819572206267800157). HP rises to 22,000/22,000/17,600 across **three** phases. He gains a spear throw, Infernal mini-boss summons, a **Cerberus stampede** with falling rocks (50 base damage), and **vase healing in pulses of 1,500 HP**. In phase 3 he "covers the entire field in darkness, limiting visibility to the immediate area where Zagreus stands" (https://hades.fandom.com/wiki/Hades/Combat) |

Why the remixes work: each one keeps the boss's identity (Theseus is still a vain showman, Hydra is still heads) but changes the **arena and the core verb** (chariot instead of spear, a free-roaming head instead of a tethered one). Players get a new fight without new characters. They also come with matching dialogue: Theseus has 7 dialogue sets for "Extreme Measures Active" and a set for "Extreme Measures Inactive" (https://hades.fandom.com/wiki/Theseus/Quotes).

**Where it failed: EM4 darkness.** Steam thread, 16 November 2020 (https://steamcommunity.com/app/1145360/discussions/0/2980782118455128257):

- Against: "The final obstacle is that you just make the screen dark so I can't actually see what's coming?"
- Against, on another EM4 element: "The adds so tanky that it deletes most builds and weapon combinations from the game."
- For: "I enjoyed his third stage. I thought it made it interesting, since it becomes more about managing information and prediction."
- For: "extreme measures 4 Hades is designed to be artificial difficulty".

Lesson: taking away **visibility** in a bullet-hell game feels like taking away agency. Taking away **space** (Tisiphone) or adding a **new verb** (chariot) does not.

**Rewards for Heat.** "You earn one Bounty the first time you vanquish the boss of each Underworld region while your Heat Gauge is full", tracked **per weapon**. Bosses drop Titan Blood, Diamond or Ambrosia at Target Heat, or otherwise flat Darkness: 50 for the Furies, 100 for the Hydra, 150 for Theseus (https://hades.fandom.com/wiki/Pact_of_Punishment, https://hades.fandom.com/wiki/Furies, https://hades.fandom.com/wiki/Theseus/Combat). The top cosmetic rewards for 8/16/32 Heat are statues, which the wiki notes are "much to the disappointment of Zagreus (and perhaps also the player)" (Pact page).

### 2.5 Telegraph language, dialogue, music and victory

- **Telegraphs.** The language is consistent: a ground circle/decal that fills, then detonates. Megaera's Flame, Alecto's Lightning Chase, Tisiphone's lines of circles and all of Theseus's Olympian Aid patterns are "damaging circles ... doing damage if Zagreus stands in them when they activate", with each god's pattern given its own shape (ring, chain, spiral, sweep) (https://hades.fandom.com/wiki/Theseus/Combat). Theseus's spear throw puts a **crosshair** on Zagreus (same). Hades's spin attack "marks an area around him" first (https://hades.fandom.com/wiki/Hades/Combat). Patches kept polishing telegraphs:
  - "The Minotaur: whirlwind attack telegraphs more distinctly while under Extreme Measures" (v1.0, https://store.steampowered.com/news/app/1145360/view/3819572206267800157)
  - "Added emote for when the Minotaur sets up the 'Bull Horn' combo attack" (https://store.steampowered.com/news/app/1145360/view/3856733252025299436)
  - "Updated, clearer cover layout in the Final Boss chamber" (https://store.steampowered.com/news/app/1145360/view/2579938650942085981)
- **Dialogue around fights.** Each boss has an authored pre-fight exchange that reflects history: Theseus alone has 15 numbered pre-fight dialogues plus situational sets (https://hades.fandom.com/wiki/Theseus/Quotes). There is also **fight banter** for attacking, taunting, addressing the audience ("They love us, Asterius!!"), calling gods, getting hit and critical health ("Urgh, this is absurd!") (same). Patches track "losing-streak events for certain bosses", so bosses comment when you keep dying to them (https://store.steampowered.com/news/app/1145360/view/2698159409992734118).
- **Victory moment.** Supergiant added "unique visuals for text presentation when Zagreus vanquishes a boss" and updated the "'There Is No Escape' and 'Boss Vanquished' messages" with new sound (https://store.steampowered.com/news/app/1145360/view/2579938650946470034, https://store.steampowered.com/news/app/1145360/view/2698159409992734118).
  - The reward drops in the room. The far door opens onto a stairway room with a fountain, a Well of Charon, a Pool of Purging and the keepsake case (https://hades.fandom.com/wiki/Furies).
  - After the final fight, "A weakened Hades asks Zagreus to tell his mother that Cerberus is fine" and Zagreus reaches the surface (https://hades.fandom.com/wiki/Hades).
- **Player opinion.** The Elysium duo is widely seen as the hardest regular boss and a difficulty spike. Players note that "EM Asterius is a menace" while EM Theseus is easier (secondary, search summary of https://steamcommunity.com/app/1145360/discussions/0/2965020518365342342 and related threads).

---

## 3. Hades II (Supergiant Games, early access 2024, v1.0 September 2025)

Hades II has two routes (Underworld and Surface), each with four regional **Guardians**. Supergiant described them in The Warsong Update announcement: "The boss battles at the end of each Region are an integral part of the experience, and we want them to be able to challenge and surprise you even more." (https://store.steampowered.com/news/app/1145350/view/1792116353167296).

### 3.1 Guardian roster

| Guardian (route) | HP | Structure | Signature idea | Source |
|---|---|---|---|---|
| Hecate (Underworld 1, Erebus) | 5,800 | Two phases. At one-third HP lost she becomes invulnerable and summons Sisters of the Dead, who must die to break her immunity | **Uses the player's Hexes**: Total Eclipse, Lunar Ray and **Twilight Curse, which turns Melinoë into a sheep** (slower, short dash with no i-frames) | https://hades.fandom.com/wiki/Hecate/Combat |
| Scylla and the Sirens (UW2, Oceanus) | Scylla 6,550, Jetty 4,200, Roxy 5,950 (shared pool) | Damage takes each member out until the next phase; phase 2 picks a **"Featured Artist"** who is empowered; Pinhead horde at 10% | **The band is the boss and the soundtrack** | https://hades.fandom.com/wiki/Scylla/Combat |
| Infernal Cerberus (UW3, Mourning Fields) | 21,500 (31,500 Unrivaled) | At 50% he burrows and sends one elite reinforcement group; phase 2 starts when they are dead | Ground circles with "a visual cue for when they expire" | https://hades.fandom.com/wiki/Cerberus/Combat |
| Chronos (UW4, House of Hades) | 20,000, then 16,000 (Unrivaled adds 26,000) | Phase 1 with 6 Satyr Supplicants; at 0% he refills and moves the fight to a **clock-face arena** | Time Burst: 999 damage with one safe numeral lit on the clock | https://hades.fandom.com/wiki/Chronos/Combat |
| Polyphemus (Surface 1, Ephyra) | 8,400 | Phase 2 at 75%: Lubbers, Shamblers, sheep | **Colour tells on limbs**; "Where Are You?" counter stance | https://hades.fandom.com/wiki/Polyphemus/Combat |
| Eris (S2, Rift of Thessaly) | 16,000 | 2 core phases + 2 buff phases, each **+100% damage** | **Wields Zagreus's Adamant Rail** (Aspect of Eris) | https://hades.fandom.com/wiki/Eris/Combat |
| Prometheus (S3, Olympus) | 33,000 (36,000 Unrivaled) | 66% / 33% | "Enhanced" variants; **foresees and dodges** big hits; camera-zoom Flame Strike | https://hades.fandom.com/wiki/Prometheus/Combat |
| Typhon (S4, Summit) | 65,000 in total (12,500 / 15,000 / 12,500 / 25,000) | Four phases shown by **visible wounds**; **health bar hidden** | Eggs hatch into elites; Zeus intervenes in phase 3 | https://hades.fandom.com/wiki/Typhon/Combat |

### 3.2 Telegraphs and readability

- **Polyphemus's glowing limbs**: "his hands or feet will glow red whenever he performs certain attacks: Right Hand Glow: Slam; Feet Glow: Leap; Both Hands Glow: Grab; Right Foot Glow: Kick; Left Foot Glow: Stomp" (https://hades.fandom.com/wiki/Polyphemus/Combat). Each move has its own body-part tell, readable even in a crowd.
- **Polyphemus's "Where Are You?"** turns damage into the trigger. While he cups his ear, "receiving most sources of damage will trigger a counterattack": a boulder falls where you stood. The wiki lists which of the player's **auto-damage sources** (familiars, hexes, boon effects such as Zeus lightning or Poseidon waves) still trigger him, and which damage-over-time effects (Scorch, Hitch) do not (same). For a survivors-style game, where most damage is automatic, this is a warning. A "don't attack now" boss move conflicts with auto-firing weapons unless you either exempt passive damage or let the player suppress it.
- **Eris's previews.** Her rocket bomb shows "the purple arrow on the ground", cluster bombs show crosshairs, and aerial bombardment marks the ground first. Patches added "improved feedback on where she is aiming with some Rail attacks" and "improved previews of her various attacks" (https://hades.fandom.com/wiki/Eris/Combat; Patch 6, https://store.steampowered.com/news/app/1145350/view/6212245217911828345; Warsong notes, https://store.steampowered.com/news/app/1145350/view/1792116353167292).
- **Chronos's lethal Time Burst** "deals 999 damage". The room darkens and "a safe zone will appear on one of the clock's numbers, which is indicated by a burst of light on the ground" (https://hades.fandom.com/wiki/Chronos/Combat). An instant-kill attack is fair only if the safe spot is unmistakable. Supergiant twice fixed it hitting players in the safe point ("Fixed deadliest attack of Chronos occasionally hitting when Melinoë was in a supposedly safe point", Patch 2). They also fixed the reverse: "Fixed the deadliest attack of Chronos being easier to evade than intended" (Patch 3) (https://store.steampowered.com/news/app/1145350/view/5742731639349105637, https://store.steampowered.com/news/app/1145350/view/5842939267306502875).
- **Prometheus's Flame Strike** pulls the camera back: "He jumps out of the arena and into the foreground, zooms the camera out, and displays indicators". There are 3 sets of top/middle/bottom indicators at 66% and 5 sets at 33%, then fire sweeps in the same pattern. It also "All persistent flames left by other attacks disappear as this attack begins" (https://hades.fandom.com/wiki/Prometheus/Combat). The memory test resets arena clutter. His **"DODGED!"** prompt shows when he negates a big hit, which keeps an unfair-looking mechanic legible (same).
- **Typhon hides his HP bar.** "At the beginning of the fight, Typhon will hide his health bar. It is impossible to tell how much progress you have made in the fight." Progress shows on his body instead: a scar across the right eye, damaged horns, lightning scars, a cracked central eye (https://hades.fandom.com/wiki/Typhon/Combat). The VFX on the body *is* the phase display.
- **Typhon's eggs** are a horde mechanic: break them within **10 s** or each hatches an elite. The options are 12 weak eggs (Canines), 8 (Polyps), 5 (Lurkers) or 3 tough eggs (Eidolon/Horror) (same). Playtesting softened it: v1.0 notes "increased duration before Eggs hatch; reduced life and damage of some summoned foes" (https://store.steampowered.com/news/app/1145350/view/1811772772248733).
- **Repeated tuning toward fairness.**
  - "Chronos: various fixes and adjustments; there should be fewer cases where he's patently unfair" (Patch 2).
  - "Eris: grenade attacks no longer wildly bounce around" (Patch 2).
  - "Infernal Cerberus: various adjustments to better align how scary he is with how scary he looks" (Patch 3).
  - "Prometheus: ... now sometimes foresees and dodges attacks, yet overall should be somewhat less punishing than before" (Warsong).
  - "Headmistress Hecate: slightly reduced hitbox of flame attacks to better match the visuals" (Post-Launch Patch 1, https://store.steampowered.com/news/app/1145350/view/1815034432912036).

### 3.3 Inversions and "steals your tools" moments

- **Hecate casts the player's Hexes.** Total Eclipse, Lunar Ray and Twilight Curse are Selene's Hexes, which Melinoë herself uses. Twilight Curse sheep-transforms the player: slower, shorter dash, "without the invulnerability frames", but still able to attack (https://hades.fandom.com/wiki/Hecate/Combat). After certain story events it "can turn you into other types of critters" (Unseen Update notes, https://store.steampowered.com/news/app/1145350/view/1802354289729251).
- **Eris uses a weapon from the first game.** Her moveset is the Adamant Rail and its Aspect of Eris special, which she uses to buff herself +100%. Unrivaled Eris switches to the **Aspect of Lucifer**, with lasers and hellfire bombs (https://hades.fandom.com/wiki/Eris/Combat). Players who knew Zagreus's tools can read her.
- **Chronos's Time Immunity** disables the player's time-slow tools (The Sorceress Arcana, Phase Shift, Close Call) (https://hades.fandom.com/wiki/Chronos/Combat).
  - Early access went further: Chronos un-paused the game. Patch notes: "Ever-merciful Chronos no longer forcibly un-pauses the game during your fight, though will still let you know what he thinks in such situations" (Olympic Update, https://store.steampowered.com/news/app/1145350/view/6212244583172695508).
  - Phase Shift was later allowed to work on him "after a certain point" via the Temporal Fluctuation unlock (Patch 3, https://store.steampowered.com/news/app/1145350/view/5842939267306502875).
  - The game also added "voice lines when using Phase Shift (Selene) vs. Chronos (or trying to...)" (Patch 2).
- **Unrivaled Typhon's child-form phase.** With Vow of Rivals IV, a 5th phase begins after Typhon falls. "Chronos will revert Melinoe to her younger form. In this form, Melinoe cannot use her attacks, specials, casts, or hexes", and she must "stay in the moving circle and dodge attacks from Chronos and Typhon until she goes back to her normal form" (https://hades.fandom.com/wiki/Typhon/Combat). This is the purest "boss strips the build" beat in the strand. It is time-boxed and pure-dodge, and a short 6th phase of revenge damage follows on a "very weakened Typhon".
- **Polyphemus's sheep** can be turned against him. Golden, green and black sheep hurt him if he grabs them, and a white sheep heals him (https://hades.fandom.com/wiki/Polyphemus/Combat). The arena is a shared resource.
- **Cerberus (Unrivaled)** "can go into a guarding position where if Melinoe attacks Cerberus, the attack will be blocked and Cerberus shoots out fireballs as a counter". His third phase begins with "a barrier that can absorbs 23 hits", which favours fast-hitting weapons (https://hades.fandom.com/wiki/Cerberus/Combat). Hit-count shields are a lever that ignores raw damage, so a giant one-shot build cannot burst through them.

### 3.4 Fear, the Oath of the Unseen and the Vow of Rivals

The Oath of the Unseen has **16 Vows**; each adds **Fear** (https://hades.fandom.com/wiki/Oath_of_the_Unseen). The vows that matter most for bosses:

| Vow | Effect | Fear |
|---|---|---|
| Pain | Foes +20/60/100% damage | 1/2/2 |
| Grit | Foes +10/20/30% HP | 1/1/1 |
| Frenzy | Foes +20/40% faster (Patch 10: "reduced effect on Vow of Rivals moves", https://store.steampowered.com/news/app/1145350/view/1803527891710568) | 3/3 |
| Time | 9:00 / 7:00 / 5:00 per region; then 5 HP/s that "cannot be reduced in any way" | 1/2/3 |
| **Rivals** | "The Guardians of the first 1/2/3/4 Region(s) shall be stronger in various ways" | 2/3/3/4 (12 total) |

**Testaments** set a Fear target per Guardian per weapon (1, 2, 4, 8, 10, 12, 16, 20) and pay out 1–3 Nightmare (same page). Like Hades bounties, the reward ladder is **per weapon**, so players keep switching builds.

**Vow of Rivals (the "Unrivaled" remixes, added in The Unseen Update, 17 June 2025).** Each rank affects one region pair on both routes. You unlock the next rank by beating the current one ("prevail against both to reveal the next Rank"). "Most Guardian Encounters now have an all-new Location", and each gets its own title (https://store.steampowered.com/news/app/1145350/view/1802354289729251).

| Guardian | Unrivaled remix |
|---|---|
| Hecate → "The Witch of the Crossroads" | Triple Divide (clones) active almost permanently; armoured Sisters; Lunar Ray with 5 beams; Twilight Curse **splits into 3** (https://hades.fandom.com/wiki/Hecate/Combat). A patch fixed a bug that made "the real Hecate ... easier to distinguish from the other two" (Patch 11, https://store.steampowered.com/news/app/1145350/view/1806064758583505). |
| Polyphemus | **Medea** joins (undamageable) and applies poison. You must visit **Curing Pools** to cleanse. Polyphemus walking through poison makes his next attacks poison you. He throws 3 boulders instead of 1 (https://hades.fandom.com/wiki/Polyphemus/Combat). |
| Scylla → "Scylla and the Sirens Feat. Charybdis" | Charybdis adds 6 tentacles (2,800 HP shared pool) with tracking bombs that split. Scylla's HP rises from 6,550 to 7,750 (https://hades.fandom.com/wiki/Scylla/Combat/Rivals). |
| Eris → "Eris the Lightbringer" | Aspect of Lucifer lasers (3 beams, then 5 covering 180°); hellfire bombs; **smaller arena**; always-elite reinforcements drawn from later regions (https://hades.fandom.com/wiki/Eris/Combat). |
| Cerberus | Lava traps, magma armour, guard-counter stance, a 23-hit barrier in phase 3 (https://hades.fandom.com/wiki/Cerberus/Combat). |
| Prometheus | **Heracles** joins as a second damageable boss; Aetos the eagle takes over if Prometheus falls first (https://hades.fandom.com/wiki/Prometheus/Combat). |
| Chronos → "Chronos, Time Itself" | Elite armoured Satyrs that leave shockwaves on death; Time Burst ×3; Tempii heal +100. A new **third phase (26,000 HP) at "the end of time"** with past duplicates of himself and clock platforms that attack (https://hades.fandom.com/wiki/Chronos/Combat/Rivals). |
| Typhon | Chronos supports; the phase 3 Zeus rescue becomes Chronos time-bubbles; bigger eggs; child-form phase 5 and finishing phase 6 (https://hades.fandom.com/wiki/Typhon/Combat). |

The design pattern, consistent with Extreme Measures: **add a partner character** (Medea, Charybdis, Heracles, Chronos) and **change the location**. You avoid just inflating numbers, and the remix carries new story.

### 3.5 Scylla and the Sirens: music as a mechanic

- "Scylla, Jetty, and Roxy are on vocals, guitar, and drums respectively, and when you render one of them temporarily or permanently indisposed, their instrument disappears from the soundtrack." Before the June 2025 patch "there were two full band Scylla songs"; "Rock and a Hard Place" became the third (Nathan Grayson, Aftermath, 17 June 2025, https://aftermath.site/hades-2-update-scylla-sirens-new-song/).
- v1.0 added "new songs from Scylla and the Sirens, one for the Region and one for the show" and a "special presentation when Scylla introduces her latest sensational song" (https://store.steampowered.com/news/app/1145350/view/1811772772248733). Post-Launch Patch 2 added that "The audience watching Scylla and the Sirens has new responses after a certain point" (https://store.steampowered.com/news/app/1145350/view/1829528821318255).
- The "Featured Artist" mechanic ties the phase-2 empowered member to the music, so the arrangement tells you who is dangerous.
- Player reception (Steam "(SPOILER WARNING) Boss Ranking", 10 May 2024, https://steamcommunity.com/app/1145350/discussions/0/4358998952356614955): Scylla is the community favourite, "an amazing boss fight". Another player: "their music changes as you defeat each of them... masterful."
- Korb's general approach: "we have drums that turn on when there's enemies present, they turn off when you kill the last enemy". Pieces escalate from "a very chill section" to "a hard rock version" for bosses (RPG Site interview with Greg Kasavin and Darren Korb, https://www.rpgsite.net/interview/20348-supergiant-games-interview-with-greg-kasavin-and-darren-korb-hades-ii-early-access-feedback-boss-themes-the-ending-coffee-and-the-future).

### 3.6 Dialogue, presentation and victory

- Supergiant patches list presentation work per boss: "Updated Hecate pre-fight animation and presentation when vanquishing her", the same for Scylla and Eris, and "Updated presentation when vanquishing Chronos" (Unseen Update, https://store.steampowered.com/news/app/1145350/view/1802354289729251). Warsong added "animations for info banners, such as when entering Locations or vanquishing Guardians" (https://store.steampowered.com/news/app/1145350/view/1792116353167292). Post-Launch Patch 2 added a "Reward preview icon when entering Locations just before a Region's Guardian", which shows the prize before the fight (https://store.steampowered.com/news/app/1145350/view/1829528821318255).
- Chatter is tuned for frequency: "Adjusted how often Headmistress Hecate and Chronos speak during battle" (Patch 6), and "Fixed a particular pre-fight greeting line from Headmistress Hecate playing too frequently" (v1.0 Hotfix 3, https://store.steampowered.com/news/app/1145350/view/1816215235360707). Bosses react to the player's loadout: "Fixed Headmistress Hecate commenting on the Aspect of Selene when you did not have it equipped" (Hotfix 2, https://store.steampowered.com/news/app/1145350/view/1830797770233956).
- Typhon's phase 3 is a **story beat inside the fight**. Zeus arrives and stuns Typhon for **15 s**, and his head and tongue fall onto the arena as a damage window (https://hades.fandom.com/wiki/Typhon/Combat).
- Rewards are a fixed, repeatable crafting material per Guardian (e.g. Cerberus 1 Tears, Eris 1 Golden Apple, Chronos 1 Zodiac Sand, Typhon 1 Void Lens), plus Nightmare for Testaments (Guardian combat pages above; https://hades.fandom.com/wiki/Oath_of_the_Unseen).
- **Player opinion** (same Steam ranking thread):
  - Chronos: "his attack patterns are predictable enough that you're not completely floundering, but they're similar enough that you are always kept on your toes."
  - Eris divides players: one calls the fight "fast, energetic and fun".
  - Polyphemus is the least liked. His "jumps are awkward since they can hit you while in midair", and "he definitely creates a need to have a ranged build". A boss that invalidates a build archetype is resented.
  - Hecate works as a teaching first boss but grows repetitive post-game.
  - Search summaries of other threads call Eris "way harder than anything else in the game, Chronos included", citing subtle tells and stacking +100% buffs (secondary, https://steamcommunity.com/app/1145350/discussions/0/4358998952353825471/?ctp=2).

---

## Sources (primary, in addition to inline)

- Risk of Rain 2 wiki (wiki.gg) via MediaWiki API: Mithrix, Teleporter, Difficulty, Directors, Shrine of the Mountain, Armor, Eclipse, Voidling, False Son (Boss): https://riskofrain2.wiki.gg/wiki/Mithrix etc.
- RoR2 dev diary 8 (False Son rework): https://devtrackers.gg/risk-of-rain/p/e20a61e8-dev-diary-8-seekers-of-the-storm-roadmap-phase-2-false-son-boss-fight
- Hades wiki (fandom) via API: Furies, Bone Hydra, Theseus/Combat, Theseus/Quotes, Asterius/Combat, Hades/Combat, Charon/Combat, Pact of Punishment; Hades II: Hecate/Combat, Scylla/Combat, Scylla/Combat/Rivals, Cerberus/Combat, Chronos/Combat, Chronos/Combat/Rivals, Polyphemus/Combat, Eris/Combat, Prometheus/Combat, Typhon/Combat, Oath of the Unseen.
- Hades Steam patch notes (app 1145360) and Hades II Steam patch notes (app 1145350), fetched through the Steam news API; URLs inline.

## Verification

Adversarial check, 3 October 2026. Each cited source was re-opened: wiki pages as raw wikitext through the MediaWiki API, Steam threads as HTML, and Hades II patch notes through the Steam news API. Result: 11 of the 12 load-bearing claims are confirmed and 1 is partly right. The extra checks found 3 problems elsewhere in the notes.

| # | Claim | Verdict | Notes / correction |
|---|---|---|---|
| 1 | Teleporter: ~120 m red dome, minimum 90 s charge, spawns stop at 99%, red boss bar, 15% yellow-item chance | Confirmed | All five points are stated verbatim on https://riskofrain2.wiki.gg/wiki/Teleporter |
| 2 | Boss Director budget `600 × sqrt(coeff) × (1 + shrineMountainStacks)`, bypasses the 40-monster cap, HP multiplier × living players | Confirmed | https://riskofrain2.wiki.gg/wiki/Directors (credits table; "The Teleporter Boss bypasses this restriction"; "its HP multiplier is multiplied by the number of *living* players") |
| 3 | Adaptive armour 3000 × dmg/maxHP, cap 400, decays 40/s; Mithrix, Voidling, False Son, Solus | Confirmed | https://riskofrain2.wiki.gg/wiki/Armor names Solus Wing and Solus Heart and adds that Solus Wing's weak points get half-effective adaptive armour |
| 4 | Mithrix P4 theft timings, 38 items, "fun phase" note, Anniversary 50%/50% returns | Confirmed | https://riskofrain2.wiki.gg/wiki/Mithrix. The quote is from the PC Patch v1.0.1.1 developer notes. The wiki also notes that step 1 actually runs every ~0.217 s because of frame rounding. See E1 for an outdated detail in the same section. |
| 5 | False Son Dev Diary 8 goals | Confirmed | All four quotes are verbatim on https://devtrackers.gg/risk-of-rain/p/e20a61e8-dev-diary-8-seekers-of-the-storm-roadmap-phase-2-false-son-boss-fight. The post is by "Antler Shield" (post-Hopoo, Gearbox era), so attribute it to "the RoR2 team", not Hopoo. |
| 6 | "Voidling has committed the cardinal sin of being boring…" | Confirmed | Posted by user azumazku in https://steamcommunity.com/app/632360/discussions/0/3189116454990708305. The original is lower-case ("voidling has…"). The thread date (4 Mar 2022) and the other quoted posts also check out. The "repetitive, slow fight" quote leaves out "(imo)". |
| 7 | Extreme Measures 1/2/3/4 Heat (10 in total), one boss per rank; Tight Deadline 9/7/5 min, then 5 unreducible damage/s | Confirmed | https://hades.fandom.com/wiki/Pact_of_Punishment. Nuance: since v1.0 the timer *adds* 9/7/5 min on entering each new region (unused time carries over). Before v1.0 it reset. |
| 8 | EM4 Hades 22,000/22,000/17,600, Cerberus stampede, 1,500-HP vase pulses, darkness phase 3 | Confirmed (attribution caveat) | Everything is on https://hades.fandom.com/wiki/Hades/Combat. However, the wiki's Reddit reference (30 Jan 2020) predates EM4 (v1.0, Sept 2020) and supports only the 17,000 standard figure. The EM4 HP numbers are uncited on the wiki, so the parenthetical in §2.1 overstates their sourcing. "Stampede" is our wording: the wiki says Cerberus "runs down the middle of the arena" and causes a quake of falling rocks. |
| 9 | Theseus calls only an Olympian who has not given a boon this run; his attacks then apply that god's curse; EM3 chariot with miniguns, 12,000 HP | Partly right | https://hades.fandom.com/wiki/Theseus/Combat confirms the boon rule (never Hermes; Artemis if all gods have given boons), the chariot, the two miniguns and 12,000 HP. But only some gods give a curse (Aphrodite Weak, Ares Doom, Demeter Chill, Dionysus Hangover, Zeus Jolted). Artemis gives "major damage", Athena brief imperviousness after attacking, and Poseidon knockback. Also, under EM3 the Olympian call happens at 33%, when the chariot breaks, not at 50%. |
| 10 | Scylla/Jetty/Roxy = vocals/guitar/drums; a knocked-out member's instrument drops out | Confirmed | Verbatim in Nathan Grayson, Aftermath, 17 Jun 2025, https://aftermath.site/hades-2-update-scylla-sirens-new-song/. The wiki also has Jetty playing guitar (https://hades.fandom.com/wiki/Scylla/Combat). |
| 11 | Unrivaled Typhon phase 5 child form, no attacks/specials/casts/hexes, moving circle; hidden HP bar; 65,000 HP over 4 phases | Confirmed | https://hades.fandom.com/wiki/Typhon/Combat. The wiki also lists a 10,000 HP "Rivals Phase" on top of the 65,000. |
| 12 | Patch 2: Chronos "patently unfair", Eris grenades "no longer wildly bounce around" | Confirmed | Both lines are verbatim in Early Access Patch 2 Notes, 4 Jun 2024, https://store.steampowered.com/news/app/1145350/view/5742731639349105637 |

**Extra checks (other claims in these notes):**

- **E1 Outdated.** §1.2 says Crowbar is on Mithrix's blacklist "after a patch". v1.0.1.1 did blacklist Mired Urn and Crowbar. The Anniversary Update reversed the Crowbar part: "Now utilizes Crowbars" (https://riskofrain2.wiki.gg/wiki/Mithrix, Version History). Only Mired Urn, Tougher Times and Razorwire (among the named items) stay unused.
- **E2 Unsupported.** §3.2 says Supergiant "twice fixed" Chronos's Time Burst hitting players in the safe point. The Hades II Steam news feed has only one such fix (Patch 2). Patch 3 fixed the opposite problem: the attack being "easier to evade than intended, introduced in Patch 2" (https://store.steampowered.com/news/app/1145350/view/5842939267306502875). Change "twice" to "once".
- **E3 Partly right.** The §2.1 table attributes the Hades HP figure to a Reddit post cited by the wiki. That holds only for the 17,000 standard value (see #8).
- **E4 Confirmed.** Voidling rears up for 3.43 s with a "thunderous sound"; the black hole is "instantly fatal"; phase 3 has a 150 m bubble (https://riskofrain2.wiki.gg/wiki/Voidling).
- **E5 Confirmed.** False Son: 7 Lunar Rain spots, 3.5 s landing, 21 s then a 2 s warning; Disable All Skills for 420 s; with a Halcyon Seed the reward becomes 60% Boss / 40% Legendary (https://riskofrain2.wiki.gg/wiki/False_Son_(Boss)).
- **E6 Confirmed.** Cerberus 21,500/31,500 HP and the 23-hit barrier (https://hades.fandom.com/wiki/Cerberus/Combat). Chronos 20,000/16,000 HP and the 999 Time Burst (https://hades.fandom.com/wiki/Chronos/Combat). The infobox gives a 699–999 range for the Time Burst, but the body text says 999.
- **E7 Confirmed.** The Oath of the Unseen vow table (Pain 1/2/2, Grit 1/1/1, Frenzy 3/3, Time 1/2/3, Rivals 2/3/3/4 = 12; 16 vows) matches https://hades.fandom.com/wiki/Oath_of_the_Unseen.
