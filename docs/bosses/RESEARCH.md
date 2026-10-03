# Research: boss fights, game by game

How other games build their bosses, and why players love or hate them, for
Survivor Unchained's night arenas (most of it) and its day story (less).
Each section is a teardown with the sources that matter; the full research
notes behind it (about 120,000 words, every claim with its URL, each strand
fact-checked) are in `notes/`. "(secondary)" marks a claim seen only in a
search summary. Where a number could not be found, it says so.

Read `MECHANICS.md` for the same material organised by mechanic rather than
by game.

## 0. The ten findings that matter most

1. **The genre's commonest complaint is the HP sponge**: a boss that is a
   bigger enemy with two to four moves and a long health bar (§6). The
   commonest praise is for a boss that briefly turns the game into a
   learnable dodging dance, then pays out big (§6).
2. **A strong build must not skip the fight, and a weak one must not be
   stuck in it.** The tools that work: phases on *health or time,
   whichever first* (Brotato, §3.1); phases on *time and level* (Vampire
   Survivors' Directer, §2.4); a damage bank released at once (the Ender,
   §2.3); caps expressed as a minimum length (Gungeon, Isaac, §5.3, §5.5);
   breakable shields at thresholds (Diablo IV, §4.1). The tools that fail:
   a hard death timer (Halls of Torment's 40-second curse, §1.2); a hidden
   cap (Gungeon raised its own, §5.3); healing a build cannot outpace
   (Rogue: Genesia, §6).
3. **Clear the stage for the boss.** HoloCure wipes the field and sends a
   themed escort; Bounty of One's hunters retreat; 20 Minutes Till Dawn's
   developer announced the same for its beta; Vampire Survivors fades to
   black before the Ender (§2–§3).
4. **Draw the boss's telegraphs above the player's own effects.** The
   second commonest complaint is not seeing the attack; every game that
   shipped a fix (Halls of Torment, Soulstone, Picayune Dreams) ended up
   layering or dimming the player's effects (§1.4, §3.4, §6).
5. **Adds must never soak the player's auto-aim.** Halls of Torment's
   angriest feedback came from adds that absorbed shots, and Army of Ruin's
   developers blamed its deadliest fight on an attack that did the same
   (§1.2, §3.11).
6. **Use the horde.** Bosses that feed on it (Sketamari), are hurt by it
   (Nova Drift's Dweller loses health when a minion dies), are armoured by
   it (Ravenswatch) or are counted down by it (Halls of Torment's Marching
   Ghosts) belong to this genre in a way a duel does not (§2, §3.7, §3.9,
   §1.2).
7. **Taking the player's tools works only if it is proportional, visible,
   time-limited and returned.** Mithrix's item theft was hated until it
   became deterministic; Megabonk returns a weapon a phase; Hades II's
   inversions are short (§5.1–5.2, §3.8).
8. **Every weapon family must be able to win.** Polyphemus is resented for
   punishing melee; a Vampire Hunters statue the flamethrower could not
   reach made players feel cheated by the draft (§5.2, §6).
9. **The kill is the reward moment.** Vampire Survivors' chest is the
   genre's best-loved ritual: it pauses the game, spins reels, never gives
   a bad item, and scripts an early jackpot (§2.5). A physical pickup that
   ends the run (Halls of Torment's crystal) beats a banner (§1.3).
10. **Endless needs new mechanics, not more health.** Opt-in boss density
    for more loot (Risk of Rain 2's Shrine of the Mountain, Vampire
    Hunters' constellations) is the best-liked answer (§5.1, §6).

## 1. Halls of Torment (Chasing Carrots, 2023–)

The owner's reference, and the survivors-like players most often praise
for its bosses. Sources: the game's Steam news (every item 2023–2026), the
community wiki (through its MediaWiki API) and about fifty Steam threads;
full detail in `notes/A1_halls_of_torment.md`.

### 1.1 Structure: three tiers, and gates in the middle

- **A three-tier threat ladder, coloured by outline**: elites blue, bosses
  red (set in the 17 Feb 2023 playtest), Agony champions yellow. Each tier
  pays differently: elites a draft of abilities, bosses a chest of three
  equipment pieces (pick one, then 0.5 s of invulnerability), Lords a
  meta-currency crystal and the next difficulty mode
  ([wiki: Pickup](https://halls-of-torment.fandom.com/wiki/Pickup); Dev
  Journal #3, Steam news).
- **Bosses at a fixed eight-minute cadence with an elite between.** Hall I:
  elite 2:20, Imp Chieftain 6:00, elite 10:15, Skeleton Lord 14:00, elite
  18:20, Lich 22:00, the Lord of Pain at 30:00
  ([wiki: Haunted Caverns](https://halls-of-torment.fandom.com/wiki/Haunted_Caverns)).
- **The next hall unlocks from a mid-run boss, never the Lord** (Imp
  Chieftain, Wraith Warlord, Frost Knight, Twisted Construct). The
  developers: "we need to make sure that players who follow a natural
  progression ... don't hit a brick wall" (7 Sep 2023, Steam news). The
  Lord is the mastery test; the mid-run bosses are the progression.
- **The horde mostly stops for the Lord.** The artifact "Torn Stage
  Curtain" reads "Enemies will keep spawning after the Lord appears",
  implying they normally do not (inference from the wiki's artifact data).

### 1.2 The Lords

| Hall | Lord | What it does | What players said |
|---|---|---|---|
| Haunted Caverns | Lord of Pain | Two bars, mounted then on foot; fireballs, a spiral, a triple dash. At launch a homing curse that killed in 40 s | Most loved and most hated: "the only Lord that feels like a Lord"; "a 40-second dps check" |
| Ember Grounds | Lord of Regret | Brain-like mines that explode after contact, a line of fire circles, spinning blades, "a MASSIVE health bar" | Most hated: "ten million friggin' HP"; the mines soaked projectiles and auto-aim |
| Forgotten Viaduct | Lord of Despair | Summons unkillable Marching Ghosts; illusions; invulnerability phases | Liked for theme: "What a fantastic boss" |
| Frozen Depths | Lord of Hate | Scatter shots, pulsing rings with safe gaps, a six-way line, a spin rush, a pounce (secondary) | Divisive: "BS hitboxes" |
| Chambers of Dissonance | Lord of Discord | 400,000 base health by one player's account (unverified) | — |
| The Vault | Lord of Greed | Sealed on a throne by four pylons (50,000 each); summoned by the player; the run lasts as long as he lives | — |
| Boglands (DLC) | Lord of Blight | Rises after 20,000 kills (25,000 at launch); mounted first | — |

Sources per row in `notes/A1_halls_of_torment.md` §2.

- **The death timer and its removal.** The Lord of Pain's curse killed
  the player after 40 s; a developer explained on the forum that it had been
  meant as 6 s with a counter that did not make the launch, and that "having only
  one valid way of finishing something is not it ... we swapped the
  mechanic to the boss getting gradually faster over time". Beta notes of
  6 Jun 2023, live on 9 Jun: "Death timer has been removed. The Lord of
  Pain will now get stronger over time." By 31 Aug 2023 every Lord had "lower health but
  they increase in difficulty over time" (Steam news). The single clearest
  lesson in the strand: escalation, not execution.
- **The Lord of Regret's orbs.** "All of the bubbles soak up all of your
  damage. I just spent literally 20 minutes chipping away at him" (Steam).
  The fix (17 Jul 2023): "The additional projectiles and indestructible
  guards will no longer be valid targets for abilities and auto-aim."
- **The Marching Ghosts** of the Viaduct: two detachments of 56 that march
  from opposite corners and meet in the middle "right before the timer
  elapses completely" (10,000 health, damage factor 0.1%): a diegetic
  countdown to the Lord
  ([wiki](https://halls-of-torment.fandom.com/wiki/Marching_Ghost)).

### 1.3 Lord Hexes, and the victory

- **A hex in every hall.** Each arena hides an optional secret that weakens
  its Lord: the Lord of Pain's pendant fires a shot for 50% of his health;
  a hidden Cyclops's eye makes the Lord of Regret's bombs harmless; a
  raven leads to a sarcophagus whose orb removes the Lord of Despair's
  invulnerability; a Frost Ghoul Lieutenant's heart simplifies the Lord of
  Hate's patterns and makes him vulnerable after his spin (shown by the
  icon pulsing); a light puzzle charges a monolith that shoots the Lord of
  Discord for 7,000 a hit ([wiki pages per hall](https://halls-of-torment.fandom.com/wiki/Haunted_Caverns)).
  Players say the first "makes him very easy, almost trivial", which is the
  point: a route to victory through knowledge rather than grinding.
- **Victory is a pickup.** The Lord drops a crystal; picking it up ends the
  run. At 1.0 the well "teleport[s] close to the player after defeating the
  lord" so the victory lap is not a walk through a live horde (Steam news,
  24 Sep 2024). In the endless Vault the run goes on until the player
  chooses to collect.

### 1.4 Readability

The Frozen Depths launch drew complaints, and the fix list (5 Sep 2023) is
the best checklist in the strand for a horde boss: "reduced trigger
distance for ranged attacks to avoid player getting off-screened; made
projectile based attack patterns of bosses less frustrating; slower
movement; less dense patterns; smaller damage areas; increased size of hit
areas". Also: an opacity slider for the player's own effects; the player's
Frost Avalanche moved *below* enemy projectiles; sound cues for lance
attacks; "Lords have new and improved sounds" (Steam news 2023–24).
Players still report that "Visual clutter makes it hard to see ... lord's
attacks". A reviewer found bosses "often oversized versions of smaller
enemies", which made the exceptions (the mounted Horseman, the Hydra) stand
out ([The Xbox Hub](https://www.thexboxhub.com/halls-of-torment-review/)).

### 1.5 Scaling and what players said

- **No damage caps.** "We don't try to kill off OP builds, it's a single
  player experience anyways" (27 May 2023). Bosses resist slows rather than
  ignoring them (boss 66%, Lord 80%, floor 50%); elemental stacks cap at 20.
- **Difficulty for strong players is opt-in**: Agony (a clock adding a rank
  every 4 min 48 s, +1 defence a rank), Torment artifacts (three Lords at
  once; "Elites, Bosses, and Lords gain additional abilities"), kill-mode
  Lords. Per-rank health was cut from × 1.2 to × 1.12 (later × 1.09)
  because enemies hit the engine's health ceiling.
- **The power spread is about 300 to 1**: "I can now melt world 1 lord in
  6~10 secs" against "Had a 50 minutes fight with the world 2 boss" (Steam).
- **The 30-minute tax**: "Then where you tired at 30min and wanna be
  rewarded you need to face a bullet sponge boss". **Single-target against
  horde-clear builds**: "i dont want to have to build ... specifically to
  kill a boss". **The counter-view**: "Losing isn't fun, and it's not meant
  to be fun. It's meant to trigger an impulse for you to improve" (all
  Steam, `notes/A1_halls_of_torment.md` §5).

## 2. Vampire Survivors and its DLC (poncle, 2021–)

Full detail in `notes/A2_vampire_survivors.md`.

### 2.1 Ordinary bosses: loot on a clock

Most bosses are big, effect-resistant enemies that drop a chest; their
health is base × the player's level at spawn ("HP x Level"). They pace the
run: evolutions come from boss chests, usually from 10:00 on, and Arcanas from
the 11:00 and 21:00 bosses ([wiki: Treasure Chest](https://vampire.survivors.wiki/w/Treasure_Chest),
[Arcana](https://vampire.survivors.wiki/w/Arcana)). Reviewers: bosses
"have far more health, but otherwise behave the same" (KeenGamer). A
minority have gimmicks: the Giant Enemy Crab's regrowing pincers;
Orochimario's eight heads; **Sketamari**, which rolls through the horde
absorbing enemies (and Reapers) and grows, its rolling louder as you near
it; the **Cosmic Egg**, which casts the player's own Infinite Corridor and
halves their health ([wiki pages](https://vampire.survivors.wiki/w/Sketamari)).

### 2.2 The Reaper: a curtain, not a fight

At the time limit the screen clears, and the Reaper comes: 655,350 × level
health, 65,535 damage a hit, another every minute
([wiki](https://vampire.survivors.wiki/w/The_Reaper)). Surviving to it *is*
the win ("it still says 'stage complete'"). Killing it became a community
legend, and when poncle made it killable they added the White Hand, an
unstoppable non-entity that ends the run after twelve bell strokes
([wiki](https://vampire.survivors.wiki/w/White_Hand)). Its reward is to
become it (Mask of the Red Death). Newcomers are baffled ("I just got 1
tapped instantly"); veterans love it ("the final fuck you when Death himself
shows up", NME).

### 2.3 The Ender: the first boss that fights back

With the Yellow Sign, 30:00 in Cappella Magna clears the field, fades to
black, counts down 30 s, and shows the five Reaper-types merging (the stage
paraded them at 0:10, 5:10, 10:10 and 15:10). The Ender has a **90-second
shield that banks all damage** and releases it at once; its attacks speed
up as it loses health through eight patterns built from the game's own
weapons and enemies ([wiki](https://vampire.survivors.wiki/w/The_Ender)).

### 2.4 The Directer: gates on time and level

The base game's final boss cannot be damaged directly. Five phases each
open on a timer **and** a player level (7, 14, 19, 22); its masks become
breakable after 60 s and level 14; its phases summon swarms themed on the
earlier stages shown behind it; it strips revivals; its last phase is a
shower of gold ([wiki](https://vampire.survivors.wiki/w/The_Directer)).
"A reliable short-term gold farm as the battle only takes 4 to 5 minutes."

### 2.5 The chest

The best-loved moment in the genre. It pauses the game, plays a "Treasure
Found" jingle then a jingle per tier (1, 3 or 5 items), spins reels, fires
fireworks; "Treasure Chests are supposed to be a purely positive thing"
(Galante, patch 0.2.7), so it never gives an unwanted item; the first six
chests are scripted 1-1-3-1-1-5; it is not magnetised, so the player walks
to it; the 5-item animation is unskippable until the player has seen 50 of
them or 500 chests ([wiki](https://vampire.survivors.wiki/w/Treasure_Chest)).
Galante came from slot machines ([Wikipedia](https://en.wikipedia.org/wiki/Vampire_Survivors)).

### 2.6 Scaling, endless and readability

Curse, Hyper, Inverse (+200% enemy health, +5% a minute) and Endless (+100%
health, +50% spawns, +25% damage a cycle, the whole boss schedule re-run).
Only two things still threaten an absurd build: percentage damage (the
Cosmic Egg) and scripted kills (the White Hand). Readability comes from
size, minute marks, a cleared screen for set pieces, markers that land
after about 2 s, mood shifts (red sky, detuned music, a lens warp, bells),
and removing the player's weapons for parts of the Death and Je-Ne-Viv
fights, which also removes their effects from the screen.

## 3. The other survivors-likes

### 3.1 Brotato (Blobfish)

Bosses only on wave 20 (a 90-second wave); one of Predator or Invoker,
both at Danger 5 with 75% health; boss health 15,000 + 750 a wave. **Each
mutation triggers at a health mark or a time, whichever first** (Predator:
50% or 45 s; Invoker: 60% or 30 s, then 40% or 60 s). **The wave ending
counts as a win**: kill the bosses or outlast 90 s
([wiki: Predator](https://brotato.wiki.spellsandguns.com/Predator),
[Invoker](https://brotato.wiki.spellsandguns.com/Invoker)). Two items'
percentage effects (Giant Belt's critical, Greek Fire's burn) are cut
tenfold against bosses and elites. A patch fixed delayed attacks that
"could deal damage during the initial frame that they were spawned": a
telegraph must be harmless until it completes. Elite waves 11–12 are "run
killers" in players' words. `notes/B1_brotato_20mtd_holocure.md` §1.

### 3.2 20 Minutes Till Dawn (flanne)

No final boss: dawn at 20:00 ends the run. Bosses at 5:00 and 15:00, elites
at 3:00, 11:20 and 16:00. **An electric barrier traps the player with the
boss for 60 s** on open maps, then dissolves. Shub-Niggurath's dash locks
its direction when the wind-up starts; Shoggoth's lasers are drawn as red
lines first; Hastur's Sploders can be shot to damage him; a secret boss is
summoned by killing Mysterious Trees, one at the end for each tree killed
([wiki: Boss](https://20-minutes-till-dawn.fandom.com/wiki/Boss)). Its
Darkness levels raise boss health, then damage, and last of all attack
frequency (D15: "Bosses attack 80% more often"). The developer announced for the beta branch (Oct 2024): "Normal enemies
will not spawn during boss fights anymore to prevent too much clutter"
(whether it reached the live game is unconfirmed). `notes/B1` §2.

### 3.3 HoloCure (Kay Yu)

A mini-boss every two minutes, bosses at 10:00 and 20:00; the 20:00 boss
must be killed (no time-out). On arrival "all previous enemies will
disappear" and a themed escort comes. One shared telegraph vocabulary for
everything (red circle, "!!" with a sound, a red line, a shadow, a cone, a
darkened screen for the big attack, a flaming aura for enrage). Hard stages
bring the previous finale back as the 10:00 event. Multi-boss finales (the
Area 15 trio; five bosses in Halloween Myth, one a healer). **Each boss
unlocks a weapon modelled on its attack** (Fubuzilla gives Fan Beam). The
win is a hard cut to "stage cleared"
([wiki: Area 15](https://holocure.wiki.gg/wiki/Area_15_(Bosses))). A new
player missed the 20:00 boss for twenty minutes: the boss must be
impossible to miss. `notes/B1` §3.

### 3.4 Soulstone Survivors (Game Smithing)

Lords of the Void spawn on kill quotas; Overlord mode is a boss rush.
Soulstone's longest-running complaint is boss telegraphs buried under the
player's own effects; the developer added a visibility slider, exempted
boss attacks from it, and players still called it a band-aid. Its Lords
now "appear encased in statues, and only when infused start to fight,
giving you a few seconds to prepare", and their health is "no longer
related to the time of a match" (A New Beginning, Mar 2024). Endless
bosses whose "attack speed almost becomes instant" were capped at +70%.
Permanent zones litter arenas. `notes/B2_soulstone_drg_dmd.md` §1.

### 3.5 Deep Rock Galactic: Survivor (Funday)

The Dreadnought (16,500 base health): a leap with a long pause first
("When he stops do a 90 degree turn and he will miss"), a stomp that
raises rock spikes the player must dig out of, a spat cocoon that hatches
Glyphids. The Twins heal each other (a transfer, 10% out and 20% in).
**The player can pop the boss's cocoon early.** The threat level rises
every 60 s of a boss fight; **the loot crate is graded by time to kill**
("the optimal play was often to ignore the end-of-stage elite to farm ...
which felt backwards"). Players loved baiting the Dreadnought under a
falling supply pod (half its health; later capped at 20–33% by hazard).
Players asked for a ground circle under the jump. `notes/B2` §2.

### 3.6 Death Must Die (Realm Archive)

Three bosses an act on a fixed clock. **Timed spawns stop while a boss
lives, and a barrier traps the player, dissolving after a set time even if
the boss lives** ([wiki: Waves](https://dmd.fandom.com/wiki/Waves)). The
Lady is "the epitome of a great boss ... you can dance with her"; the Frog
King cannot be dashed through, which broke dash builds, and its slam must
be read from the sprite before the circle appears; the Lady's charm on
summons was hotfixed from 20% to 7%. `notes/B2` §3.

### 3.7 Ravenswatch (Passtech)

Not strictly a survivors-like, but the closest analogue to our day and
night. **Night changes behaviour, not numbers**: hogs stop exploding,
ghosts become visible, gnolls sleep, the Tentacle Nightmare becomes a
mobile laser; heroes change too (Scarlet becomes a werewolf). **Every
chapter boss flips the arena to night at half health**; enraged, it attacks
faster with the same patterns, shown by the bar glowing red (the wiki does
not say what triggers the enrage). Bosses carry a basic armour (50% less
damage); the Faceless doubles it (75% less) while its eyes live, and is
stunned when they die; the Claws has no adds but two hands, each immune
once staggered until the other is staggered too. Clearing the chapter's
Nightmare Tumour takes 30% off the boss's health. An overtime penalty (up
to +100% boss health and damage over three minutes) and an early-summon
reward (the Hourglass). A night form that removed a hero's damage (the
Snow Queen) was reworked: night should be a gift with a cost, never a tax.
`notes/C1_more_survivors.md`, Ravenswatch.

### 3.8 Megabonk (vedinad)

Find the boss portal within ten minutes or face the Final Swarm. The final
boss strips the player's weapons and **returns one each phase**. Endless
runs reached five hours at 1.5 frames a second; one patch added ghosts to
the Final Swarm, and a later one (December 2025) made them speed up after
20 minutes and capped crowd-control immunity. Boss Curse shrines add
bosses for chests. `notes/C1`, Megabonk.

### 3.9 Nova Drift (Chimeric)

Boss waves every 20; a final boss at 120, added so builds would be judged
by "can it beat the boss" rather than wave height. **The Dweller loses
health whenever one of its minions dies.** Star Eater takes *more* damage
from 35 s into the fight, carrying weak builds to the end: a floor, not a
cap. `notes/C1`, Nova Drift.

### 3.10 Spirit Hunters: Infinite Horde (Ant Workshop)

A boss at 15:00 inside a spike cage that shrank and one-shot at launch;
it became a fixed cage of "Boss Hurty Spikes" with the boss's health raised
to match. The bugs that drew complaints were knockback into the spikes.
Off-screen arrows point to bosses. `notes/C1`, Spirit Hunters.

### 3.11 Army of Ruin (Milkstone)

Its telemetry showed deaths on the first Forge stage peaking at minute 15,
in the boss wave; the developers' "guess" was that the boss's saw blocked
shots and dragged the fight out while the minion ramp peaked. The fix was
lower boss health and a slower ramp. Late, on long stages, a
bigger horde helped evolved builds: "adding new enemies may even work in
favor of the player". `notes/C1`, Army of Ruin.

### 3.12 Magicraft (Wave Games)

Bosses with 25-second invulnerability shields that drop on their own (or
early to a rune); a hidden room for a hitless kill; a death animation added
at 1.0. `notes/C1`, Magicraft.

## 4. ARPG bosses from a high camera

The lesser half of the brief. Full notes: `notes/E1_diablo.md`,
`notes/E2_poe_le.md`, `notes/E3_other_arpgs.md`.

### 4.1 Diablo II, III and IV

- **Diablo II** is mostly stat checks with one signature move each. The
  Lightning Hose works because Diablo "turns slowly while casting the spell"
  (circle him, do not flee); Duriel is remembered as cheap because his tiny
  tomb and an always-on slow take away the one verb the camera gives you;
  Baal's Vile Effigy, a clone identical to him, shows why look-alikes fail
  when sprites are small
  ([Diablo Wiki](https://diablo.fandom.com/wiki/Diablo_(Diablo_II)); `notes/E1` §1).
- **Diablo III** built the top-down vocabulary still in use. Belial: three
  phases, then a giant form whose Fist Slam is a green ring ("slightly
  larger than its visual", a known bug) and whose Eruption scatters rings
  that explode after 2 s. Azmodan announces his two biggest moves with a
  shout ("Enough! The dark power of Hell will consume you!") and his pools
  halve the safe radius; his Globe explodes early on the central pillar.
  Diablo's Realm of Terror is the same geometry in a new palette with fog,
  and clones of the player's own class. Malthael leaves one safe sector
  behind him. **Torment enrages at 3:00 turn a known hazard all the way
  up** (all the Butcher's grates, Belial's meteors, Azmodan's pools).
  **Greater Rifts**: progress, not time, summons the guardian; it arrives
  with a sound, a voice and the sky darkening; "all other monsters within
  100 yards die and despawn"; all loot is moved onto it
  ([Diablo Wiki: Rift Guardian](https://diablo.fandom.com/wiki/Rift_Guardian)).
- **Diablo IV's Uber Lilith** is the series' cautionary tale: one-shots,
  patterns that cannot be learnt, no damage windows ("when is my turn to
  attack again?"; "an Action-RPG without the action"), hitboxes larger than
  the visuals, a platform that breaks three times. Season 4 replaced the
  one-shots with "heavily ramping damage" and matched the hitbox to the
  visual. A 2025 patch fixed her getting "stuck in the first phase if her
  health decreased too quickly"
  ([Maxroll](https://maxroll.gg/d4/bosses/echo-of-lilith); `notes/E1` §3.1).
- **Diablo IV's lair bosses**: Varshan channels to absorb one of three adds,
  and gains a buff unless it is killed first; Grigoire lights seven of nine
  floor tiles; Zir's Wing Blast tracks, then locks; Andariel adds a
  permanent hazard at each intermission. Health buffs (+50–150%) never
  fixed a spread "ranging from 500k to trillions"; "the issue with bosses
  wasn't that they died too quickly, [it] was that they're a gear check and
  then they're of no consequence" (Macrobioboi). **Season 10 replaced
  immunity phases with shields** at two thirds and one third, worth a third
  and two thirds of maximum health, lasting 5 s: break them and the boss
  never goes invulnerable. **Stagger**: a bar filled by every kind of crowd
  control; when full the boss is held, then resists for a while (`notes/E1`
  §3.6–3.7).

### 4.2 Path of Exile 1 and 2, Last Epoch

- **Voiced killing blows**: Sirus shouts "DIE!" before his beam; the Maven's
  memory game starts with "SCURRY, SCURRY!" and her tri-beam with "STAND
  STILL!" ([Maxroll: Maven](https://maxroll.gg/poe/bosses/the-maven-boss-guide)).
- **Safety as a shape**: Zana's bubble against the Shaper's bullet hell; the
  Uber Elder's inner ring; Sirus's maze exits marked by flares; the Arbiter
  of Ash's seed that is safe *inside*.
- **One colour for "you cannot tank this"**: Path of Exile 2's red flash for
  unblockable attacks, kept consistent across patches.
- **Gates**: Sirus's throne intermissions at 75/50/25%; the Uber Elder's two
  bosses swapping invulnerability every 25%; Last Epoch 1.1's ward at health
  breakpoints that decays; Path of Exile 2's emergence damage reduction that
  fades over time (`notes/E2` §1).
- **The horde in the boss**: Xesht's fight starts with a breach horde where
  "killing monsters adds to a timer"; Atziri's adds walk to her and heal her;
  the Shaper's add waves refill flasks.
- **Failures**: lingering ground that makes most of the arena unsafe (Shaper
  phase 3, Uber Maven's void zones, Aberroth's "countless DoT puddles");
  deaths that could not be seen ("no audio clue"); losing a whole attempt
  and its loot to one death (Path of Exile 2's citadels, the Arbiter before
  0.1.1); and, at the other end, the Eater of Worlds, called the easiest
  pinnacle for "slow, well telegraphed moves" that leave "way too much of a
  dps window". Telegraphs must be clear and short.
- **Uber versions**: a flat "70% less damage taken" plus a twist or two;
  cheap, popular, and the model for an endless-hour remix. Jonathan Rogers:
  "if you expect to die in a boss fight the first time as you'll learn it,
  then that's actually okay" ([Maxroll interview](https://maxroll.gg/poe/news/pax-west-path-of-exile-2-interview-with-jonathan-rogers)).

### 4.3 Grim Dawn, Titan Quest, Torchlight, Lost Ark and the Souls games

- **Titan Quest** publishes a flat boss contract: immune to crowd control
  ("1000% resistance"), 85–95% resistant to percentage-health damage,
  behind an ornate door that locks, guarding the best chest. It stops
  control builds trivialising bosses, and makes them useless at the
  climax. **Tartarus** is the closest ARPG analogue to an ember arena:
  timed waves at the player's exact level under a stacking curse, and
  every fifth battle the boss himself; his orb can be left untouched to
  make the next five battles harder and **double the chance of a unique**,
  a press-your-luck reward ([wiki](https://titanquest.fandom.com/wiki/Tartarus_~_Lord_of_the_Abyss)).
- **Torchlight III**'s early-access notes are a frank tuning record: boss
  health more than doubled after bosses died "in sub-30 seconds on multiple
  characters and builds"; hazards made "intentionally smaller than visual
  suggests"; the long, well-telegraphed slam given 200% damage and the fast
  claw 75%; the camera pulled out for a big boss; loot made to land a beat
  after the death.
- **Grim Dawn** turned invisible attrition into one readable blow. Its
  Celestial superbosses were felt as gear checks ("AFKed more than I was
  fighting"); version 1.2 added **Sunder**, a slow, named, dodgeable attack
  that leaves the player taking more damage for a while, slowed the
  animations of such attacks, and stopped them tracking the player late.
  Its Crucible (150–200 waves; cash out every ten; Celestial blessings
  bought between waves, our great blessings' nearest cousin) adds seconds
  to the bonus timer for every boss killed. Players there accept "a big
  telegraph ability that's meant for you to avoid", and hate the deaths
  that are coincidences of horde, projectile and a boss's death blast
  ("getting punished for killing stuff").
- **Lost Ark** has the clearest shared boss vocabulary in the genre, learnt
  once and reused: a **stagger** bar (empty it and the boss is held, and on
  Guardians each stagger permanently raises the damage it takes); a
  **counter** window (the boss glows blue before a charge; a counter skill
  landed then staggers it); **destruction** of armour and parts; phases
  keyed to a visible **bar count** ("x160"). Valtan destroys the arena's
  outer rings at bars 85 and 35 with a red decal on what will fall, and
  its earlier mechanics hand the player the tools for later ones (the
  towers' orbs survive the one-shot axe). Players hate shared wipes and
  colours reused for routine attacks ("imagine if someone had any sort of
  color blindness?"); Akkan was designed "significantly less punishing"
  after the backlash against Brelshaza.
- **Elden Ring and the Souls games**, where they transfer: posture as a
  hidden stagger bar, with weak points as posture multipliers; a delayed
  attack works from above only if the delay is drawn (a filling decal),
  otherwise it reads as random; a named signature move at a fixed moment
  with a universal answer (Malenia's Scarlet Aeonia opens her second phase
  every time and is dodged by moving sideways) becomes the story players
  tell; Radahn's meteor reads from above as a growing shadow.

Full notes and sources: `notes/E3_other_arpgs.md`. Elden Ring Nightreign,
the closest commercial analogue to a day-and-night run with a boss at
night's end, is in `notes/F1_nightreign.md` and §4.5.

### 4.4 What works from a top-down camera

| Works | Why | Example |
|---|---|---|
| Ground shapes with a fixed delay (1–2 s) | the camera looks at the floor; shapes read where sprites overlap | Belial's rings; Azmodan's corpses; Lilith's fissures |
| A slow-turning beam | the counter is a direction (circle), a learnable skill | the Lightning Hose; Malthael |
| Safe-sector and safe-tile puzzles | the answer is a place, seen at a glance | Malthael's sector; Grigoire's tiles; Zana's bubble |
| Telegraphs that track, then lock | a dodge window without a static target | Zir's Wing Blast; the Butcher's charge line |
| Hazards that grow with time or lost health | pressure rises without a wall | Andariel's layers; Azmodan's pools; Lilith's platform |
| Built-in punish windows | the boss is open after its big move | the Butcher stunned after charging a wall; HoloCure's A-chan |
| A voice before the killing move | sound cannot be drowned by effects | Sirus; Azmodan; the Maven |

| Fails | Why | Example |
|---|---|---|
| An always-on slow or aura with no counter | removes the only verb | Duriel's Holy Freeze |
| A hitbox larger than its decal | the decal lies | Belial; launch Lilith |
| One-shots layered with randomness | survived, never learnt | launch Uber Lilith |
| Long untargetable spells | "an Action-RPG without the action" | Uber Lilith; old Diablo IV immunity |
| Clones identical to the boss | tiny from above; which is real? | Baal's Vile Effigy |

### 4.5 Elden Ring Nightreign (FromSoftware, 2025)

The closest commercial analogue to our structure: a run that names its
final boss before it starts, two 15-minute days each closed by a shrinking
ring that herds the party into a night boss's arena, and a third day that
is the Nightlord fight. Full notes: `notes/F1_nightreign.md`.

- **The circle is the clock and the arena builder.** The Night's Tide
  appears at 4:30, shrinks for three minutes, holds, then shrinks again at
  11:00 to the boss's ground; in the rain the player takes escalating
  damage that becomes lethal after about two minutes (the wikis disagree
  on 100 s or 120 s) ([wiki.gg](https://eldenring.wiki.gg/wiki/Nightreign:Night%27s_Tide)).
- **The boss is known, so the run is preparation.** Each Nightlord's
  weakness is shown before the expedition. Before each night boss, "a short
  gauntlet of enemies spawns ... thematically related to the boss and
  therefore indicate its identity to allow for some preparation".
- **Weaknesses are scripted interrupts, not just multipliers**: a little
  lightning breaks Maris's arena-wide sleep channel; poison staggers Adel
  (in his first phase only); fire breaks Caligo's armour. Raids during the
  day preview the Nightlord's mechanics.
- **Everdark remixes** skip the teaching phase, start at the escalated one,
  and add one phase that changes the rules (a tornado safe zone for Adel, a
  possessing third entity for Gnoster, a weapon handed to the player for
  Maris), with +25–50% health. Players loved them; Everdark Libra's
  re-healed adds, clones and hexes made it the most hated.
- **The launch controversy**: boss health scaled with the number of players
  while survivability did not; solo players were punished and duos were
  "overlooked"; FromSoftware added an auto-revive per boss on day two, then
  solo buffs, then a duo mode two months later. Reception rose from Mixed
  to Very Positive as Everdarks and new Nightlords arrived. Losing a 40-
  minute run in seconds at the boss is the recurring complaint; rewards are
  paid win or lose, scaled to how far the run got.

### 4.6 ARPG horde arenas with bosses

The ARPG modes nearest an ember arena (`notes/F3_horde_arenas_and_missing_bosses.md`):

- **Path of Exile's Simulacrum**: waves started by the player, rising
  Delirium, bosses possible from one wave and guaranteed by a later one.
  GGG's data on 813,604 runs: waves 1–9 completed 99.9% of the time, wave 15
  96.35%, wave 20 76.25%, the sharpest drops at the boss guarantees: "the
  boss arrival *is* the difficulty curve" ([forum](https://www.pathofexile.com/forum/view-thread/2828348)).
- **Ultimatum's Trialmaster** carries every modifier the player accepted
  into his arena: the boss inherits the run's bargains. **Diablo IV's
  Infernal Hordes** end at the Fell Council (three of five, chosen at
  random), or, for 666 of the run's Burning Aether, at Bartuc instead: the
  boss as a purchase. Players there "go for Hellborne every time", the
  lesson against a dominant bargain.
- **Softening all-or-nothing loss**: Path of Exile 2 loosened its trials
  (retries, leave at any time); Blight keeps the chests of lanes already
  cleared; Gungeon's Resourceful Rat leaves his drops if you lose.

## 5. Roguelites that teach readable bosses

### 5.1 Risk of Rain 2 (Hopoo)

- **The teleporter event**: the boss arrives on top of the horde (it ignores
  the 40-monster cap) and must be killed while the player holds a charging
  circle about 120 m across for at least 90 s; natural spawns stop at 99%.
  Teleporter bosses have a red bar. **The Shrine of the Mountain** doubles
  the boss budget and the drops: an opt-in bet on one's own build
  ([wiki: Teleporter](https://riskofrain2.wiki.gg/wiki/Teleporter)).
- **Mithrix**: four phases. Phase 2 the boss leaves and the horde is the
  fight; phase 3 he returns and leaves fire pillars that burn for 45 s;
  phase 4 he **steals every item** and returns them as he is hurt. Hated
  until Hopoo made returns deterministic ("if you have him at 50% health,
  you will have 50% of your items back") and said "We want this to be a fun
  phase, not a frustrating conclusion". Players still scrapped items before
  the fight so he could not use them. Adaptive armour (30 armour per 1% of
  maximum health dealt in one hit, capped at 400, decaying 40 a second)
  taxes burst. Victory is a three-minute escape with the full build
  returned ([wiki: Mithrix](https://riskofrain2.wiki.gg/wiki/Mithrix)).
- **Voidling**: beautiful but "has committed the cardinal sin of being
  boring": three near-identical phases, very high health, long gaps.
  **False Son**'s rework added "Audio and Visual effects ... to every
  different False Son ability" to end "what just happened??" deaths
  (`notes/C2_ror2_hades.md` §1).

### 5.2 Hades and Hades II (Supergiant)

- **Phases as build protection**: Hades never scales boss health to the
  player, but every threshold gives brief invulnerability, and a patch fixed
  cases where "boss damage limits between phases could be bypassed". The
  Bone Hydra is invulnerable until its colour-coded support heads die;
  Tisiphone's walls close in at 50% and 25%.
- **Turning the player's tools**: Hades fires the player's own Cast;
  Theseus calls an Olympian who has *not* given the player a boon, and
  shouts "You cheat!" at a Greater Call. In Hades II, Hecate casts the
  player's Hexes (one turns Melinoë into a sheep); Eris wields the first
  game's Rail; Chronos turns Melinoë back into a child for one dodge-only
  phase; Unrivaled Cerberus has a barrier that absorbs 23 hits, a lever that
  ignores raw damage.
- **Remixes change the verb, the arena or the partner**: Extreme Measures
  gives Theseus a chariot with miniguns and frees the Hydra's head; Hades
  II's Vow of Rivals adds Medea, Charybdis, Heracles or Chronos and a new
  location. Players accept these, and reject the one that removes
  information: EM4 Hades's darkness ("you just make the screen dark so I
  can't actually see what's coming?").
- **Telegraphs**: Polyphemus has one glowing limb per move; Chronos's
  999-damage Time Burst lights the one safe numeral on a clock face;
  Prometheus clears the arena's lingering flames before his memory test;
  Typhon hides his health bar and shows **wounds** instead; his eggs hatch
  into elites unless broken in 10 s.
- **A warning for auto-firing games**: Polyphemus's "Where Are You?" counter
  punishes the player for hitting him, including with familiars and boon
  effects. A move that says "do not attack now" cannot work where weapons
  fire on their own.
- **Music as mechanic**: when Scylla's Sirens are knocked out their
  instrument leaves the song; players call it "masterful". Bosses comment on
  the player's loadout and losing streaks; a reward preview before the
  fight; a "Boss Vanquished" card and a safe room after
  (`notes/C2_ror2_hades.md` §2–3).
- **Disliked**: Polyphemus "definitely creates a need to have a ranged
  build"; a boss that invalidates an archetype is resented.

### 5.3 Enter the Gungeon (Dodge Roll)

Every boss has a DPS cap over a 3 s window (Keep 30 to Bullet Hell 80),
which works out at about 25–35 s a phase; the final update **raised** the
caps "so item combos and synergies will feel appropriately powerful", and
Boss Rush has none. A Master Round (a heart container) for a boss taken
without a hit; an intro card per boss; the High Dragun's last phase is a
survival puzzle between safe circles
([wiki: Bosses](https://enterthegungeon.wiki.gg/wiki/Bosses); `notes/D_readable.md` §1).

### 5.4 Nuclear Throne (Vlambeer)

Big Bandit opens a secret area if killed in under 10 s (speed rewarded,
not punished); his charge triggers on spacing rules (too close, or hiding).
Lil' Hunter's landing is shown by a shadow, and his health-gated summons
punish burst without a cap. Destroying the Throne's four generators takes
half its remaining health (on the first pass only) (`notes/D` §2).

### 5.5 The Binding of Isaac (McMillen)

Armour is health ÷ soft-cap DPS, so the number is the intended minimum
length in seconds (Hush 140, Mega Satan 90), with a 9% floor so broken
builds still win; Mega Satan turns invulnerable at fixed damage and calls
waves; Hush darkens the room as it loses health; Delirium, which becomes
other bosses, is hated for "0 pattern or telegraphing"
([wiki: Damage Scaling](https://bindingofisaacrebirth.wiki.gg/wiki/Damage_Scaling);
`notes/D` §3).

### 5.6 Hyper Light Drifter and others

Hyper Light Drifter teaches without words: strict faction colours, size as
threat, first-frame direction tells (Judgement's crouch shows the side of
its sweep), the Emperor stunned by its own exploding adds. Touhou names
every pattern and gives it a timer and a capture bonus; "survival" cards are
DPS-proof. Returnal keeps one colour per rule (purple: cannot dash through).
Cuphead teaches one skill per boss and shows progress on the death screen.
Silksong's bosses move into position before acting. Slay the Spire's Heart
takes at most 300 a turn. The Game Accessibility Guidelines: never colour
alone, never sound alone (`notes/D` §4–8).

### 5.7 What developers have said

From `notes/F2_dev_talks.md` (many talks exist only as video; where no
transcript could be read, the notes say so):

- **Wyatt Cheng** (BlizzCon 2014) on Greater Rift guardians: "we don't want
  randomness to dictate your success or failure"; a random boss should
  change how you play, not whether you win.
- **Grinding Gear Games** (Path of Exile 2, May 2025): two Ritual types and
  the Volatile Plants modifier were "responsible for over half of all player
  deaths in the endgame"; logging the cause of every death is how they
  found it. For the Arbiter of Divinity (July 2026) they made its voice
  lines "guaranteed for his notable skills" and widened the gaps inside
  combos.
- **Mega Crit** (Slay the Spire 2) removed a boss, the Doormaker, for being
  "a bit more complex than what we want"; its composer: at the boss "that
  threat level needs to feel amped up", by restating the act's motifs.
- **Studio MDHR** designs a Cuphead boss's patterns before its look (Game
  Informer, 2022).
- **Jan Willem Nijman** (Vlambeer): screenshake that "degenerates quickly",
  a freeze of "about 10-20 milliseconds whenever you hit something". With
  hundreds of creatures on screen, the heavy versions belong to boss hits,
  phase breaks and the kill (`docs/feel` makes the same point).
- **Supergiant** patched telegraphs to be clearer as attacks got harder
  under Extreme Measures, and tracks losing streaks so bosses can comment
  on them.

## 6. Player sentiment across the genre, and the also-rans

From `notes/X_sentiment_and_others.md` §14, which ranks complaints and
praise by how often they recur across games and sources (Steam threads and
reviews; Reddit through archives, §6 below).

**Complaints, most common first**: (1) the HP sponge ("Bosses are real HP
sponge", I Am Legion; "boss fights feel like chores", Nordic Ashes); (2)
cannot see the attack ("your own attacks blinds you", 20 Minutes Till
Dawn); (3) the build cannot answer the boss (Rogue: Genesia's Vampire Queen
healing faster than she is hurt, and its shielded Void Primordial, which one
player had at 0.005 health after about 18 hours at one frame a second, the
thread never confirming a kill; a Vampire Hunters statue "the
flamethrower literally cannot reach"); (4) wasted time after a long run;
(5) endless that is the same boss with more health ("isn't all that
enticing", Picayune Dreams' developer); (6) arena changes that outlast the
fight (Vampire Hunters' permanent slime); (7) single-stat checks; (8)
recycled bosses; (9) unexplained instant death.

**Praise, most common first**: (1) a mode switch into learnable patterns
(Picayune Dreams, whose bosses "are consistent and are meant to be
learned"; Halls of Torment's "FFXIV style AoEs"); (2) a big reward at the
kill; (3) a clear stage for the fight ("All regular bounty hunters then
retreat", Bounty of One); (4) felt growth (killing a once-impossible Lord
in ten seconds); (5) opt-in boss density for strong builds; (6) a boss that
breaks the game's rules ("The 'wait, it's doing what?' moment ... is where
the fun lives, not in harder stats", a MicroWars devlog); (7) control over
when the boss comes (Boneraiser Minions' extra waves).

Picayune Dreams shipped the most transferable small fix: "all bosses ...
automatically reduce your weapon visibility".

**Reddit** (read through archives; `notes/F4_reddit_sentiment.md`, with
thread scores): Vampire Survivors' Reaper still produces "did I win?"
threads, and players call the level-scaled fight "a waste of time... just
quit"; survivors players now expect an effect-opacity slider; Halls of
Torment players called an easier, longer second phase "a chore" and
defended dread over "epic" music; celebrated "deletion" clips of strong
builds are a genre of their own (show the time to kill on the victory
card); Deep Rock Galactic: Survivor's 30-second escape after the boss is a
top complaint, because "actually killing the boss" should be the optimal
play. Reddit and Steam agree with each other on every ranking above.

## Sources

Every claim above has its source in the notes, with inline URLs:

| File | Strand |
|---|---|
| `notes/A1_halls_of_torment.md` | Halls of Torment |
| `notes/A2_vampire_survivors.md` | Vampire Survivors and DLC |
| `notes/B1_brotato_20mtd_holocure.md` | Brotato, 20 Minutes Till Dawn, HoloCure |
| `notes/B2_soulstone_drg_dmd.md` | Soulstone Survivors, DRG: Survivor, Death Must Die |
| `notes/C1_more_survivors.md` | Ravenswatch, Megabonk, Nova Drift, Spirit Hunters, Army of Ruin, Magicraft |
| `notes/C2_ror2_hades.md` | Risk of Rain 2, Hades, Hades II |
| `notes/D_readable.md` | Gungeon, Nuclear Throne, Isaac, Hyper Light Drifter, Touhou, Returnal, Cuphead and the cross-cutting research on caps and accessibility |
| `notes/X_sentiment_and_others.md` | Rogue: Genesia, Vampire Hunters, Picayune Dreams and others; the sentiment synthesis |
| `notes/E1_diablo.md` | Diablo II, III and IV |
| `notes/E2_poe_le.md` | Path of Exile 1 and 2, Last Epoch |
| `notes/E3_other_arpgs.md` | Grim Dawn, Lost Ark, Titan Quest, Torchlight, Souls lessons |
| `notes/F1_nightreign.md` | Elden Ring Nightreign |
| `notes/F2_dev_talks.md` | Developer talks, interviews and patch-note statements |
| `notes/F3_horde_arenas_and_missing_bosses.md` | Simulacrum, Ultimatum, Infernal Hordes; Gungeon's Rat, Isaac's Mother and others |
| `notes/F4_reddit_sentiment.md` | Reddit, read through archives |

Each notes file ends with a "Verification" section: a second agent re-opened
the strand's most load-bearing claims and tried to refute them; corrections
are listed there and have been carried into this file.
