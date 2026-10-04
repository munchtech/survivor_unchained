> Research notes for `docs/bosses/`, kept as written. Where the **Verification** section at the end corrects a claim, the correction stands; `RESEARCH.md` uses the corrected version.

# E1 — Diablo II, III and IV: boss fights from an isometric camera

Strand E1 for the Survivor Unchained boss-fight design document. Research date: 3 October 2026. Claims marked "(secondary)" were seen only in a search-result summary, not on the page itself.

## Summary of lessons

1. **Telegraph on the ground, in a colour that belongs to the boss.** D3 standardised the vocabulary that still works from above: rings before a slam (Belial's green rings, Azmodan's red circle with a 1–1.5 s delay), a highlighted line before a charge (Butcher), a 1.5 s charge-up before a breath (Diablo), floor tiles that light before they burn (Butcher, Grigoire). Where the visual area and the real hitbox differ (Belial's slam is "slightly larger than its visual"; Uber Lilith's waves until Season 4), players call the fight unfair.
2. **Use sound and voice as a second channel.** Azmodan shouts a fixed line before his adds and before his pool attack; the Rift Guardian spawn is announced by a sound, a voice line and the sky darkening. In a crowded survivors screen, audio is the one telegraph that does not compete with particle noise.
3. **Clear the horde for the duel, or give the horde a job.** D3 Greater Rifts kill every monster within 100 yards when the guardian spawns. D4's Varshan makes adds a timed objective (kill the one he is channelling or he gains a buff); Duriel's burrow makes adds the gate. Adds that are filler help AoE builds and remove the challenge; Lilith's lack of adds hurt builds whose sustain comes from kills.
4. **Weak-to-absurd builds: use damage checks with time windows, not invulnerability or raw HP.** D4 Season 10 replaced immunity phases with breakable shields (1/3 and 2/3 of max HP, 5 s each): weak builds see the phase, strong builds earn the skip. Health buffs (+50–150% in 1.1.1) and cuts (−30%, −60%) never fixed a spread "ranging from 500k to trillions".
5. **Phase transitions must be overkill-proof.** A 2025 bug left Uber Lilith stuck invulnerable when her health fell "too quickly". A survivors build will cross several thresholds in one frame.
6. **An enrage should be a mechanic the player already knows, turned all the way up.** D3 Torment enrages at 3:00 make the Butcher's grates all ignite, Belial's meteors cover the platform, Azmodan's pools cover the arena.
7. **Arenas shrink and accumulate.** Azmodan's pools halve the safe radius; Beast in the Ice's blizzard constricts; Andariel adds a permanent hazard per intermission; Lilith's platform breaks at 85%, mid-phase and 30%. Rising pressure as HP falls is a natural, readable soft enrage.
8. **One-shots, no damage windows and randomness kill goodwill.** Launch Uber Lilith ("when is my turn to attack again?", "400 tries... hated every minute of it") is the series' cautionary tale; Blizzard swapped one-shots for "heavily ramping damage".
9. **A boss that is only a gear check is "of no consequence"** whether it lasts one second or sixty (streamer Macrobioboi). Give each boss one signature, learnable move (Diablo II's slow-turning Lightning Hose; Malthael's safe sector behind him).
10. **Make the spawn and the kill events.** Diablo Clone's realm-wide countdown messages, the Rift Guardian's darkened sky, all loot moved onto the guardian, Diablo III's exploding corpse and "Destroy Diablo" objective, Belial's rare post-kill ambush.

## What makes a boss mechanic work from a top-down camera (synthesis)

| Works | Why | Example |
|---|---|---|
| Ground decals with a fixed delay (1–2 s) | the camera looks at the floor; shapes read even when sprites overlap | Belial Fist Slam and Eruption (2 s); Azmodan corpses (1–1.5 s); Lilith fissures (1 s) |
| Sweeping beams with a slow turn | movement direction (circle, do not flee) is a learnable skill | D2 Diablo Lightning Hose; D3 Diablo Lightning Inferno; Wandering Death beams |
| Safe-sector or safe-tile puzzles | the answer is a place on screen, visible at a glance | Malthael's sector behind him; Grigoire's 2 of 9 tiles; Lilith's "stand where she is" during waves |
| Telegraph that tracks then locks | gives a dodge window without being static | Zir Wing Blast; Butcher Charge line |
| Hazards that grow with time or lost HP | pressure rises without a hard wall | Butcher grates; Andariel layers; Lilith platform |
| Built-in punish windows | the boss is vulnerable after its big move | Butcher stunned 1 s after charging into a wall; Malthael vulnerable while preparing Soul Sweep |

| Fails | Why | Example |
|---|---|---|
| Always-on slows or auras with no counter | removes the main verb (moving) | D2 Duriel's Holy Freeze in a tiny room |
| Hitbox larger than the visual | the decal lies | D3 Belial Fist Slam; D4 Lilith waves (fixed Season 4) |
| One-shots layered with randomness | cannot be learnt, only survived | launch Uber Lilith |
| Long untargetable periods | "an Action-RPG without the action" | Uber Lilith; old D4 immunity phases |
| Clones identical to the boss | from above, sprites are tiny; players cannot tell which is real | D2 Baal's Vile Effigy (players de-spawned it by leaving the screen) |


## 1. Diablo II (2000) and Diablo II: Resurrected (2021)

Diablo II's bosses are stat-checks more than pattern fights. They were built for a slow, attrition-based game with potions, resistances and town portals, and the "mechanics" are mostly elemental damage you counter with gear, plus one or two signature moves you can read and avoid. That is relevant to Survivor Unchained's day half: bosses here work because the arena and the gear check are the fight.

### Act bosses at a glance (official Arreat Summit stats)

| Boss | HP Normal / Nightmare / Hell | Signature threat | Arena | Source |
|---|---|---|---|---|
| Andariel | 1,024 / 24,800 / 60,031 | poison attack "she will cast when you get up close" | Catacombs lair with a small lake outside; guide suggests leading her "in circles around the little lake" | [Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act1-andariel.shtml) |
| Duriel | 3,995 / 55,799 / 84,524 | Holy Freeze aura (level 5, +30–35 cold damage; level 6 in Hell, +35–40); attack mix 17% melee, 33% Smite, 50% Jab | Tal Rasha's Chamber, a tiny sealed room | [Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act2-duriel.shtml) |
| Mephisto | 6,036 / 74,547 / 94,320 | Lightning, Charged Bolt, Poison Nova, skull missile, Frost Nova, Blizzard; Hell resists 75% to cold/lightning/poison/fire | Durance of Hate with his Council Members | [Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act3-mephisto.shtml) |
| Diablo | 13,818 / 90,749 / 113,812 | Red Lightning Hose ("half physical, half lightning"), Bone Prison, Fire Nova, Firestorm, Charge | Chaos Sanctuary, after opening five seals | [Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act4-diablo.shtml) |
| Baal | 26,484 / 117,596 / 493,701 | Vile Effigy clone, Festering Appendages tentacles, Mana Rift, Hoarfrost, Incineration Nova | Throne of Destruction waves, then Worldstone Chamber | [Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act5-baal.shtml) |

