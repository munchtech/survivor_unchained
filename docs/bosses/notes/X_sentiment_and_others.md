> Research notes for `docs/bosses/`, kept as written. Where the **Verification** section at the end corrects a claim, the correction stands; `RESEARCH.md` uses the corrected version.

# X — Other survivors-likes and player sentiment about bosses

Strand X: a sweep of survivors-likes not covered elsewhere (Rogue: Genesia, Vampire Hunters, Picayune Dreams, Bounty of One, Boneraiser Minions, Temtem: Swarm, I Am Legion, Yet Another Zombie Survivors, Grind Survivors, and briefer notes on others), plus a synthesis of player sentiment about survivors-like bosses. British spelling; "(secondary)" marks claims seen only in a search-result summary.

## Summary of lessons

1. **Dim the player's own effects during a boss.** Picayune Dreams made "all bosses ... automatically reduce your weapon visibility" after shipping it on the final boss only ([Steam news](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2088840&count=60&maxlength=0&format=json)). "Couldn't see it" is the second most common complaint across the genre.
2. **Give the boss the stage.** Announce it with a banner, pull the horde back or wall it off, and let the duel read (Bounty of One: "All regular bounty hunters then retreat").
3. **Never let a gate become a soft-lock.** Healing, shields, penetration checks and hard timers that a legal build cannot answer produced the worst stories in the sweep (Rogue: Genesia's 30-hour Void Primordial at 1 FPS). Every gate needs a fallback that grows with time, such as healing that weakens the longer the fight runs.
4. **Patterns, not HP.** The praised bosses (Picayune, Halls of Torment's Lord of Pain, Death Must Die's Lady) are learnable dodging dances; the hated ones are HP bags with 2–4 moves. "HP sponge" is the number one complaint.
5. **Make the boss break a rule.** For an auto-firing game the boss's job is to change movement and positioning rules, not to add HP: "The 'wait, it's doing what?' moment ... is where the fun lives, not in harder stats" ([MicroWars devlog](https://hdd42.itch.io/microwars/devlog/1493822/designing-bosses-for-an-auto-battler)).
6. **Check every boss against every drafted weapon.** If geometry or immunity stops a weapon type from hitting (Vampire Hunters' unreachable statue against the flamethrower), players feel cheated by the draft.
7. **Endless needs new mechanics, not more HP.** Picayune's own developer said re-fighting the same bosses "just with more health" is not enticing. Use opt-in boss density, remixes or boss rushes (Vampire Hunters constellations, YAZS Boss Rush).
8. **Arena changes should end with the fight**, and should collide the way they look (Vampire Hunters' permanent slime; Grind Survivors' barrier gaps).
9. **Pay out big at the kill.** Boss-exclusive chests and relics are the most consistently praised part of a survivors-like boss.
10. **Let players feel their growth.** Deleting a once-hard boss is part of the fantasy, and players like controlling when the boss arrives (Boneraiser's purchasable extra waves).

Note on method: Reddit itself (reddit.com and the redlib mirrors) could not be fetched from this environment, so Reddit opinion appears here only where a search summary surfaced it, and is marked "(secondary)". Steam discussion threads, Steam reviews and the Steam news API (`api.steampowered.com/ISteamNews/GetNewsForApp`) were readable and are the main primary sources for player and developer voice.

---

## 1. Rogue: Genesia (developer posts as "Plexus"; S-rank "Worlds Ascension" update March 2025)

**What it is.** A survivors-like built around absurd number growth: a run moves through zones, elites raise a "corruption" meter, and late-game health values are written with named suffixes (T, Qt, Sp, Sx). That number scale is the background to every boss complaint below.

### Bosses and mechanics
| Boss | Mechanic | Source |
|---|---|---|
| Vampire Queen (manor zone) | Spawns zone circles; standing in them drops her shield. At very low health she fires "life restore beams" that heal her. | [Steam thread "Unkillable Vampire Queen"](https://steamcommunity.com/app/2067920/discussions/0/595143167557246497); zone-circle detail from a search summary (secondary) |
| Vampire Queen, numbers | "default health and damage values of Vampire Queen at A-rank are 30K damage and 500T HP, in S-rank, those values are 1B damage and 500Sx" | Feb 2026 dev blog via [Steam news API](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2067920&count=60&maxlength=0&format=json) |
| Sand Worm | Shield that only breaks after killing a set number of elites; a counter in the top-left shows how many remain. | search summary of Steam discussions (secondary) |
| Void Primordial (endless, tier A) | Shielded; damage only lands if the build has enough defence penetration. A patch added damage to the boss "at a rate of 0.01% of damage dealt to the shields". | [Steam thread](https://steamcommunity.com/app/2067920/discussions/0/624417180895737619) |
| Generic late-boss phase | "when it gets to the phase where it teleports constantly and shoots projectiles, just run and dodge until the phase is over" | search summary (secondary) |

The design idea is sound: shields that ask for something other than raw DPS (stand in a zone, kill elites from the horde, have penetration). The Sand Worm in particular uses the horde as part of the mechanic, since the elites that feed the counter come out of the normal spawn stream.

### Where it fails: bosses that cannot be killed
The Rogue: Genesia forums are the clearest case study in this sweep of what happens when a boss's defensive mechanic and the player's build fail to meet.

- **Vampire Queen heals faster than you hurt her.** The thread "Unkillable Vampire Queen" starts with a player watching her health go "from 80 Qt to 8 Sp" and back without dying. They first blamed performance: "I turned off all weapons except Death Scythe, and that stopped the boss HP resetting all the time. This seems like the game engine doesn't work correctly if there are too many projectiles / low fps." The real cause was that at high corruption the low-health healing beams restored more than the player could deal. Another player: "This boss has poor design in my opinion." Later replies say she is "super easy" after nerfs. ([Steam](https://steamcommunity.com/app/2067920/discussions/0/595143167557246497))
- **Healing as a DPS gate stretches fights.** In the "BLOOD-HANDED" challenge thread one player reports spending 20+ minutes unable to damage her, and another relays that the developer was "considering a change to her healing, possibly making it heal less the longer the fight goes on." ([Steam](https://steamcommunity.com/app/2067920/discussions/0/595143167557277975)) A heal that weakens over time is a decent anti-stall rule worth noting.
- **Void Primordial: 30 hours at 1 FPS.** One player reports the boss with "quadrillion hp" could not be damaged directly, but lost HP slowly through the 0.01% shield-bleed patch; after 30+ hours at 1 FPS it was at 0.005 HP. A summoner player: "I'm on summoner and have no way to damage the boss... this sucks." He finished it "after watching a TV show". Another was at 5,084 HP after 15 hours. The developer asked for the save file. ([Steam](https://steamcommunity.com/app/2067920/discussions/0/624417180895737619))

**Lessons.** (1) A gate the build cannot answer (penetration, healing, shield) turns a boss from a test into a soft-lock. Every gate needs a fallback that scales with time, not just a token bleed. (2) Bosses must not depend on frame rate. Projectile-heavy late builds will drop frames, and heal or damage maths that is framerate-dependent will break exactly then. (3) Players let you disable weapons in Rogue: Genesia ("You can disable weapons by clicking on them in the weapon list", search summary, secondary), which shows the community already turning down its own effects to fight bosses.

---

## 2. Vampire Hunters (Gamecraft Studios; EA July 2023, 1.0 30 October 2024)

**What it is.** A first-person survivors-like: you fire your stacked weapons yourself while hordes close in. Runs are timed; at the 30-minute mark a reviewer found that "instead of an instant-death mechanic" they "were given a task to complete. Completion of the task led to the eventual end of the level." ([Thumb Culture](https://www.thumbculture.co.uk/vampire-hunters-1-0-release-pc-review)) That is the opposite of the Vampire Survivors Reaper: the end of the clock opens an objective, not an execution.

### Bosses and systems (from patch notes)
All from the [Steam news API for app 2206270](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2206270&count=60&maxlength=0&format=json):
- Named bosses and boss-elites include **Slayme** (a slime boss; an achievement asks you to "Remain fully slimed for 60 seconds straight"), **The Lava Thing** ("Molten fury in a monstrous form"), **Eye Tyrant**, **Warden of the Ankrahdoom** ("Collect his pieces and watch chaos unfold"), **Blue Oni**, **Iron Maidens**, and **Dracula**, fought in a dedicated final map, Dracula's Cave, where one challenge reads "You must defeat every boss he summons before taking him down."
- **Boss chests.** Defeating bosses drops special chests containing high-tier or boss-exclusive relics ([search summary of update coverage](https://gamedeveloper.com/press-release/vampire-hunters-new-major-update-out-today-on-steam-), secondary).
- **Boss frequency as a difficulty dial.** The August 2025 "constellations" (run modifiers) include: Pavo, "Bosses spawn twice as often. +100% Score"; Boötes, "When you kill an Elite, there is a 10% chance of spawning a random Boss. +300% Score"; Sagitta, "You collect Boss Chests instantly when you slay a boss. Bosses have +10% HP". The relic **Potion of Doom** will "Kill a random boss every time you collect a health potion".
- Dracula summoning all previous bosses at once is what players use to farm boss-kill achievements ([Steam "Bloodbath" thread](https://steamcommunity.com/app/2206270/discussions/0/604148672905642534)).

### Player sentiment
The venting thread "Does this game become less obnoxious to play?" lists "Bosses that teleport around, adding enemy-buffing pillars around the map" and "a boss that covers everything in slime... permanently", concluding "you have to rush these bosses, or else, your run becomes even more terrible." ([Steam](https://steamcommunity.com/app/2206270/discussions/0/4638240322751659013)) The complaint is not about difficulty but about **bosses that permanently degrade the run** if you are slow: the arena change outlasts the fight. Note that the developers later made Slayme removable from the boss pool via a modifier, which suggests the slime boss was a known sore point (inference from the patch line "Slayme is removed from the Boss Pool").

**Lessons.** Boss frequency and boss chests work well as opt-in risk/reward knobs. Persistent arena damage (slime, buff pillars) is resented when it punishes a weak build for the rest of the run; make arena changes end with the boss.

---

## 3. Picayune Dreams (developer posts as "Stepford"; launched late 2023, Contamination update February 2025)

**What it is.** The clearest "survivors waves, then real bullet-hell boss" hybrid. Its store page promises "a gauntlet of Bullet Hell bosses" in "high-octane, punishing battles" (search summary of the [Steam page](https://store.steampowered.com/app/2088840/Picayune_Dreams/), secondary). It draws openly on Vampire Survivors and Touhou.

### Bosses and the fixes that matter
From the [Steam news API for app 2088840](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2088840&count=60&maxlength=0&format=json):
- **Bosses dim your own weapons.** Contamination update (20 Feb 2025): "Just like the final boss, all bosses will now automatically reduce your weapon visibility and then return it to the default after the fight is over." Earlier (1.0.0.3, Dec 2023): "Ghost Boss now forcibly lowers weapon alpha, just like the Final Boss", and "Reverted Ghost Boss' blue bullets back to being red, like in the demo". This is the single most transferable readability rule in this strand: during a boss, the player's own effects fade so enemy bullets read.
- **Teleport telegraph.** "Added an indicator circle for when the Demon boss will teleport"; "Undying Horror Ghost will no longer be obscured by anything".
- **Crowd control immunity during attacks.** "Biker has stun/slow immunity during some attacks"; "Yuki can no longer be slowed or stunned". A strong build would otherwise freeze the pattern and erase the fight.
- **Gating levelling.** 1.1.0.9: "Disabled levelling up during 50 Mortality boss" (no level-up popups mid-pattern).
- **Scaling formula.** 1.1.0.14 (Jan 2025): "Boss Health gain per Overdrive level, 40% > 15% * clamp(Bosses Killed,10)", with the developer adding "(please tell me if the boss fights take too long now on high overdrives)". Also "Changed how 50 Mortality Boss calculates its phases, to remove some softlocks".
- **Spawn ordering.** "Statue of Distribution can no longer spawn before Bunny boss, as its effects are negligible at that stage".
- **Developer on looping.** In a one-year post (24 Nov 2024) the developer wrote that "the whole looping mechanic isn't particularly well balanced and fighting the same bosses that you have already been able to defeat (just with more health now) isn't all that enticing." That is the endless-mode problem stated by the person who built it.

### Player sentiment
- Positive: "Bosses harshly flip the gameplay around, as they are designed as bullet hell encounters, featuring bullet patterns that are consistent and are meant to be learned through multiple attempts before being mastered." Negative in the same review: "there is no change made even on subsequent loops. Bosses, and likewise, enemies, merely become harder numerically rather than mechanically." ([Steam review by Halicor](https://steamcommunity.com/profiles/76561198037951083/recommended/2088840/))
- Review summaries: it "skillfully mixes the appeal of the Survivors subgenre with few but very well done bullet hell bossfights"; "it feels more dependent on player skill than the upgrades ... by sheer virtue of the bullet hell bossfights"; "Each bullet hell boss is its own little dance to learn" (search summary of Steam reviews, secondary).
- Aggregated review analysis ([Vaporlens](https://vaporlens.app/app/2088840/picayune_dreams.md)) lists bullet-hell bosses as a positive theme ("challenging and intense boss fights that are both fun and satisfying") but also "boss variety ranges from inspired to 'just plain mean'" and "questionable boss balance contributes to dominant meta strategies".

**Lessons.** Picayune is proof that players accept a hard mode-switch at the boss, from power fantasy to pattern-dodging, if the patterns are consistent and learnable and the screen is cleared for them. Its weak point is the one every endless mode hits: the same boss with more HP.

---

## 4. Bounty of One (Ishtar Games)

**What it is.** A Wild West survivors-like for one to four players with a twist: your character must stop moving to shoot. Bounty hunters swarm you; "deputies" are mid-tier health-barred enemies; "sheriffs" are the bosses; the Undertaker (later joined by Ruthless Ruth in the Nightmare Escape mode) is the final boss.

### How the boss arrives
- "after a few minutes, a banner pops up telling you that the Sheriff is coming." All regular bounty hunters then retreat, leaving the player to face the boss alone. "The Sheriffs have a lot of health and deal a lot of damage, so make sure to dodge and use your dashes." ([GameGrin review](https://www.gamegrin.com/reviews/bounty-of-one-review/))
- So the boss arrival is announced in advance (banner) and the horde **withdraws**, turning the fight into a duel. Because shooting requires standing still, the duel becomes a rhythm of dodge, plant, fire. The reviewer liked this: evasion becomes the skill.
- Reward: sheriffs drop purple chests with exclusive items; the reviewer's favourite was "the 180-degree No Scope that allows you to shoot both in front and behind you" ([GameGrin](https://www.gamegrin.com/reviews/bounty-of-one-review/)). Deputies drop ordinary upgrade chests.

### Bosses as the difficulty clock
A balance line in the patch notes: "Enemies's life improves by 25/50/75/100% when you kill a sheriff" ([Steam news API for app 1968730](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=1968730&count=60&maxlength=0&format=json)). Each boss kill steps the whole horde up, so the boss is the run's tier boundary rather than a separate event. Ruthless Ruth arrived in the one-year update as "a new fearless boss to challenge your skills" (same source).

Telegraph advice from players (secondary, search summary of an achievement guide on [steamah.com](https://steamah.com/bounty-of-one-tips-for-100-achievements/)): to avoid "horses and bullets from Undertaker" dash diagonally and back; for Simple Tom "run horizontal until he starts to spin, then jump down and all bullets are dodged." Both describe learnable, positional patterns.

**Lesson.** Clearing the horde at boss arrival is the simplest readability tool in the genre (HoloCure and 20 Minutes Till Dawn do versions of it; see B1). Bounty of One adds a banner a few seconds before, and a global "every boss kill makes the horde stronger" rule.

---

## 5. Boneraiser Minions (developer posts as "caiys")

**What it is.** A survivors-like where you do not attack. You raise skeleton minions from the bones of the dead and they fight for you. That makes it the closest analogue to a fully auto-firing build: the player's only verbs are movement, dash and raising.

### Bosses
From the [Steam news API for app 1944570](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=1944570&count=60&maxlength=0&format=json) and the thread ["Need some tips for two of the bosses"](https://steamcommunity.com/app/1944570/discussions/0/3789255198746334162):

| Boss | Mechanics / notes |
|---|---|
| King Gigald | The main antagonist and final boss; on New Game Plus "The falling King will now be re-created when starting a new New Game Plus loop". Halloween event reskins him as "the Plump Pumpking". |
| Shinobi | Teleport slashes, returning shurikens; the teleport has a distinctive sound cue. Player tip: "walking in a square pattern and dashing straight up/down when they teleport usually gets me through with no-to-low damage." |
| Lunatic (Fanatic) | Orbiting tracking spheres; extra balls spawn at 60% and 30% health; orbit widens over time. Damage of "his big swinging balls" cut "to 14 (from 16)" (v35.25). Tip: lure "close > distant > close". |
| Lord of the Land | "The Flagbearer enemies that spawn mid-fight now use a new Trumpeter sprite" (adds summoned mid-fight). |
| Wizarding Councilor, Elven Warfinder | Tuned for readability: "fast fireballs are now slower"; "His basic arrows have been slightly slowed down (especially the Poison arrows)"; projectiles "now do 15% less damage". |
| Godly Vessel (v37) | "seeks to fill you full of his holiness spear" |
| Princess (v37) | Spectator boss: you are "forced to boneraise to the enjoyment of the watching Princess. She'll occasionally throw out an attack". |
| Fanatical Brother | Spawns "at the 5 minute mark" on Royal Causeway. Other bosses were pushed back: High Wizard "will now show up a minute later". |

Two developer notes matter for an auto-firing design:
- The Imp Contraptineer class got a buff because "the class struggled against the main bosses" (v36). A build archetype that clears hordes but cannot kill bosses is a known failure mode and gets patched at the class level.
- Players agree that the cure for hard bosses is minion damage: higher damage shortens the fight and so limits how many attack cycles you must dodge ([Steam thread](https://steamcommunity.com/app/1944570/discussions/0/3789255198746334162)). The developer congratulated an NG+ Gigald kill ("congrats on the Gigald pounding"), which the player called "crazy" ([Steam](https://steamcommunity.com/app/1944570/discussions/0/4629233379372501457)).

**Lessons.** HP-threshold add spawns (60%/30%) give a pure-movement player something new to read in each phase. Slowing projectiles is the standard fix when a boss is unreadable for a player who cannot shoot back on demand. The "spectator boss" who lobs occasional attacks while you fight the horde is a cheap way to make a whole stage feel like a boss stage.

---

## 6. Temtem: Swarm (Crema; 1.0 2 April 2025)

**What it is.** A co-op (up to three players) creature-collecting survivors-like.

- Structure: "Two mini bosses await in each arena, carefully selected to match that arena's typings and lore, with the first mini boss spawning at minute 5 and the second at minute 10" (search summary of developer/press material, secondary), followed by a stage boss.
- The 1.0 update added the Evershifting Tower, where "three sensational, boosted mini-bosses" from earlier maps return before a new final boss "that reigns over the skies" ([Steam news API for app 2510960](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2510960&count=60&maxlength=0&format=json)). Reusing earlier mini-bosses as a final gauntlet is the same pattern HoloCure uses (B1).
- Concrete numbers from the 1.0 balance notes (same source): mini-boss Zizare "Base HP decreased: 5,292 ➜ 4,500", "Base Damage decreased: 70 ➜ 60"; final boss Galios base damage "100 ➜ 90"; its Umbra variant "120 ➜ 110".
- Type matchups shape boss fights: the stage boss Oceara is pure Water, weak to Nature and Electric, and heals with Sanative Rain (search summary, secondary). A third-party guide describes a three-phase fight at 100–70%, 70–30% (screen-filling waves, "the real wall") and 30–0% (charging dashes) ([PixelNitro](https://pixelnitro.com/?p=3710)), but that page reads like generated SEO content, so treat the thresholds as unverified.

**Lesson.** A 5/10/final cadence with themed mini-bosses is a clean template; a final "boss rush of earlier mini-bosses" reuses content while feeling like a climax.

---

## 7. I Am Legion: Stand Survivors (2024–25) — the boss timer

A small survivors-like whose bosses are fought against a **time limit**. Its patch notes are a short lesson in how such timers get tuned after launch ([Steam news API for app 3109580](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=3109580&count=40&maxlength=0&format=json)):
- Demo / 1.0.7a: "Extended the first boss's time limit from 3m to 3m30s".
- 1.0.2a (25 Feb 2025): "Extended BOSS challenge time (First BOSS: 3:30 → 4:00, Second BOSS: 3:00 → 4:00)".
- 2.0.1d: "In Classic Mode, the first boss now always drops an Awakening Scroll." v2.0 mentions "Boss Kill Time Rewards".

The Steam thread "Bosses are real HP sponge" ([Steam](https://steamcommunity.com/app/3109580/discussions/1/597394771139398521/)) shows why: "Crazy, the bosses hp are way too huge"; "we got an update giving more time, cause they had indeed a lot of hp, so timer had to be increased"; and "Bosses are HP sponges in the later difficulties ... you have to rely on getting a good start, if you get a garbage start you just lose." Defenders answer with meta-progression ("Once you level up your character and update your meta progression tree, it becomes way easier") and set bonuses ("a huge boss damage boost like 60%").

**Lesson.** A hard DPS timer on a boss turns any weak draft into a guaranteed loss, and players read it as RNG ("good start or you lose"). If a timer exists, the safer use is as a **bonus** (kill-time rewards) rather than a fail state, which is the direction this developer also moved.

---

## 8. Yet Another Zombie Survivors (1.0 on 20 August 2026)

The developers were asked for real bosses by players during Early Access. A developer replied: "Yes, we'll be adding main bosses in addition to the current, 'normal' boss monsters", one main boss per area ([Steam thread](https://steamcommunity.com/app/2163330/discussions/0/601898034735932566)). The 1.0 changelog lists "5 main bosses, 2 standard bosses & 3 new standard enemies" and a Boss Rush mode, billed in May 2026 as a "REAL boss fight game mode, in which you'll face the toughest of foes so far". In Boss Rush you are "racing the clock to get as powerful as you can before the 10'th minute mark, at which point the Final Boss spawns"; it unlocks after Hardcore on each map, and clear times go on per-arena leaderboards ([Steam news API for app 2163330](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2163330&count=60&maxlength=0&format=json)). Version 1.1 added a boss rematch feature (search summary, secondary).

**Lesson.** A two-tier boss vocabulary ("normal" timed bosses that are big enemies, and authored "main" bosses) is what players asked for here, and the authored ones then became a standalone mode with leaderboards. Boss Rush with a fixed "build window then boss" clock is a natural post-game for Survivor Unchained's endless play.

---

## 9. Spellbook Demonslayers, Nordic Ashes, Survivor.io: thin evidence

- **Spellbook Demonslayers** (2022): "Boss enemies also drop chests, which you can pick up for ability upgrades too" ([GamingOnLinux](https://www.gamingonlinux.com/2022/08/spellbook-demonslayers-is-the-most-insane-vampire-survivors-like-yet)). One user found that after the jungle area they were killing bosses in 2–3 turns by spamming blood magic and fire (search summary, secondary). No boss mechanics found.
- **Nordic Ashes: Survivors of Ragnarok** (2023): advertises "Elites and Bosses with their own behaviors to make battles more epic", and Twitch integration that names elites and bosses after viewers (search summary of the store page, secondary). Bosses include God Surt and Fenrir, the final boss of Sandheim, with a 2024 global community challenge to "Defeat Fenrir to earn points" ([Steam news API for app 2068280](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2068280&count=60&maxlength=0&format=json)). Review aggregation: "some boss fights feel like chores due to inconsistent difficulty scaling" ([Vaporlens](https://vaporlens.app/app/2068280/nordic_ashes_survivors_of_ragnarok.md)). One negative Steam review (id 234437714): "95% of deaths are from running away from 500 enemies and then a boss summoned something underneath you that you couldn't see" ([Steam reviews API](https://store.steampowered.com/appreviews/2068280?json=1&filter=all&language=english&num_per_page=100&purchase_type=all)). That is the classic crowd-hidden telegraph complaint.
- **Survivor.io** (Habby, mobile): chapter 1 has three bosses: "Boucebloom" ("fires three projectiles that scatter and bounce off surfaces"), "Devourer" ("If you stand still, Devourer will rush towards you") and "Steel Ghasher" ("Just dodge his projectiles") ([TouchTapPlay](https://www.touchtapplay.com/how-to-beat-chapter-1-in-survivor-io/)). Players on the French App Store complain that "les chapitres sont vraiment très long (entre 10 et 15 minutes)" ([App Store](https://apps.apple.com/FR/app/id1528941310)). Guides advise the Kunai because it is "effective against Bosses", which shows the horde-weapon / boss-weapon split even in the most casual entry (same TouchTapPlay source). I could not verify from a primary source the commonly described Survivor.io rule that the boss spawns inside a closing barrier.

---

## 10. Hero Siege (ARPG with horde density) — relevant to the day half

Hero Siege is closer to Diablo than to a survivors-like, but its pinnacle boss is a useful model for linking story bosses to an endgame fight. Each Act boss drops one of six artifacts; "When you have collected all artifacts you can summon Uber Damien, a boss", by talking to an NPC in town. Players say: "He has about 20-25 million health and his laser will one hit you" ([Steam thread](https://steamcommunity.com/app/269210/discussions/0/487876474228053027)). A collect-the-keys-from-story-bosses, summon-the-pinnacle-boss loop could link Survivor Unchained's day bosses to a night-arena challenge.

(Windblown and Rogue Survivors were on the candidate list. Windblown is a Dead Cells-style action roguelite, not a survivors-like, and I found nothing boss-specific for Rogue Survivors worth reporting, so both are omitted.)

---

## 11. More player voice from Steam review data

Pulled from the Steam reviews API (most-helpful English reviews), quoted verbatim:

- **Picayune Dreams** (positive, id 236115885): "The bullet hell aspect comes into play when you reach the first boss, but if you don't focus on killing it then the longer it'll throw bullets at you." Positive, id 236064423: "the bosses are fantastic, each one has a nice thing going on with them and are all very fun to fight in general even if some are easy." Positive, id 236442187: "it's got fun bullet hell bosses, amazing music..." ([API](https://store.steampowered.com/appreviews/2088840?json=1&filter=all&language=english&num_per_page=100&purchase_type=all))
- **Rogue: Genesia** (positive, id 235456066): "Boss encounters provide memorable spikes in difficulty, pushing mastery of movement and timing." ([API](https://store.steampowered.com/appreviews/2067920?json=1&filter=all&language=english&num_per_page=100&purchase_type=all))
- **Vampire Hunters** (negative, id 235241393), on weapons that cannot engage a boss: "Boss 2 is a floating skull that shoots fireballs... If you try to use a flamethrower during this fight getting close enough to it will usually mean you get shot"; "Boss 3 is a giant statue in the middle of the floating ring... Also the flamethrower literally cannot reach the boss". Negative, id 235096242: "DEMANDS ARE FOR DAMAGE. WEAPONS DO NOT MEET THE DEMAND MINUS THE PIRATE CANNON, AND THEN IT FALLS OFF WHEN HORDES START TANKING HITS". ([API](https://store.steampowered.com/appreviews/2206270?json=1&filter=all&language=english&num_per_page=100&purchase_type=all)) The first is the clearest statement in this sweep of a boss whose geometry quietly invalidates a drafted weapon.
- **Boneraiser Minions** (positive, id 235138067): "You can spend your hard earned gold to unlock new enemy waves that show up, which will delay when the final boss shows up, thus allowing you to farm more XP and get super strong." ([API](https://store.steampowered.com/appreviews/1944570?json=1&filter=all&language=english&num_per_page=100&purchase_type=all)) Players like controlling *when* the boss arrives relative to their power.

---

## 12. A design principle from an auto-battler developer

The MicroWars devlog "Designing bosses for an auto-battler" ([hdd42 on itch.io](https://hdd42.itch.io/microwars/devlog/1493822/designing-bosses-for-an-auto-battler)) addresses the same problem: the player does not aim, so what makes a boss? Its answer: "A boss fight needs to feel wrong the moment the map loads. So every boss breaks something the normal game enforces." Its Titan breaks stat limits (defence 40 against the usual 2–5), Mimic copies the player's own type and cards, Hydra splits four times faster, and Plague makes five enemy colonies ignore each other. "The best bosses take a rule the game normally enforces ... and bend it just far enough to be wrong", and "The 'wait, it's doing *what*?' moment when the arena loads is where the fun lives, not in harder stats." Boss maps also switch off the usual passive win conditions, forcing direct engagement.

For an auto-firing game this is the most useful framing found: since the player's damage output is automatic, the boss's job is to change the *rules of movement and positioning* (Picayune's dimmed weapons, Bounty of One's withdrawn horde, Rogue: Genesia's stand-in-the-circle shield), not to add HP.

---

## 13. Grind Survivors: a case study in thin bosses

Two of the most-helpful negative Steam reviews ([Steam, top-rated reviews](https://steamcommunity.com/app/3816930/reviews/?browsefilter=toprated)) are almost entirely about bosses:
- Reskins: "the bosses have exactly the same attacks, and all of them (except for the Spider and the Winged Demon) are the same only differing in color"; "the bosses in the third mission (except for the final boss, the Worm) are a simple repaint".
- Too few moves: "the final boss of the level (while having new model and effects) only having grand total of 2 attacks, both copied from the final boss of lvl 1"; "the 3rd boss, all it does is reuse attacks from other enemies/bosses AGAIN".
- Arena rule that contradicts its own visuals: "The arenas that appear during the boss fights disappear gradually. You intuitively expect to be able to slip through the gaps. But no, you can't until the entire barrier disappears".

**Lesson.** If a boss barrier is drawn as breaking up, its collision must break up with it. Players will forgive a weak boss more readily than a boss that is visibly recycled.

---

## 14. Player sentiment across the genre: synthesis

This section draws on the games above and cross-references the sibling notes (A1 Halls of Torment, A2 Vampire Survivors, B1 Brotato/20MTD/HoloCure, B2 Soulstone/DRG:S/Death Must Die, C1). Quotes already given in those files are only pointed to here.

### What players say they want
- **"Real" bosses, as distinct from big enemies.** Yet Another Zombie Survivors players explicitly asked for "main bosses" on top of the timed "normal" boss monsters, and the developers built them and then a Boss Rush mode around them ([Steam](https://steamcommunity.com/app/2163330/discussions/0/601898034735932566)). A Reddit comment surfaced by search praises Halls of Torment because it "has a couple unique boss types in each level that are much more engaging fights than the usual VS dps check style bosses" (secondary, search summary of an r/SteamDeck thread). On ResetEra: "the bosses with their FFXIV style AoEs are super fun" (Beelzebufo, [ResetEra](https://www.resetera.com/threads/halls-of-torment-looks-like-it-could-be-good-competition-for-vampire-survivors.796848/)).
- **A pattern to learn and a dance to perform.** Picayune Dreams' bosses are praised because their patterns "are consistent and are meant to be learned" (above). Death Must Die's Lady is "so fun because you can dance with her" (B2). Halls of Torment's Lord of Pain, the hardest Lord, is also the most loved because it "feels very bullet-hell" (A1).
- **The power payoff.** A Halls of Torment player "came back to Lord 1 an killd him in 10 seconds. You really feel the power" (A1). Bosses that were once walls and later melt are part of the meta-progression fantasy, not a failure of it.

### Why players hate them
The complaints recur across every game examined. Ranked by how often they appeared across games and sources in this sweep and its siblings:

| Rank | Complaint | Where it shows up (examples) |
|---|---|---|
| 1 | **HP sponge: long fight, few moves.** Bosses that are the horde's enemy with a bigger health bar, or authored bosses with 2–4 attacks repeated over a long fight. | Halls of Torment Lord of Regret, "ten million friggin' HP" (A1); I Am Legion, "Bosses are real HP sponge" ([Steam](https://steamcommunity.com/app/3109580/discussions/1/597394771139398521/)); Nordic Ashes "boss fights feel like chores" ([Vaporlens](https://vaporlens.app/app/2068280/nordic_ashes_survivors_of_ragnarok.md)); Vampire Survivors bosses that "have far more health, but otherwise behave the same" (A2); Grind Survivors "grand total of 2 attacks"; Brotato elites "too spongey" (B1); Soulstone (B2). |
| 2 | **Can't see the attack.** Telegraphs hidden under the horde or under the player's own weapon effects. | Nordic Ashes "a boss summoned something underneath you that you couldn't see"; 20MTD Hastur, "your own attacks blinds you" (B1); Soulstone (B2); DRG:S jump (B2); Rogue: Genesia players switching off their own weapons; Picayune Dreams shipping a fix that dims player weapons during every boss. |
| 3 | **The build cannot answer the boss.** Healing, shields, penetration checks, time limits or geometry that a legal horde-clearing build has no answer to, so the run is lost or soft-locked through no fault of play. | Rogue: Genesia Vampire Queen and Void Primordial (30 hours at 1 FPS); Vampire Hunters "the flamethrower literally cannot reach the boss"; Boneraiser Minions buffing a class that "struggled against the main bosses"; I Am Legion timers ("if you get a garbage start you just lose"); Halls of Torment "i dont want to have to build ... specifically to kill a boss" (A1); DRG:S "the DPS check" (B2). |
| 4 | **Wasted time.** A loss, or a slog, after a long run feels like the run was thrown away. | Halls of Torment "the 30-minute tax" (A1); Survivor.io chapters "vraiment très long"; Picayune "if you don't focus on killing it then the longer it'll throw bullets at you". |
| 5 | **Endless and loops: same boss, more HP.** | Picayune Dreams' developer: "fighting the same bosses that you have already been able to defeat (just with more health now) isn't all that enticing"; a reviewer: "Bosses ... merely become harder numerically rather than mechanically." |
| 6 | **Arena changes that punish beyond the fight, or lie about collision.** | Vampire Hunters' permanent slime and buff pillars ("you have to rush these bosses, or else, your run becomes even more terrible"); Grind Survivors' barrier gaps. |
| 7 | **Single-stat checks.** A boss that is only beatable with one stat, usually movement speed. | Halls of Torment Lord of Pain (A1); Brotato elites on high danger (B1); DRG:S "keep at least +10% movement speed" (B2). |
| 8 | **Recycled content.** Repaints and borrowed attacks. | Grind Survivors; 20MTD "the first boss appears at identical locations in 2 of the 3 areas" (B1). |
| 9 | **Unexplained instant death.** | Vampire Survivors' Reaper for newcomers (A2); Hero Siege Uber Damien's one-shot laser. |

### Why players love them
Ranked in the same way:

| Rank | Praise | Examples |
|---|---|---|
| 1 | **A mode switch into learnable patterns.** The boss briefly turns the game into a dodging game with consistent, readable attacks. | Picayune Dreams (whole reputation); Halls of Torment "FFXIV style AoEs" and Lord of Pain; Death Must Die's Lady; Boneraiser's Shinobi with a sound-cued teleport. |
| 2 | **A big reward spike at the kill.** | Vampire Survivors' chest (A2); Soulstone powers (B2); Vampire Hunters boss-exclusive relics; Bounty of One's purple chest ("the 180-degree No Scope"); Spellbook Demonslayers' boss chests. |
| 3 | **A clear stage for the fight.** The horde withdraws, or a barrier forms, and the boss gets the screen. | Bounty of One ("All regular bounty hunters then retreat"); HoloCure and 20MTD (B1). |
| 4 | **Felt power growth.** Coming back and deleting a boss that once walled you. | Halls of Torment (A1). |
| 5 | **Opt-in boss density and boss modes for strong builds.** | Vampire Hunters constellations ("Bosses spawn twice as often. +100% Score"); Soulstone curses (B2); YAZS Boss Rush with leaderboards; Dracula summoning every boss. |
| 6 | **Bosses as an event that breaks the game's rules.** | Vampire Survivors' Reaper as a punchline ("the final fuck you when Death himself shows up", A2); the MicroWars principle; Boneraiser's watching Princess. |
| 7 | **Player control over timing.** | Boneraiser Minions: buying extra waves "will delay when the final boss shows up", letting players choose how strong they arrive. |


---

## Gaps

- Reddit (reddit.com and redlib mirrors) could not be fetched; Reddit views appear only via search summaries, marked secondary. No r/survivorslikes "best boss" thread could be read directly.
- No GDC talk or formal postmortem specifically on boss design in survivors-likes was found. The nearest primary developer sources are patch-note rationale (Picayune Dreams, Rogue: Genesia, Boneraiser Minions) and the MicroWars auto-battler devlog.
- HP and timing numbers were rare: found for the Vampire Queen (500T HP at A-rank, 500Sx at S-rank), Temtem: Swarm (Zizare 5,292→4,500 HP), I Am Legion boss timers, Boneraiser's Lunatic thresholds (60%/30%), YAZS's 10-minute Boss Rush clock and the Picayune boss HP formula. Not found for Bounty of One sheriffs, Vampire Hunters bosses, Survivor.io and Nordic Ashes.
- Survivor.io: no primary source for boss spawn times or the barrier rule; Yolk Heroes turned out to be a Tamagotchi-style idle RPG, not a survivors-like; Windblown is not a survivors-like; Rogue Survivors and Spellbook Demonslayers yielded no boss mechanics.
- Temtem: Swarm phase thresholds come from a low-quality guide site and are unverified.

## Sources (main)

- Steam news API: Rogue: Genesia (2067920), Vampire Hunters (2206270), Picayune Dreams (2088840), Boneraiser Minions (1944570), Bounty of One (1968730), Temtem: Swarm (2510960), Nordic Ashes (2068280), I Am Legion (3109580), Yet Another Zombie Survivors (2163330); URLs inline above.
- Steam reviews API (appreviews) for 2088840, 2067920, 2206270, 2068280, 1944570; URLs inline.
- Steam discussions: Rogue: Genesia [595143167557246497](https://steamcommunity.com/app/2067920/discussions/0/595143167557246497), [595143167557277975](https://steamcommunity.com/app/2067920/discussions/0/595143167557277975), [624417180895737619](https://steamcommunity.com/app/2067920/discussions/0/624417180895737619); Vampire Hunters [4638240322751659013](https://steamcommunity.com/app/2206270/discussions/0/4638240322751659013), [604148672905642534](https://steamcommunity.com/app/2206270/discussions/0/604148672905642534); Boneraiser [3789255198746334162](https://steamcommunity.com/app/1944570/discussions/0/3789255198746334162), [4629233379372501457](https://steamcommunity.com/app/1944570/discussions/0/4629233379372501457); I Am Legion [597394771139398521](https://steamcommunity.com/app/3109580/discussions/1/597394771139398521/); YAZS [601898034735932566](https://steamcommunity.com/app/2163330/discussions/0/601898034735932566); Hero Siege [487876474228053027](https://steamcommunity.com/app/269210/discussions/0/487876474228053027); Vampire Survivors [5501743491362402359](https://steamcommunity.com/app/1794680/discussions/0/5501743491362402359), [4634861089657535404](https://steamcommunity.com/app/1794680/discussions/0/4634861089657535404).
- Reviews: [Halicor on Picayune Dreams](https://steamcommunity.com/profiles/76561198037951083/recommended/2088840/); [GameGrin, Bounty of One](https://www.gamegrin.com/reviews/bounty-of-one-review/); [Thumb Culture, Vampire Hunters](https://www.thumbculture.co.uk/vampire-hunters-1-0-release-pc-review); [Grind Survivors top reviews](https://steamcommunity.com/app/3816930/reviews/?browsefilter=toprated); [Vaporlens, Picayune](https://vaporlens.app/app/2088840/picayune_dreams.md); [Vaporlens, Nordic Ashes](https://vaporlens.app/app/2068280/nordic_ashes_survivors_of_ragnarok.md); [ResetEra Halls of Torment thread](https://www.resetera.com/threads/halls-of-torment-looks-like-it-could-be-good-competition-for-vampire-survivors.796848/).
- Design: [MicroWars, "Designing bosses for an auto-battler"](https://hdd42.itch.io/microwars/devlog/1493822/designing-bosses-for-an-auto-battler).

## Verification

Adversarial check, 3 Oct 2026. Sources re-fetched: the Steam news API (count=100), the Steam threads and the review and devlog pages cited.

1. **Picayune Dreams Contamination (20 Feb 2025): bosses dim weapons, plus a Demon teleport indicator.** CONFIRMED. Both lines are in "Picayune Dreams: Contamination" (2025-02-20). The feature was first announced in "We need your HELP! + Update News!!" (31 Aug 2024).
2. **Picayune boss HP formula and the developer's "isn't all that enticing" quote.** PARTLY RIGHT. The wording is exact, but both dates in §3 are wrong.
   - The formula line is from patch **1.1.0.14, dated 21 Mar 2025**, not "Jan 2025".
   - The looping quote is from **"Progress on the next update!" (13 May 2024)**, not a "one-year post (24 Nov 2024)". The one-year post is "365 Days" (4 Dec 2024), and it does not contain the quote.
   - Source: https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2088840&count=100&maxlength=0&format=json
3. **Vampire Queen: 30K damage / 500T HP at A-rank; 1B damage / 500Sx HP at S-rank.** CONFIRMED, word for word, in "Dev Blog February 2026" (26 Feb 2026).
4. **Void Primordial bleed of 0.01% and a 30-hour kill at 1 FPS.** PARTLY RIGHT.
   - The "0.01%" comes from a player (Orgrider) in the thread. The official patch note in Update 1.0.1 (18 Mar 2025) says "Void primordial now take **0.1%** of damage inflicted to the shields". Cite the patch note and use 0.1%.
   - The OP was at 0.005 HP after about **18 hours**, not after 30+. At 30+ hours they posted a screenshot. The thread does not say the boss died; the OP stopped the run and sent the save to the developer.
   - The OP's slow HP loss fits Hotfix 1.0.0.a (8 Mar 2025), which says the boss's "max health over time" decays. It is not only the shield bleed.
   - The "TV show" summoner (Razunter) is a different player.
   - Sources: https://steamcommunity.com/app/2067920/discussions/0/624417180895737619 and https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2067920&count=100&maxlength=0&format=json
5. **Bounty of One: a Sheriff banner, the hunters retreat, a purple chest.** CONFIRMED by GameGrin. One wording note: the review says "special items like the 180-degree No Scope". It does not say "exclusive".
6. **Bounty of One: "Enemies's life improves by 25/50/75/100% when you kill a sheriff".** CONFIRMED as quoted from "Dev talk: The last steps" (14 Jul 2023), a pre-release preview. The Full Release post (8 Sep 2023) describes a shipped pact as "Enemies' life increases by 150% every time you kill a sheriff", so the final values may differ from the preview.
7. **Vampire Hunters Pavo and Boötes modifiers.** CONFIRMED, word for word, in "Free Major Content Update is LIVE!" (14 Aug 2025).
8. **Vampire Hunters venting quote.** CONFIRMED, word for word. Thread by V'ehxness, 28 Nov 2024.
9. **I Am Legion: boss timers extended after "real HP sponge" complaints.** PARTLY RIGHT.
   - The numbers are correct (3:30→4:00 and 3:00→4:00).
   - The date is wrong. The patch is "Thank you and new version update is now live" (**8 Mar 2025**, the day after launch), not "1.0.2a (25 Feb 2025)" as §7 says.
   - The order of events is backwards. The "Bosses are real HP sponge" thread was posted on 8 Mar 2025, the same day as the patch and apparently after it. The thread's OP cites the extra time as proof the bosses had too much HP. The thread therefore cannot show that the extension was a response to it.
   - Sources: https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=3109580&count=40&maxlength=0&format=json and https://steamcommunity.com/app/3109580/discussions/1/597394771139398521/
10. **Boneraiser Minions: Lunatic orbs at 60%/30% HP; Shinobi teleport sound cue.** PARTLY RIGHT.
    - Both come from one player (Skillo). The thresholds are hedged in the original: "(60% hp and 30% hp, something like that)".
    - This is a player's estimate, not developer data. It should not be listed among the "hard numbers" in the Gaps section.
11. **Temtem: Swarm 1.0 changes to Zizare and Galios.** CONFIRMED in "Temtem: Swarm - Patch 1.0" (2 Apr 2026).
12. **MicroWars devlog quote.** CONFIRMED, word for word, on the hdd42 itch.io devlog.

Other claims checked:
- **§1 heading, Rogue: Genesia's "S-rank 'Worlds Ascension' update March 2025".** WRONG. "Major Update 1.1.0 - Worlds Ascension" shipped on **13 Mar 2026**; it was previewed in the Feb 2026 dev blog. March 2025 is the 1.0 launch.
- **Vampire Hunters 1.0 on 30 Oct 2024; Slayme can be removed from the boss pool.** CONFIRMED by the news posts of 30 Oct 2024 and 14 Aug 2025.