Note the scaling: Andariel goes from 1,024 to 60,031 HP across difficulties (about 59x), and Baal from 26,484 to 493,701 (about 19x) ([Arreat Summit, Andariel](http://classic.battle.net/diablo2exp/monsters/act1-andariel.shtml); [Baal](http://classic.battle.net/diablo2exp/monsters/act5-baal.shtml)). Diablo II copes with the player's power curve by re-running the same bosses at steeply higher numbers and resistances, not by new mechanics.

### Andariel: the gentle first gate

Andariel's only real "mechanic" is a poison burst at close range; the official advice is "Whenever possible fight from a distance" and to open a Town Portal before the fight so you can get back to your body ([Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act1-andariel.shtml)). The arena's lake gives a kiting loop. Lesson: the first boss teaches "stand back from the green thing" and that a loop in the room is a resource.

### Duriel: the tiny tomb, and why it is remembered as cheap

Duriel is the series' clearest example of the arena being the mechanic. You enter Tal Rasha's Chamber and he is already there, yelling "Looking for Baal?" ([Diablo Wiki](https://diablo.fandom.com/wiki/Duriel)). PlanetDiablo's period strategy guide says the room is "fairly small, so there isn't much space to maneuver in", that his Holy Freeze aura "turns your character blue and slows you down", that "Cannot be frozen" does not help, and that he "can take you out with one or two hits", especially Sorceresses ([PlanetDiablo archive](https://gamespy-archives.quaddicted.com/sites/www.planetdiablo.com/diablo2/strategy/general/duriel.shtml.html)). The fandom wiki adds that Holy Freeze is not affected by cold resistance, Cannot Be Frozen or Thawing Potions, though Thawing Potions reduce the cold damage ([Diablo Wiki](https://diablo.fandom.com/wiki/Duriel)).

Player reputation: commonly called the hardest boss on Normal "but for cheap reasons": you are under-levelled, trapped in a small room you can only leave by Town Portal, and slowed by an aura no item cancels (secondary, via [Atrocious Gameplay wiki](https://atrociousgameplay.miraheze.org/wiki/Duriel_(Diablo_II))). The "cheap" complaint is specific: the threat is not readable or dodgeable, the slow takes away the one verb the top-down ARPG gives you (moving), and the room takes away kiting. It is memorable precisely because it breaks the rules the rest of the game teaches. Survivor Unchained lesson: one claustrophobic boss can be a great set piece, but a slow that cannot be countered plus no room to move reads as unfair.

### Mephisto: the boss you can cheat with terrain

Mephisto's lair holds Council Members; the official guide suggests clearing them or isolating Mephisto with a Town Portal trick, and says cold and lightning resistance "helps a lot" ([Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act3-mephisto.shtml)). He is famous among farmers for the "moat trick" — standing across the lava moat where his AI cannot reach — which made him the classic magic-find boss (general community knowledge; not verified on a primary page in this session, so treat as unverified).

### Diablo: the Red Lightning Hose and the slow turn

Diablo is the best D2 example of a readable top-down signature attack. The Lightning Hose deals "half physical, half lightning damage" and full lightning resistance plus damage reduction or block "may allow you to survive" ([Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act4-diablo.shtml)). The fandom wiki gives the counter-play: "run around Diablo rather than away from him. Diablo turns slowly while casting the spell, making it quite easy to outrun it", but he often uses it "three times in a row", and stamina can run out, so walking makes it "almost impossible to evade" ([Diablo Wiki, Diablo (Diablo II)](https://diablo.fandom.com/wiki/Diablo_(Diablo_II))). That is a strong design: a sweeping beam with a slow turn rate is legible from above, and the answer (circle, do not flee) is a skill the player can learn.

Other D2 Diablo details:
- He opens with a fire circle; Bone Prison traps you, your hireling, or your Town Portal, so "Opening a Town Portal should be done out of sight" ([Diablo Wiki](https://diablo.fandom.com/wiki/Diablo_(Diablo_II)); [Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act4-diablo.shtml)).
- His AI does not leave the central area of the Chaos Sanctuary, so the four halls and seal areas are safe zones for potions and portals ([Diablo Wiki](https://diablo.fandom.com/wiki/Diablo_(Diablo_II))). This is an implicit leash; it keeps the boss fight in its intended arena.
- The build-up is the reward: you must open five seals, three of which release unique bosses with packs (Grand Vizier of Chaos, Lord De Seis, Infector of Souls) before Diablo appears ([Diablo Wiki](https://diablo.fandom.com/wiki/Diablo_(Diablo_II))). The finale is "a spectacular death animation" ([Diablo Wiki](https://diablo.fandom.com/wiki/Diablo_(Diablo_II))).

### Baal: the horde before the boss

Baal's Throne of Destruction is the closest thing in the Diablo series to a survivors-style "waves then boss" structure. Five waves, one per act ([almarsguides](https://almarsguides.com/Computer/Games/Diablo2/Quests/Act5/6EveofDestruction/)):

| Wave | Leader | Pack | Defining trait |
|---|---|---|---|
| 1 (Act I) | Colenzo the Annihilator | Fallen | fire enchanted, fire immune (secondary, [fextralife](https://diablo2.wiki.fextralife.com/Colenzo+the+Annihilator)) |
| 2 (Act II) | Achmel the Cursed | cold Skeleton Mages, Unravelers | magic-immune Unravelers |
| 3 (Act III) | Bartuc the Bloody | Council Members | lightning-resistant |
| 4 (Act IV) | Ventar the Unholy | Venom Lords | poison-immune |
| 5 (Act V) | Lister the Tormentor | Minions of Destruction | fire-immune |

Waves are triggered by clearing: "if no enemies are around Baal he'll summon the next wave or go through the Worldstone Portal, whichever is next" ([almarsguides](https://almarsguides.com/Computer/Games/Diablo2/Quests/Act5/6EveofDestruction/)). Each wave is built to exploit a different immunity, so the sequence is a build-coverage test before the boss. The final two waves are "extra difficult and worth the most by far" and wave 5's Minions of Destruction are "extremely difficult to defeat for many Classes and Builds" (secondary, [rankedboost](https://rankedboost.com/diablo-2/bosses/lister-the-tormentor/); [gamerguides](https://gamerguides.com/diablo-ii-resurrected/guide/where-to-farm/boss-runs/baal)). "Baal runs" — farming the waves for XP — became the standard levelling activity in multiplayer, so the waves outlived the boss as content.

Baal himself (in the Worldstone Chamber) mixes positional threats and resource drains ([almarsguides](https://almarsguides.com/Computer/Games/Diablo2/Quests/Act5/6EveofDestruction/); [Arreat Summit](http://classic.battle.net/diablo2exp/monsters/act5-baal.shtml)):
- Hoarfrost: "A V-shaped blue wave causing knockback and stun" — a cone telegraphed by shape and colour.
- Incineration Nova: dodgeable fire nova.
- Festering Appendages: tentacles from the ground "impeding the backward progress of his adversaries" — a zoning tool that punishes retreat.
- Mana Rift: removes half your stored mana.
- Vile Effigy: an exact clone at the same health percentage, used "should Baal be confronted with overwhelming numbers". Players learned to de-spawn the clone by leaving the screen, because the game "unloads monsters when they are off screen" ([almarsguides](https://almarsguides.com/Computer/Games/Diablo2/Quests/Act5/6EveofDestruction/)). Lesson: a clone that is indistinguishable from the boss is confusing from a top-down camera; give clones a visual tell.

### Über bosses and Diablo II: Resurrected

- **Über Diablo (Diablo Clone)**: spawned on Hell difficulty when enough Stones of Jordan are sold to merchants; the screen shakes and "Diablo walks the earth" appears. Monster level 110, 642,700 HP, 95% resistance to fire/cold/lightning/poison; drops the Annihilus charm ([Diablo Wiki, Über Diablo](https://diablo.fandom.com/wiki/Uber_Diablo)). In Resurrected, he spawns across a whole region, with escalating realm-wide messages from "Terror gazes upon Sanctuary" to "Diablo has invaded Sanctuary" ([Diablo Wiki](https://diablo.fandom.com/wiki/Uber_Diablo)). Patch 2.4 (14 April 2022) made the count tracked per region and separate for the eight ladder/non-ladder game types (secondary, [gfinityesports](https://www.gfinityesports.com/article/patch-notes-update-blizzard)). This is a great "event boss" pattern: a shared countdown builds anticipation before a single spawn.
- **Über Tristram (Pandemonium Event)**: transmute three keys to open a portal to a copy of Tristram holding Über Mephisto, Pandemonium Diablo and Über Baal together. Über Mephisto has a level 20 Conviction aura applying -125% to fire, cold and lightning resistances and summons skeleton mages and archers "everywhere"; Pandemonium Diablo has "tons of life" and summons Pit Lords; Über Baal summons Ghoul Lords and other undead. The last to die drops the Hellfire Torch ([Diablo Wiki, Über Tristram](https://diablo.fandom.com/wiki/Uber_Tristram)). The fight is three bosses roaming a town with their adds; the wiki's tips describe pulling Diablo and Baal away from Mephisto first and calling Mephisto "easily the hardest", with a Life Tap tip "If Life Tap isn't cast within the first 10-15 seconds, you will die" ([Diablo Wiki](https://diablo.fandom.com/wiki/Uber_Tristram)). Lesson: multiple simultaneous bosses force the player to split them with movement, which works from a top-down camera because you can see all three.

### What D2 teaches about top-down bosses
1. A signature attack with a slow turn (the Lightning Hose) or a clear shape (Hoarfrost's V) is readable from above; damage that is an always-on aura (Holy Freeze) is not, and players call it cheap.
2. The arena is half the fight: a lake to circle (Andariel), a tiny room (Duriel), a moat (Mephisto), seals and halls (Diablo). Leashing the boss to its arena (Diablo's AI stays in the centre) creates safe zones that give rhythm.
3. Waves before a boss (Baal) can be the best part, especially if each wave tests a different gap in the build.
4. Server-wide or run-wide countdowns to a boss spawn (Diablo Clone) generate anticipation for free.

## 2. Diablo III (2012) and Reaper of Souls (2014)

Diablo III moved the series from stat-check bosses to pattern bosses: ground decals, wind-ups, voice-line warnings, arena hazards and timed phases. It also produced the most survivors-relevant boss structure in the series — the Nephalem/Greater Rift, where a kill-driven progress bar summons a random boss and a 15-minute timer judges the whole run.

### Design intent (official)

Blizzard's 2010 encounter preview said the goal was to make encounters "more tactically interesting" without removing "accessibility, speed, and forward momentum", and defined "big hit" monsters whose attacks are telegraphed, slow and avoidable, but dangerous in tight spaces ([Blizzplanet, 23 Dec 2010](https://blizzplanet.substack.com/p/blizzard-previews-diablo-iii-monster-encounters-and-behavior)). In May 2012, community manager Nik Gionazakos explained why elites were harder and more rewarding than act bosses: "We didn't want 'boss farming' to become the goal of Diablo III the way it was in DII" ([Gameranx](https://gameranx.com/updates/id/6973/article/diablo-iii-why-are-elites-and-champions-are-more-challenging-than-act-bosses/)). That decision is why D3's story bosses became one-off set pieces and the Rift Guardian became the repeatable boss.

### The Butcher (Act I): telegraph vocabulary on day one

The Butcher's fight (an octagonal room split into seven fire-grate segments, two health pools) introduces every telegraph type D3 uses ([Diablo Wiki](https://diablo.fandom.com/wiki/Butcher_(Diablo_III))):
- **Wind-up as tell**: Heavy Smash — he "impatiently jumps two times (to allow visually predicting this move...)" before a cone slam. Advice: run to his side, "not directly away from him".
- **Line decal**: Charge "will highlight a straight line, and then charge in that direction"; at the end he headbutts the wall and is stunned for 1 second — a built-in punish window.
- **Pull plus combo**: Sickle Grab pulls a distant hero in and readies Heavy Smash.
- **Arena escalation**: fire grates highlight before igniting; "As the fight drags on, more and more of these grates will activate at once."
- **Enrage**: on Torment, a hard 3-minute enrage after which "all fire grates will activate at once and stay that way".

### Belial (Act II): the three-phase template

Belial is the cleanest D3 phase structure ([Diablo Wiki, Belial (Diablo III)](https://diablo.fandom.com/wiki/Belial_(Diablo_III))):

| Phase | Trigger | What happens |
|---|---|---|
| 1 | fight start | Belial does not fight; he summons a "large, yet, a limited amount" of snakemen on a timer, not on deaths |
| 2 | after phase 1 adds | Belial drops in with "relatively little health"; adds resume but "not for the first 30 seconds, so it is possible to finish Phase 2 without them even appearing"; three fast fly swarms along the ground |
| 3 | below 25% HP in phase 2 | Belial becomes his giant true form with full and "greatly increased" life, immobile, the whole inner platform edge counts as his body; immune to nearly all crowd control; remaining adds die |

Phase 3 attacks are all ground decals:
- **Fist Slam**: "A green ring appears on the ground where Belial is about to strike"; single slams or a three-hit combo with growing radius; after the combo he drops a health globe. The wiki warns the hit area "is slightly larger than its visual" — a readability bug worth avoiding.
- **Eruption**: every 50 seconds he slams both limbs for about 15 seconds while "small green rings will show up chaotically all over the arena. After two seconds, each ring explodes". This is described as "by far the most dangerous of his attacks".
- **Breath**: crosses the arena; avoided by hugging the left or right end.
- Health globes drop every 10% of damage in phase 3 — healing tied to progress.
- **Enrage**: on Torment, a hard 3-minute enrage where he "continuously use[s] his Meteor Strike, covering the entire platform at once (impossible to dodge)".

Player opinion is "divided" on whether Belial is one of the easier or one of the hardest D3 bosses (secondary, search summary citing [GamesRadar boss guide](https://www.gamesradar.com/diablo-3-boss-guide/4) and [ExpertBeacon](https://expertbeacon.com/who-is-the-hardest-boss-in-diablo-3/)). The transformation (small human emperor to screen-filling demon) is the memorable beat; the phase 2 "30-second grace before adds" is a neat detail that rewards strong builds with a cleaner fight.

### Azmodan (Act III): voice lines as telegraphs, shrinking arena

The Heart of Sin is a circular arena with a central pillar ([Diablo Wiki, Azmodan (Diablo III)](https://diablo.fandom.com/wiki/Azmodan_(Diablo_III))). His kit:
- **Falling Corpses**: "a red circle will appear around the player in a wide radius. After 1-1.5 seconds, corpses will fall all over the circled area for 3-5 seconds."
- **Globe of Annihilation**: a slow homing meteor that hits for "very high Fire damage within roughly 10 yards, enough to kill an adequately geared hero outright"; it explodes early if it hits the central pillar — terrain as counter-play.
- **Demon Gate**: portal devices that spawn Hell Brutes "roughly one every five-ten seconds" with no cap; a destroyed device gives a guaranteed health globe and devices are marked on the map. He announces it: "Arrogant Nephalem, my servants will feast on your pride as they devour your flesh!"
- **Pools of Destruction**: fast-spreading pools over the outer edge, "decreasing its safe radius by approximately one half"; announced by "Enough! The dark power of Hell will consume you!"
- **Eye laser** only when no hero is in melee range — an anti-kite tool.
- **Enrage**: Torment hard enrage at 3 minutes; pools cover the entire arena permanently.

Azmodan is the best example of an audio telegraph: two of his biggest moves are preceded by a distinctive shout. In a crowded survivors screen, a voice line is a telegraph that does not compete with visual noise.

### Diablo (Act IV): the shadow realm

The Crystal Arch fight has three phases and "no enrage timer" ([Diablo Wiki, Diablo (Diablo III)](https://diablo.fandom.com/wiki/Diablo_(Diablo_III))):
- **Phase 1**: fireballs leaving fire pools, Flame Circle, Firestorm, and Bone Prison — black pools on the ground; if caught, he teleports to you and drains you, but "cannot actually kill a hero (reducing to 1 Life instead)".
- **Phase 2** (at about 65% damage): he shunts you into the Realm of Terror, a "dark and shadowy counterpart" arena without healing wells, with impassable pits and "vision range is limited due to swirling fog" ([Diablo Wiki, Realm of Terror](https://diablo.fandom.com/wiki/Realm_of_Terror)). You fight the Shadow of Diablo ("roughly half the total health of Diablo in phase 1") and Shadow Clones of your own class — one per player, appearing every 45 seconds or after each third of the shadow's health; each drops a guaranteed health globe. Prime Evil's Curse applies one of seven 12-second debuffs.
- **Phase 3**: Diablo heals back to at least 65%, the arena is "constantly bombarded by little meteors", and he gains Lightning Inferno — a breath "charged up for 1.5 seconds" fired in his facing direction; avoid it by hiding behind one of the two crystals or outrunning it.
- **Victory**: at about 5% the "Destroy Diablo" objective appears; "After some time, Diablo's body will explode", followed by a cutscene and loot.

Lessons: the realm shift is a cheap but strong arena change (same geometry, new palette, fog), and fighting a clone of your own class is a memorable idea that scales the threat to what the player brought. The "cannot kill you" grab is a dramatic beat without being unfair.

### Malthael (Reaper of Souls): no enrage, survival not DPS

Malthael's platform is small and circular with two health wells ([Diablo Wiki, Malthael](https://diablo.fandom.com/wiki/Malthael)):
- Throughout: a knockback Charge that "can (and often will) kick the player into Death Shrouds"; Drain Soul (a whirling ring that can reflect projectiles); Death Shrouds (slow-moving cold clouds that he casts "faster the more health he is losing").
- **Phase 1**: Soul Nova — he lands in the centre and releases slow, sparse blobs to the edge; easy to dodge "especially if you stand close to the platform's edge".
- **Phase 2** (after 25% damage, announced only by the line "The end is inevitable"): Skull Spiral and two Exorcist adds that drop health globes.
- **Phase 3** (below about 50%, cutscene where he absorbs the Black Soulstone): Soul Sweep — five red flame waves in all directions except behind him, then "two wing-like lines of projectiles" sweeping round; "The sector behind him is the only place that remains clear". He spawns shrouds two at a time.
- Numbers: "7 billion [life] at Torment VI (70) for soloing heroes"; "no enrage timer (there have been precedents of fighting him for up to 3 hours on Torment VI)" — "more of a survival battle, not a DPS race".
- A subtle mechanic: slowing his attack speed enlarges the Soul Sweep coverage until damage becomes "unavoidable" — a player debuff that backfires, which is the kind of interaction that feels unfair if not signposted.

Opinion: critics found him visually imposing but forgettable as a character — "never around long enough to make players care" (secondary, [PC Gamer review-in-progress via search summary](https://www.pcgamer.com/uk/diablo-3-reaper-of-souls-review-in-progress)); some melee players liked "the need to actually move" (secondary, same search).

### Torment enrage rule (summary)

On Torment, D3 act bosses get hard 3-minute enrages that convert an existing arena hazard into total coverage: Butcher (all grates), Belial (platform-wide meteors), Azmodan (permanent pools) ([Diablo Wiki: Butcher](https://diablo.fandom.com/wiki/Butcher_(Diablo_III)), [Belial](https://diablo.fandom.com/wiki/Belial_(Diablo_III)), [Azmodan](https://diablo.fandom.com/wiki/Azmodan_(Diablo_III))). Diablo and Malthael have none. The pattern — enrage = the arena hazard you already learned, turned all the way up — is clean and readable.

### Nephalem Rifts, Rift Guardians and the Greater Rift timer

This is the system Survivor Unchained's ember arenas most resemble. From the [Diablo Wiki, Nephalem Rift](https://diablo.fandom.com/wiki/Nephalem_Rift) and [Rift Guardian](https://diablo.fandom.com/wiki/Rift_Guardian) pages:

- **Progress, not time, summons the boss.** A progress bar fills with kills; originally exactly 999 kills, since 2.1 weighted by monster strength; elites drop progress orbs worth 1% each (3–4 per pack in normal rifts, always 4 in Greater Rifts).
- **The spawn is an event.** At 100% a random Rift Guardian spawns "near the player (it is marked by characteristic sound, Orek's announcement, and darkening of the sky, so it's very hard to miss)". Sound, voice and a global lighting change — three channels at once.
- **The horde is cleared for the boss.** In Greater Rifts, "Once the Rift Guardian spawns, all other monsters within 100 yards die and despawn." This guarantees a readable duel after a dense horde, which is directly applicable to a 30:00 boss.
- **The timer.** Greater Rifts have a 15-minute timer; the guardian still spawns if the bar fills late, but to beat the rift "players must kill (not just summon) the Guardian before the time is up". Deaths add escalating respawn delays (5 seconds, plus 5 per death, up to 30).
- **Loot is moved onto the boss.** "Most monsters do not drop loot. All loot is moved to the Rift Guardian." Legendary gems come only from Greater Rift guardians.
- **Lock-in.** No skill or gear changes until the guardian dies, so you cannot swap to immunity amulets for the boss.
- **Scaling.** Each Greater Rift rank adds "on average" 17% monster life plus damage; rank 60 ≈ Torment XIII; no upper limit.
- **Guardian stats.** Each guardian has 35% more life than an average act boss for the difficulty, greatly increased damage, and extra abilities, often summoning minions "every few seconds". Ranged attacks often cannot be used in melee range; they never fire from off-screen; they take no damage beyond 100 yards; since 2.4 they teleport to a player if too far or pathing fails.
- **Close-out.** After the guardian dies you talk to Orek; the rift closes 30 seconds after you claim the reward, so you pick up loot first.

Maxroll's pushing guide says guardians have about "3.5x the HP of yellow elite packs" and "it can take very long times, up to half of your total 15 minutes on certain builds, to finally kill it"; AoE builds prefer add-summoning guardians such as Hamelin or Saxtris ("you can get extra targets for Area Damage"), while single-target builds prefer solo guardians ([Maxroll, Greater Rift Pushing Guide](https://maxroll.gg/d3/resources/greater-rifts)). Pushers "fish" for good maps and guardians, and Cold Snap is cited as a notably bad draw (secondary, search summary; source page not opened). Perendi summons Armored Destroyers every 20 seconds, increasing "up to five per cast when he is near death" (secondary, [Diablo Wiki mirror](https://breezewiki.discard.no/diablo/wiki/Perendi)).

What the Greater Rift teaches:
1. A random boss pool at the end of a timed run makes boss RNG decide success, which players tolerate in a leaderboard push only because they can re-roll quickly. For a 30-minute run, randomness in *which* boss should not swing the outcome as much.
2. Whether adds help or hurt depends on the build (AoE vs single target). A boss that summons adds is a gift to horde-clear builds — exactly the builds a survivors game produces. To test them, the boss itself must need single-target damage, or adds must be few and dangerous.
3. Moving all loot onto the boss makes the kill the payoff moment.

## 3. Diablo IV (2023 onward)

Diablo IV is the most useful case study for Survivor Unchained because it has lived through the exact problem a survivors game has: player power scales without limit, and Blizzard has spent three years trying to keep bosses meaningful against builds that range from under-geared to absurd. The history of patches is effectively a list of tools — health buffs, health cuts, immunity phases, breakable shields, stagger, damage reduction, randomised boss pools, timers — and how players reacted to each.

### 3.1 Echo of Lilith ("Uber Lilith"): the famous difficulty

**Mechanics.** From [Maxroll's Echo of Lilith guide](https://maxroll.gg/d4/bosses/echo-of-lilith) (current version, Torment I or higher):

*Phase 1 — Hatred Incarnate* (transitions at 70% and 40% with minion waves):
- Blood Orb Creation: "siphons the blood out of the player, dealing unavoidable damage", spawns volatile blood and three Dancing Lightning Orbs that orbit for 5 seconds then launch outward; hits stack a damage debuff.
- Fissure: "two series of parallel fissures on the ground in a criss-cross pattern", exploding after a 1-second delay.
- Wave of Spikes: "wide wave of demonic spikes that deals lethal damage on contact" from her and two shadow clones.
- Death from Above: she leaps away, three warning markers appear, then clones crash down and launch spike waves in one of four patterns (same direction, opposite, triangle plus slam, opposite plus slam).
- At 70%: two minions spawn and she spams Death from Above; at 40%: three minions and the triangle pattern.

*Phase 2 — Mother of Mankind:*
- Ground Slam pulls players in, summons 4–6 Children of Lilith, then "slams down onto the ground, dealing lethal damage in a large circle".
- Shadow Clone dash in three lines, then a large shadow explosion.
- Flight: she leaves and crosses the arena leaving cursed blood that "ignites, dealing lethal damage to all enemies caught in it".
- **Platform destruction**: below 85% HP the first section breaks — "6 seconds later, the cut-off section crumbles down into the abyss, instantly killing all players"; a second break mid-phase; a third below 30%, after which Flight has unlimited cooldown and she often casts it twice in opposite directions. PureDiablo notes the order is always top, then right, then left ([PureDiablo](https://www.purediablo.com/?p=43346), via search summary, secondary).
- Phase 2 Blood Boils/fireballs track players at about 145% movement speed; the guide recommends at least 145% movement speed ([PureDiablo](https://www.purediablo.com/?p=43346)). Since Season 3, phase 2 floor mechanics are "fixed": you can no longer burst her before the Blood Boils spawn ([PureDiablo](https://www.purediablo.com/?p=43346)).

Current rewards: 4 Paragon points, a Gilded Season Rank laurel, a Crux of the False Prophet, a Mythic Unique Journey Cache, an Atavistic Echo, Neathiron, and 1,600 each of Forgotten Souls and Obducite ([Maxroll](https://maxroll.gg/d4/bosses/echo-of-lilith)). Her first-kill spark (needed to craft Mythic Uniques) was the main reason to fight her ([mein-mmo](https://mein-mmo.de/en/diablo-4-endboss-sorgt-fuer-frust,1131291)).

**How players broke her at launch.** Within weeks of release (June 2023), Necromancers used vulnerable-damage stacking to kill both phases "in under two minutes", Sorcerers filled the stagger bar with crowd control and then burst her in the staggered window, and Rob2628 got the first clear with a Barbarian whose legendary affix "was scaling far above its intended levels"; PCGamesN commented that "being able to entirely negate mechanics does feel a bit like it circumnavigates a lot of the challenge" ([PCGamesN, 21 June 2023](https://www.pcgamesn.com/diablo-4/uber-lilith-cheese)). The first Hardcore kill was by Lightee's Whirlwind Barbarian exploiting a Wrath of the Berserker interaction (secondary, [esports.gg](https://esports.gg/news/diablo-4/lightee-secures-worlds-first-uber-lilith-kill-in-diablo-4-hardcore/)).

**Why players hated her.** The complaints are specific and instructive:
- One-shots against non-meta builds: "Uber Lilith fight is pure trash" (Reddit, quoted by [CharlieIntel](https://www.charlieintel.com/diablo/diablo-4s-trash-uber-lilith-boss-fight-is-one-shotting-max-level-characters-288403/)); the streamer Wudijo reportedly needed about 200 attempts (same source).
- Unpredictable patterns that cannot be memorised (same source).
- No offensive windows: "So uh… when is my turn to attack again?"; "The fight feels like an Action-RPG without the action"; players spend "half the fight playing ring-around-the-rosie" ([mein-mmo](https://mein-mmo.de/en/diablo-4-endboss-sorgt-fuer-frust,1131291)).
- Reward mismatch: "If she's made unfairly hard, it should at least be worth the effort" (Reddit user Darduel, via search summary of [mein-mmo](https://mein-mmo.de/en/diablo-4-endboss-sorgt-fuer-frust,1131291), secondary).
- Visuals not matching hitboxes, no adds to sustain life-steal builds, and a shrinking arena: "Has cost me 400 tries for the first kill. And I hated every minute of it" ([mein-mmo, 30 June 2024](https://mein-mmo.de/en/diablo-4-lilith-72-tries-0-hp,1144875/)).
- Necromancers could largely stand back while minions killed her, avoiding the problem ([mein-mmo](https://mein-mmo.de/en/diablo-4-endboss-sorgt-fuer-frust,1131291)).

**How Blizzard responded.**
- Patch 1.1.1 (8 August 2023) buffed boss health for bosses above level 60 by 50% at level 80 up to 150% at level 150, but excluded campaign bosses and Uber Lilith ([Gfinity](https://www.gfinityesports.com/article/diablo-4-latest-patch-controversial-boss-health-buffs)).
- For Season 4 (announced 22 March 2024), lead class designer Adam Jackson said her wave hitbox "will better match the visual", and waves and ghosts would no longer one-shot but "do heavily ramping damage as you get hit" ([Dexerto FR](https://www.dexerto.fr/diablo-4/blizzard-annonce-ajustements-majeurs-uber-lilith-diablo-4-saison-4-1549256/)). Replacing a one-shot with a stacking-damage debuff keeps the punishment but allows one mistake.
- A later bug shows the opposite end of the power curve: by Season 8, builds dealt damage so fast that Lilith became "stuck" in her phase-1 invulnerability state ([Icy Veins, 4 July 2025](https://wp-prod.icy-veins.com/invincible-uber-lilith-thanks-to-too-much-damage/)); patch 2.3.2 (29 July 2025) fixed "a bug where the Echo of Lilith could get stuck in the first phase if her health decreased too quickly" ([mein-mmo](https://mein-mmo.de/en/diablo-4-lilith-bug-patch-232-patch-notes-deutsch,1516844/)). **Lesson: any phase transition must be robust to overkill — damage that skips a threshold in one frame must still trigger the transition.**

### 3.2 The lair bosses (boss ladder)

Since Season 8, the ladder has three tiers ([Maxroll, bosses overview](https://maxroll.gg/d4/resources/bosses-overview)): Initiate (Urivar, Grigoire, Beast in the Ice, Echo of Varshan, Lord Zir; 1 Lair Key), Greater (Duriel, Harbinger of Hatred, Echo of Andariel, the Butcher; 1 Greater Lair Key, dropped by Initiates), and Superior (Belial; 1 Superior Lair Key, only from the Belial ambush). Fighting is free; you pay keys only to open the Hoard after a win, so "you only pay the cost if you succeed" (secondary, [Icy Veins Season 8 preview via search](https://www.icy-veins.com/d4/news/diablo-4-season-8-official-preview-belial-returns-boss-powers-endgame-boss-rework-and-much-more/)).

| Boss | Phase thresholds | Signature mechanics and telegraphs | Source |
|---|---|---|---|
| Beast in the Ice | intermissions at 66% and 33% | in intermissions the boss is invulnerable and untargetable, the arena "constricts due to blizzard", exploding adds spawn, and Strafing Run sends "waves of ice that sweep across the arena" with telegraphed safe zones; Icy Hail fires "4 icy explosions" in pentagonal patterns, then a second spread of 5 in phase 3 | [Maxroll](https://maxroll.gg/d4/bosses/the-beast-in-the-ice) |
| Grigoire | 80% (Charged Pylons), 60% (Galvanic Ascendance) | sparks float round the room after each mace hit; Thunderous Blow telegraphed by red circles; Galvanic Ascendance lights 9 floor tiles, 7 electrified and 2 safe; Knights Penitent spawn in a ring and converge | [Maxroll](https://maxroll.gg/d4/bosses/grigoire-the-galvanic-saint) |
| Echo of Varshan | none (same 3 abilities throughout) | Putrid Dance marks pink floor areas that explode after a delay (3 patterns); Summon Malignance — he summons 3 minions and channels to absorb one; kill the targeted minion before the channel ends or he gains Wrathful, Devious or Vicious buffs | [Maxroll](https://maxroll.gg/d4/bosses/echo-of-varshan) |
| Lord Zir | 80% (Blood Seekers), 66% (Wing Blast), 60% (empowered Blood Rain) | moving, merging blood puddles that shoot Vulnerable projectiles; Blood Orbs spawn adds about every 20% health; Wing Blast telegraph on the floor "initially tracks movement before locking position" | [Maxroll](https://maxroll.gg/d4/bosses/lord-zir) |
| Duriel, King of Maggots | burrows at 66% and 33% | burrowed: summons 3 Pangs of Duriel that must die before he re-emerges; his underground AoE deals "massive damage"; Rain of Maggots adds; Rampaging Charge | [Maxroll](https://maxroll.gg/d4/bosses/duriel-king-of-maggots) |
| Echo of Andariel | intermissions below 80% and 40% | three Effigies of Anguish with suppressor fields; persistent arena hazards accumulate (dust storm at the edge, counter-clockwise rotating sparks, blood stripes below 40%, a rotating fire beam between two skulls that divides the arena); attacks stack a Tormented damage-taken debuff | [Maxroll](https://maxroll.gg/d4/bosses/echo-of-andariel) |
| Belial, Lord of Lies | not specified | Crushing Slam swipes the whole platform; Toxic Breath beams end to end (echoing his D3 phase 3); poison pools spawn waves left and right; in his ambush form, Deception creates a weak decoy and Arena of Deceit "traps the player within a deadly circle and summons multiple decoys" | [Maxroll](https://maxroll.gg/d4/bosses/belial-lord-of-lies-boss-guide) |

**Patterns worth stealing:**
- *Interrupt-the-channel adds* (Varshan): the add is a timed objective, not filler; failing gives the boss a visible buff. This uses the horde productively.
- *Safe-tile puzzles* (Grigoire's 2-of-9 tiles) and *telegraph that tracks then locks* (Zir's Wing Blast) both read well from above.
- *Accumulating arena hazards* (Andariel): each intermission adds a permanent layer, so the arena gets harder as the boss's health falls — a natural soft enrage.
- *The ambush* (Belial): after a lair boss dies, a timer starts and "on rare occasions" Belial appears; beating him repeats the previous boss's loot and gives the Superior key ([Maxroll](https://maxroll.gg/d4/resources/bosses-overview)). A surprise second boss after the victory moment works well for an "endless after the win" phase.

### 3.3 Uber Duriel and the "loot piñata" problem

Duriel arrived in Season 2 as the only source of Uber Uniques (secondary, [Prima Games](https://primagames.com/news/duriel-brings-uber-unique-farming-to-diablo-4)). A four-player group recorded 43 Uber Uniques from 540 kills, about 2% (secondary, [GameLeap](https://www.gameleap.com/articles/diablo-4-season-2-what-is-the-drop-rate-of-uber-uniques)). Players reported "400 without an Uber, have quit the season" and a first Uber after 500 attempts ([mein-mmo, 12 January 2024](https://mein-mmo.de/diablo-4-300-duriel-runs/)). When a boss is killed hundreds of times, the fight becomes a summoning animation; the excitement moves entirely to the loot roll. For a survivors game that only has one boss per 30-minute run, this risk is much smaller — but endless play after the win should not turn the boss into a repeatable piñata.

### 3.4 Tormented bosses and the one-shot problem

Season 4 (May 2024) added Tormented level-200 versions of every ladder boss, summoned with Stygian Stones (secondary, [Wowhead / Dexerto search summary](https://www.wowhead.com/news=339165/new-changes-coming-to-ladder-bosses-in-diablo-4-season-4)). On the PTR, Rob2628 showed a Hurricane Druid one-shotting them and argued it was not acceptable; a Minion Necromancer could kill Duriel (reported as 10 billion HP) in one or two hits (secondary, same search; [mein-mmo](https://mein-mmo.de/en/diablo-4-ptr-op-builds-verbieten-helden-schwaechen,1113353)). The community split: some argued the damage spread "ranging from 500k to trillions" made bosses meaningless; others said overpowered builds are "the appeal" of the genre ([mein-mmo](https://mein-mmo.de/en/diablo-4-ptr-op-builds-verbieten-helden-schwaechen,1113353)). Then the mid-season patch 1.4.3 cut all Tormented bosses' health by 30% (including Lilith's Blood Boils) so "most builds are able to get to Tier 60" of the Pit (secondary, [Wowhead / Maxroll search summaries](https://www.wowhead.com/beta/news/diablo-4-mid-season-patch-1-4-3-patch-notes-class-changes-reduced-pit-difficulty-342951)). By Season 5, a four-player team was one-shotting Uber Lilith and every Tormented boss (secondary, [Icy Veins headline](https://www.icy-veins.com/d4/news/diablo-4-season-5-four-player-team-one-shots-uber-lilith-and-all-tormented-bosses)).

The lesson is the asymmetry: the same tuning pass that makes the boss a wall for the median player is still a one-shot for the top 1%. Health tuning alone cannot fix a distribution that wide.

### 3.5 Boss health: up, then down

| When | Change | Reaction | Source |
|---|---|---|---|
| 1.1.1, Aug 2023 | bosses above level 60 get +50% (level 80) to +150% (level 150) health; Uber Lilith and campaign bosses excluded | Wudijo: "This is really bad for a lot of builds"; Macrobioboi: "The issue with bosses wasn't that they died too quickly, [it] was that they're a gear check and then they're of no consequence." | [Gfinity](https://www.gfinityesports.com/article/diablo-4-latest-patch-controversial-boss-health-buffs) |
| 1.4.3, mid Season 4 (June 2024) | Tormented bosses −30% health | Pit made more reachable | secondary, [Wowhead](https://www.wowhead.com/beta/news/diablo-4-mid-season-patch-1-4-3-patch-notes-class-changes-reduced-pit-difficulty-342951) |
| Season 11 (late 2025) | dungeon bosses about −60% health, world bosses about −10%; capstone bosses lose their resilience stat; aim "less tanky, but more dangerous", "intense and deadly without dragging on" | — | [Icy Veins (Colin and Zaven interview)](https://wp-prod.icy-veins.com/?p=109114) |

Macrobioboi's line is the single most useful piece of player feedback in this strand: a boss that is only a gear check is "of no consequence" whether it dies in one second or sixty.

### 3.6 Immunity phases versus breakable shields (Season 10)

Before Season 10, lair bosses went fully invulnerable at thresholds (as Beast in the Ice still describes). In Season 10 (patch 2.4.0, 23 September 2025) Blizzard replaced immunity phases with damage shields: a shield appears at 2/3 health worth 1/3 of max health, and at 1/3 health worth 2/3 of max health; each lasts 5 seconds; break it in time and the boss "doesn't become invulnerable". Lead designer Ben Fletcher: "So if you're strong enough, you can still just straight up delete the boss and keep grinding" ([mein-mmo EN](https://mein-mmo.de/en/diablo-4-changes-the-most-annoying-boss-mechanic-actually-makes-some-of-the-best-builds-good-now,1526637/); [mein-mmo DE](https://mein-mmo.de/diablo-4-aendert-nervigste-boss-mechanik-oneshot/)). Players welcomed not having to "play through the annoying second battle phase anymore" (same source).

This is the clearest Diablo answer to "weak to absurd": a **damage check with a time window**. A weak build sees the full phase; a strong build is rewarded with a skip it earned; nobody is stuck waiting on an invulnerable boss. It also shows the cost: when a skip is possible, the mechanics in the skipped phase are never seen by the players who are strongest — so put the signature moment in a phase that cannot be skipped, or make the skip itself the spectacle.

### 3.7 Stagger

Bosses have a Stagger bar under the health bar that fills from crowd control (chill, daze, fear, freeze, immobilise, knock-down, knock-back, pull, slow, stun, tether); when full it turns blue and drains while the boss is effectively under all crowd control at once and cannot attack or move ([PureDiablo wiki, via search summary](https://www.purediablo.com/diablo4/Stagger_Meter), secondary). Season 12's patch 2.6.0 (11 March 2026) made bosses stagger "approximately twice as fast", stopped stagger from decaying, added a 20-second window where the boss is "5 times harder to Stagger", and raised the threshold 50% per extra party member ([Blizzard patch notes 2.6](https://news.blizzard.com/en-gb/article/24266869/diablo-iv-patch-notes-2-6); [Icy Veins](https://wp-prod.icy-veins.com/players-will-stagger-bosses-faster-in-diablo-4-season-12/)). Blizzard wanted it "more consistent and predictable, especially for builds that rely on crowd control but previously struggled to stack it quickly enough before the meter reset" ([Icy Veins](https://wp-prod.icy-veins.com/players-will-stagger-bosses-faster-in-diablo-4-season-12/)). Patch 3.2.2 (30 September 2026) fixed Pulverize being able to "indefinitely immobilize a Staggered boss" (secondary, [Blizzard patch notes search summary](https://d4guides.gg/en/news/diablo-4-patch-3-2-2-all-14-fixes-for-season-15-explained)).

Stagger matters for Survivor Unchained because it converts the horde-clearing tools a survivors build accumulates (slows, freezes, knock-backs) into boss damage windows without letting them lock the boss permanently. The post-stagger resistance window is the essential safety valve; without it (Pulverize bug) crowd control becomes a permanent lock.

### 3.8 World bosses

World bosses (Ashava, Avarice, Wandering Death, and since Season 11 Azmodan) are scheduled public events with a visible countdown, and "Joining the event after it starts is only possible for a short window" ([Maxroll, Ashava](https://maxroll.gg/d4/bosses/ashava-the-pestilent-world-boss-guide)). They have "a defensive interaction called Resilience, which causes them to take less damage than ordinary bosses" (no numbers given) ([Maxroll, Wandering Death](https://maxroll.gg/d4/bosses/wandering-death-world-boss-guide)). Telegraphs are large and graphic: Wandering Death's rotating Death Beams ("stay between them"), Death Crater with a 5-second detonation, and Death Grasp, where the "Ground change colors as if it's been combed" before hooks erupt (same source). Ashava's Double Swipe "Carves the ground in a 360-degree sweep, then carves again right after in a 180-degree sweep" ([Maxroll, Ashava](https://maxroll.gg/d4/bosses/ashava-the-pestilent-world-boss-guide)).

Despite Resilience, in Season 14 (from 30 June 2026) optimised groups killed Wandering Death at Torment 12 in under 10 seconds — "the world boss didn't fully spawn before dying". A commenter recalled that in the beta (level cap 25) world bosses lasted the full 15 minutes and "were still fun" ([mein-mmo](https://mein-mmo.de/en/diablo-4-spieler-absurd-stark-lassen-weltboss-platzen-vor-spawn,1575214/)). The beta 15-minute figure is a player recollection, not verified.

### 3.9 The Pit (Pit of the Artificers): a Greater Rift with a boss

The Pit, added in Season 4, is D4's version of the Greater Rift ([Maxroll Pit guide](https://maxroll.gg/d4/resources/pit-guide)):
- 15-minute timer; kill enough monsters to fill a bar and "a boss spawns close by".
- The boss is "randomized from the same list that is used in The Tower", with different HP and attacks; "some have annoying mechanics that can ruin a pit run".
- 150 tiers (later extended), with health and damage rising every tier.
- A full clear gives 4 glyph upgrade attempts, +1 for a death-free run.
- Deaths cost time — 30 seconds, then 60, then 90 for each later death; clearing with 4–6 minutes to spare skips a tier, 6+ minutes skips two (secondary, [search summary of Sportskeeda / fdaytalk guides](https://www.fdaytalk.com/diablo-4-pit-of-artificers-guide/)).
- Patch 1.4.2 adjusted Pit boss powers and affixes to be "more in-line with the difficulty of the dungeon leading up to the fight" and made affixes not overlap (secondary, [Icy Veins 1.4.2 headline / search summary](https://www.icy-veins.com/d4/news/diablo-4-patch-1-4-2-notes-pit-tuning-and-more/)).

### 3.10 Recent story bosses: Mephisto (Lord of Hatred)

The Lord of Hatred expansion's Mephisto fight (Torment X or higher) is a three-phase set piece at 66% and 33%, with phase names (Echo of Akarat, Echo of Mephisto, Hatred's Domain) ([Maxroll](https://maxroll.gg/d4/bosses/mephisto-boss-guide)). Notable mechanics: Maw of Hatred, where he "vanishes beneath waters" and waves drive players to the centre where an eruption is an instant kill; Wave of Defilement, which corrupts abilities until cleansed by orbs; Echoes of Hatred adds that mimic boss abilities. Maxroll calls the attacks "heavily telegraphed" (same source). It confirms D4's direction: telegraph clearly, then layer many simultaneous hazards in the last phase.

### 3.11 What D4 teaches
1. One-shots plus unclear hitboxes plus no damage windows (launch Uber Lilith) is the recipe players hate most. Blizzard's own fix was "heavily ramping damage" instead of one-shots and hitboxes matching visuals.
2. Health is the wrong lever for a wide power distribution: +150% health annoyed AoE builds without challenging the best builds; −30% and −60% cuts followed.
3. Breakable shields with a 5-second window are the best "weak to absurd" tool in the series: weak builds see phases, strong builds earn skips.
4. A boss needs adds if the player's sustain depends on kills (life-steal, on-kill effects) — a direct concern for a survivors build. Lilith's lack of adds was a specific complaint.
5. Phase transitions must survive overkill (the 2025 Lilith stuck-phase bug).
6. Stagger turns the horde-control toolkit into a boss-damage window, but needs a resistance cooldown so control cannot become a permanent lock.

## 4. Direct applications for Survivor Unchained

These are inferences from the evidence above, not findings.

- **The 30:00 boss as a Rift Guardian.** Copy the D3 Greater Rift beat: announce it on three channels (sound, voice line, global lighting change), and despawn or rout the ordinary horde near the player when it arrives, so the duel starts readable. Keep the horde only as the boss's own summons with a job (Varshan's channel, Duriel's burrow gate) or as fuel for kill-based sustain.
- **Phase gates as breakable shields.** At each threshold give the boss a shield worth a fixed share of max HP for a short window (D4 used 1/3 and 2/3 of max HP for 5 s). A weak build sees the phase; an absurd build shatters it and earns a spectacle. Never use a hard untargetable phase longer than a few seconds.
- **Clamp per-hit damage at thresholds and queue transitions**, so a single overkill hit cannot skip the transition code (the 2025 Lilith bug).
- **Stagger as the bridge between horde tools and the boss.** Let slows, freezes and knock-backs fill a bar that opens a damage window, with a resistance cooldown after each stagger (D4: 20 s at 5x resistance).
- **Enrage from the arena's own hazard.** If the boss is still alive at, say, 3 minutes after spawning, turn its existing hazard to full coverage (D3 Torment rule) rather than introducing an unseen wipe.
- **One signature move per boss that is a movement skill**, such as a slow-turning beam you circle or a safe sector behind the boss. These read from above and survive particle noise.
- **Post-victory surprise for endless play.** A rare ambush boss after the main kill (Belial) or a run-wide countdown to a special spawn (Diablo Clone) gives the endless phase its own events without devaluing the 30:00 victory.

## Gaps and caveats

- Exact HP values for D4 bosses (Lilith, lair bosses, Tormented versions) were not found on primary pages; the "10 billion HP" Tormented Duriel figure is secondary.
- Launch-era (June 2023) Uber Lilith specifics — her level, launch first-kill rewards and any 2023 hotfix to her damage — were not verified.
- Official Blizzard patch notes for 1.1.1, 1.4.2 and 1.4.3 could not be read directly (fetch blocked or truncated); those entries rely on news coverage, some secondary.
- D4 world boss "Resilience" has no published number in the sources found.
- D2 Mephisto's "moat trick" is community knowledge not verified on a page in this session.
- No GDC talk or postmortem on Diablo boss design specifically was found; design intent comes from the 2010 D3 encounter preview, a 2012 community-manager post, and 2025 interviews (Ben Fletcher; Colin and Zaven).
- Icy Veins pages often returned HTTP 403; their wp-prod mirror was used where possible.

## Verification

Adversarial fact-check, 3 October 2026. Each claim was checked against the cited page (Fandom pages read as wikitext through the Fandom API because the HTML returned HTTP 402; mein-mmo pages read as raw HTML, which came back in German).

| # | Claim | Verdict | Notes / correction |
|---|---|---|---|
| 1 | D2 boss HP and Duriel's Holy Freeze level | confirmed | Duriel 3,995/55,799/84,524, Holy Freeze level 5 (Normal/Nightmare) and 6 (Hell), +30–35 / +35–40 cold, attack mix 17/33/50%. The Diablo (13,818/90,749/113,812) and Baal (26,484/117,596/493,701) numbers are correct but come from their own Arreat Summit pages ([act4-diablo](http://classic.battle.net/diablo2exp/monsters/act4-diablo.shtml), [act5-baal](http://classic.battle.net/diablo2exp/monsters/act5-baal.shtml)), not the Duriel page. |
| 2 | D2 Lightning Hose: circle him, slow turn, "three times in a row" | confirmed | The wiki says "most often three times in a row" and adds a tell: he raises both hands, less than one second before it hits ([Diablo Wiki](https://diablo.fandom.com/wiki/Diablo_(Diablo_II))). |
| 3 | Baal waves start when no enemies are near him; each wave tests a different immunity; wave 5 fire-immune | partly right | The trigger quote and wave 5's fire immunity are correct. But almarsguides lists wave 1 (Fallen) as "no immunities" and wave 3 (Council Members) as "no immunities but highly resistant to Lightning". It never says each wave tests a different immunity; that is the notes' own inference, and it holds only for waves 2, 4 and 5. The wave-1 "fire immune" cell, from fextralife, conflicts with almarsguides ([almarsguides](https://almarsguides.com/Computer/Games/Diablo2/Quests/Act5/6EveofDestruction/)). |
| 4 | Belial: phase 3 below 25%, Eruption every 50 s for about 15 s with a 2 s ring, slam larger than its visual, 3-minute Torment enrage | confirmed | Wording nuance: the wiki says Eruption comes "if Belial survives ... for 50 seconds", so "every 50 s" is a fair reading but not stated outright ([Diablo Wiki](https://diablo.fandom.com/wiki/Belial_(Diablo_III))). |
| 5 | Greater Rift: 15-minute timer, monsters within 100 yards die, loot moved to the guardian, +17% life per rank | confirmed | All four statements are on the page verbatim ([Diablo Wiki](https://diablo.fandom.com/wiki/Nephalem_Rift)). |
| 6 | Azmodan voice lines, pools halve the safe radius, corpses 1–1.5 s | confirmed | Exact quotes match ([Diablo Wiki](https://diablo.fandom.com/wiki/Azmodan_(Diablo_III))). |
| 7 | Lilith phase 2 platform: 85% break, crumbles 6 s later; third break below 30% gives Flight "unlimited cooldown" | partly right | The thresholds and the 6 s are correct. "Unlimited cooldown" reverses the meaning: Maxroll says she "now has **no cooldown** on her Flight ability" and often uses it twice in a row. Fix lines 13, 223 ("unlimited cooldown" → "no cooldown") ([Maxroll](https://maxroll.gg/d4/bosses/echo-of-lilith)). |
| 8 | Season 4 Lilith changes, quoted from Adam Jackson | confirmed | The quote is from Adam Jackson, lead class designer, 22 March 2024 (a tweet quoted by [Dexerto FR](https://www.dexerto.fr/diablo-4/blizzard-annonce-ajustements-majeurs-uber-lilith-diablo-4-saison-4-1549256/)). |
| 9 | Patch 1.1.1 boss health +50–150% above level 60, Uber Lilith excluded; Macrobioboi quote | confirmed | 8 August 2023; campaign bosses are also excluded; both quotes are verbatim ([Gfinity](https://www.gfinityesports.com/article/diablo-4-latest-patch-controversial-boss-health-buffs)). |
| 10 | Season 10 shields at 2/3 and 1/3 HP (1/3 and 2/3 of max HP, 5 s); Ben Fletcher's "straight up delete the boss" | partly right | The mechanics are confirmed from the 2.4.0 patch-note excerpt, which also adds that invulnerability phases cannot trigger until 10 s into the fight. The Fletcher wording is not verbatim in the source. He was speaking on the 16 September 2025 livestream; the English mein-mmo page renders the line as "If you're strong enough, you can still just obliterate the boss", and the German one as "einfach zerlegen und direkt weitermachen beim Grinden". Present it as a paraphrase, or cite the original livestream ([mein-mmo EN](https://mein-mmo.de/en/diablo-4-changes-the-most-annoying-boss-mechanic-actually-makes-some-of-the-best-builds-good-now,1526637/)). |
| 11 | Patch 2.6.0 stagger changes | confirmed | 11 March 2026: "approximately twice as fast", no decay, "5 times harder to Stagger" for 20 s, +50% threshold per extra party member ([Blizzard](https://news.blizzard.com/en-gb/article/24266869/diablo-iv-patch-notes-2-6)). |
| 12 | Patch 2.3.2 (29 July 2025) Lilith stuck-in-phase-1 fix | confirmed | [mein-mmo](https://mein-mmo.de/en/diablo-4-lilith-bug-patch-232-patch-notes-deutsch,1516844/). |
| 13 | Season 14: Wandering Death at Torment 12 died in under 10 s, before fully spawning | partly right (season wrong) | The kill details are correct, but it happened at the **end of Season 13**. The article (30 June 2026, the day Season 14 launched) says the clip was posted "2 Tage vor dem Season-Ende". The beta comment is specifically about Ashava: "often needed the full 15 minutes to kill Ashava" (user Tezzinator), not world bosses in general ([mein-mmo](https://mein-mmo.de/en/diablo-4-spieler-absurd-stark-lassen-weltboss-platzen-vor-spawn,1575214/)). |

Other claims checked:
- **Lilith stuck-phase bug "by Season 8"** (line 241): partly right. The Icy Veins article (4 July 2025) is about **Season 9**, which had just started ([Icy Veins](https://wp-prod.icy-veins.com/invincible-uber-lilith-thanks-to-too-much-damage/)).
- **Baal Hoarfrost quote** (line 92): partly right. The phrase "A V-shaped blue wave causing knockback and stun" is a paraphrase, not a quote. almarsguides says: "the V shape blue wave that Baal shoots out that knocks you back. It will stun you when it hits you". Arreat Summit describes it as pushing back and *slowing*. The tentacles quote "impeding the backward progress of his adversaries" is not on the almarsguides page; it is presumably Arreat Summit wording, not verified.
- **Azmodan as a world boss since Season 11**: confirmed. He was the first new world boss since launch ([Icy Veins](https://www.icy-veins.com/d4/news/who-is-azmodan-diablo-4s-lord-of-sin-returns-in-season-11/)).
- **Season 10 start date of 23 September 2025**: confirmed by mein-mmo.
