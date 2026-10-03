> Research notes for `docs/bosses/`, kept as written. Where the **Verification** section at the end corrects a claim, the correction stands; `RESEARCH.md` uses the corrected version.

# A1 — Halls of Torment: bosses, Lords and elites

Strand: Halls of Torment (Chasing Carrots; Prelude March 2023, Early Access 24 May 2023, 1.0 on 24 Sep 2024, The Boglands DLC 28 Oct 2025, The Lost Archives DLC announced for 22 Oct 2026). Sources: the game's Steam news feed (all items Jan 2023–Oct 2026), the community Fandom wiki (via MediaWiki API, incl. its data modules), and about 50 Steam discussion threads. Reddit, wiki.gg and Prima/PC Invasion guides were blocked to fetching.

Abbreviation: "News" = the game's Steam announcement feed, cited by item URL (downloaded copy in `raw/hot_news.txt`).

## Lessons (summary)

1. HoT runs a three-tier threat ladder with colour-coded outlines (elite blue, boss red, Agony champion yellow) and a distinct reward per tier: elites give an ability draft, bosses a 3-item equipment chest, Lords a meta currency and the next difficulty mode.
2. Mid-run bosses (at 6, 14 and 22 minutes elapsed on Hall I) are the progression gates. The next hall unlocks from a mid-run boss, never from the Lord, so new players move on without beating the hardest fight.
3. The Lord at 30:00 is the mastery check. Players accept it as a long-term goal, but they resent it when it is a long, low-variety HP sponge, because it comes after 30 minutes of play.
4. A hard death timer (the Lord of Pain's 40-second curse) was the most hated mechanic in Early Access. It was replaced within weeks by Lords that "get stronger over time", which turns a binary DPS check into a soft one.
5. Every hall hides an optional "Lord Hex" (secret) in the arena. Each one halves HP, disarms adds, removes invulnerability, simplifies patterns or adds a turret. This gives weak builds a route to victory through knowledge rather than grinding.
6. Boss adds that soaked auto-aim and projectiles (the Lord of Regret's orbs) produced the angriest feedback. The fix was to make them untargetable, plus a hex that makes them harmless.
7. Horde-boss fairness checklist from the Frozen Depths patch: no off-screen triggers, slower and sparser bullets, smaller damage zones, larger hurtboxes. Also: player effects drawn under enemy projectiles, an opacity slider, and sound cues on lunges.
8. Power spread is accepted, not capped. The difficulty for strong players moved into opt-in layers: the Agony clock, Torment artifacts such as three Lords at once or "bosses gain abilities", and kill-count or player-triggered Lords that turn power into a shorter night.
9. Victory is a pickup: the Lord drops a crystal, collecting it ends the run, and the well teleports to the player. In the endless Vault the run continues until the player chooses to collect.

## 1. Developer-stated structure (from Steam news)

### 1.1 The three-tier threat ladder: elite, boss, Lord

- Dev Journal #3 (14 Feb 2023) lays out the run: "In the main stages time ticks down from 30 minutes to your certain doom ... Among those hordes you will encounter elite enemies and bosses. Elite enemies are stronger versions of regular enemies, highlighted with glowing outlines. Defeating them will reward you with abilities ... But above the Elites are the Bosses. They are the true hazards ... Not only do they have significantly more health, they also have unique attack patterns that require good evasion skills on your part, while monsters keep swarming you! Defeating bosses will reward you with a selection of equipment that can be recovered later on and reused in all future runs." https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5036749277248077201
- Colour coding was set in the playtest of 17 Feb 2023: "Elites now have a blue outline while bosses have red outlines"; the same patch "Increased speed of Elites and Boss Monsters". https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5059268099240713442
- Early bug fix (10 Feb 2023): "The final boss should now always appear when the time hits 0" — i.e. the Lord is tied to the countdown reaching zero. https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5036749277233326522
- Reward split, therefore: elites = abilities (in-run power); bosses = a chest of equipment (meta-progression via the well); Lord = stage clear, unlocks, later Torment Shards and (in Agony) Artifacts.

### 1.2 Bosses as the progression gate

Every boss kill is wired to a quest, and the quests are the unlock system. Data below is from the community wiki's quest module (Module:QuestData, which mirrors the in-game quest boards) https://halls-of-torment.fandom.com/wiki/Module:QuestData and the patch notes.

| Hall | Boss / Lord | Quest reward on first kill |
|---|---|---|
| Haunted Caverns | Imp Chieftain | Stage: Ember Grounds |
| Haunted Caverns | Skeleton Lord | Item: Necromancer's Clutch |
| Haunted Caverns | Lich | Character: Cleric |
| Haunted Caverns | Lord of Pain | Haunted Caverns: Agony Mode |
| Ember Grounds | Flamedancer | Item: Demonic Bond |
| Ember Grounds | Wraith Warlord | Stage: Forgotten Viaduct |
| Ember Grounds | Wyrm Queen | Character: Warlock |
| Ember Grounds | Lord of Regret | Ember Grounds: Agony Mode |
| Forgotten Viaduct | Wraith Horseman | Character: Shield Maiden |
| Forgotten Viaduct | Frost Knight | Stage: Frozen Depths |
| Forgotten Viaduct | Hydra | Viaduct starting ability |
| Forgotten Viaduct | Lord of Despair | Viaduct: Agony Mode |
| Frozen Depths | Basilisk | Character: Beast Huntress |
| Frozen Depths | Twisted Construct | Stage: Chambers of Dissonance |
| Frozen Depths | Elder Giant | Character: Norseman |
| Frozen Depths | Lord of Hate | Frozen Depths: Agony Mode |
| Chambers of Dissonance | Void Caller | Shrine of Torment (Agony/Torment end-game) |
| Chambers of Dissonance | The Village | 1,000 gold |
| Chambers of Dissonance | Twisted Knight | 1,000 gold + start ability |
| Chambers of Dissonance | Lord of Discord | Chambers: Agony Mode |
| The Vault | Lord of Greed ("The Penny Dropped") | More Artifacts / post-game |
| Boglands (DLC) | Bog Serpent | Golem upgrade: Earthen Trails |
| Boglands (DLC) | Blightfiend | Additional skill scroll |
| Boglands (DLC) | Lord of Blight | Boglands: Agony Mode |

Cumulative kill quests sit on top: "Survivor I" (kill 1 Lord) gives the Revives blessing; "Boss Slayer I/II/III" ask for 10/40/100 boss kills; "Survivor II/III" 10/50 Lords https://halls-of-torment.fandom.com/wiki/Module:QuestData. Note the design consequence: the *next stage* is always unlocked by a mid-run boss (Imp Chieftain at 6:00 elapsed, Wraith Warlord, Frost Knight, Twisted Construct), not by the Lord. The patch notes confirm this repeatedly: "Ember Grounds now unlock by defeating the Imp Chieftain boss" (3 Mar 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5070528176566335986; "Forgotten Viaduct can be unlocked by defeating the 2nd boss on Ember Grounds" (16 May 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6557848386959232761; Frozen Depths "can be unlocked by beating the Frost Knight on the Forgotten Viaduct" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5124584686261074502; Chambers "unlocked by defeating the Twisted Construct in Frozen Depths" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5589599109282862901. The developers explained why: "Keep in mind at which point Frozen Depths get unlocked. You can enter the stage after defeating the second boss of the Forgotten Viaduct ... we need to make sure that players who follow a natural progression ... don't hit a brick wall." (7 Sep 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5159491482909241076. So a mid-run boss is a *gate that tests whether your account is strong enough to see the next hall*, while the Lord is the hall's completion and difficulty-mode key.

### 1.3 Reward and drop table by tier

From the wiki's Pickup page https://halls-of-torment.fandom.com/wiki/Pickup and Champion page https://halls-of-torment.fandom.com/wiki/Champion:

| Source | Drop | What the player does with it |
|---|---|---|
| Elite (blue outline) | Scroll of Mastery: new ability or ability upgrade "out of 3 options"; sometimes a Bottle Chest (1 potion bottle, or an equipment item if none available) | In-run power spike |
| Boss (red outline) | Chest: "Contains 3 Equipment Items. Only 1 can be picked." After picking, the hero gets "0.5s of invincibility" | Equip now; can send one item home via the Well for permanent unlock |
| Champion (yellow outline, Agony/Torment only) | Rolled from a pool: Champion Chest (2 Uncommon/Rare items, pick 1) 20% rising 3% per TR+AR to 50%; Scroll of Mastery 30%→60%; Extra Bucket 5%→20% (max 2 per run); Tome of Mastery at TR+AR ≥ 5; gold bags | Loot pinata on a timer |
| Lord | Torment Shard(s): at least 1, up to 4 depending on Torment Rank | Permanent stat upgrades at the Scriptor |
| Lord in Agony | An Artifact (difficulty modifier) | Unlocks more of the end-game |

The 0.5 s invincibility after choosing from a boss chest is a small but deliberate readability fix: the game pauses for the choice, and the player is not punished for the frame they return to the horde (wiki, Pickup page, above).

The end of a stage: the Lord drops a purple crystal (the Torment Shard) and, per the wiki's Lord of Pain page, "As soon as his 2nd health bar reaches 0 and you pick up his loot, you are victorious" https://halls-of-torment.fandom.com/wiki/Lord_of_Pain. Before 1.0 players asked what the crystal was for; the answer was that picking it up ends the run and lets you use the well https://steamcommunity.com/app/2218750/discussions/0/3803902828475073682/. At 1.0 the developers made "The well ... teleport close to the player after defeating the lord of a stage" so the victory lap does not require a walk across a map still crawling with enemies https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6341720536520860655, and later did the same for the Archaeologist's shrine ("Shrine of Archeologists will now be teleported to the player like the well after defeating a lord", 6 Dec 2024) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1785321795635148. The developers retroactively gave the crystal a purpose: "Torment Shards? Yes, you probably already have a handful of them lying around. Never wondered about those fancy crystals the lords are dropping? ;)" (29 Aug 2024) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6240387642453550199.

Whether the horde keeps coming once the Lord is out: the artifact "Torn Stage Curtain" reads "Enemies will keep spawning after the Lord appears" https://halls-of-torment.fandom.com/wiki/Module:ArtifactData, which implies that by default the spawn stream stops (or is greatly reduced) when the Lord arrives — I could not find an explicit developer statement, so treat this as inference. In Agony "Enemies stop spawning, after you defeated the prime Lord" (player, Jan 2026) https://steamcommunity.com/app/2218750/discussions/0/693123995207396277/. Either way the Lord fight is mostly a duel against leftover mobs plus the Lord's own summons, not a fight inside the full horde.

## 2. Stage-by-stage: every boss, elite and Lord

Times below are *time remaining* on the 30:00 countdown, from the community wiki wave tables (each stage page). Bosses have no numeric HP published anywhere I could find; the wiki does not list it and the developers never posted it. Where a player has quoted a number it is labelled.

### 2.1 Haunted Caverns (Hall I) — Lord of Pain

Source for the table: https://halls-of-torment.fandom.com/wiki/Haunted_Caverns

| Time left | Elapsed | Encounter | Type |
|---|---|---|---|
| 27:40 | 2:20 | Skeleton (Sturdy Elite) | elite |
| 24:00 | 6:00 | Imp Chieftain | boss — kill unlocks Ember Grounds |
| 19:45 | 10:15 | Skeleton (Shield Elite) | elite |
| 16:00 | 14:00 | Skeleton Lord | boss — unlocks Necromancer's Clutch |
| 11:40 | 18:20 | Skeleton (Mage Elite) | elite |
| 08:00 | 22:00 | Lich | boss — unlocks Cleric |
| 00:00 | 30:00 | Lord of Pain | Lord |

Rhythm: elite, boss, elite, boss, elite, boss, Lord — roughly one notable spawn every 4 minutes, with bosses at a fixed 8-minute cadence (6, 14, 22 elapsed). Dev Journal #3 says the stage "has a slow start. It's mostly dominated by skeletons and you'll encounter mainly skeleton themed bosses" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5036749277248077201. Champion and secret mechanics added later; Hall Strength (champion HP scaling) runs 500 → 19,000 across the run https://halls-of-torment.fandom.com/wiki/Hall.

**Imp Chieftain (6:00 elapsed).** The first real check: a beginner guide notes it arrives "at the 24-minute mark, giving you six minutes of prep time to collect the Golden Scroll in the level" (secondary: search-engine summary of a PC Invasion/Prima guide; page itself blocked) https://pcinvasion.com/?p=373537. Its kill is the gate to the second hall, so for a new player it is the *de facto* first boss of the game. Attack details: not found.

**Skeleton Lord (14:00 elapsed) and Lich (22:00 elapsed).** Names and rewards confirmed (QuestData, above). The Lich "only appears when you're down to the last eight minutes" (secondary: search-engine summary; the Prima/PC Invasion page was blocked, so the exact source page is unconfirmed) https://primagames.com/?p=144909. Attack details: not found.

**Lord of Pain (30:00).** The most-discussed boss in the game.
- Structure: "He has two stages, starting off mounted. Once his first health bar is drained, he dismounts and fights on foot." https://halls-of-torment.fandom.com/wiki/Lord_of_Pain
- Moveset reported by players: fireball "spam" and a "spiral projectile magic"; he "dashes 3x in row and your character may be too slow to keep a distance" https://steamcommunity.com/app/2218750/discussions/0/3803902423389575487/ ; "Half way through phase one, its so fast you can't escape him" https://steamcommunity.com/app/2218750/discussions/0/3801651208779515558/. A player's tip on the spiral: "they are never in the same place twice in 1 attack, so if you dodge one you can move where it was and be fine" (same thread 3803902423389575487).
- The **Curse Bolt / death timer** (EA launch, May–June 2023): "Curse kills the player after 40 seconds, and the player can only continue fighting with Revivals." https://halls-of-torment.fandom.com/wiki/Curse. A patch on 6 Apr 2023 made him cast "homing projectiles with the death curse" and admitted "Originally, it was not intended to beat this encounter by reviving" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5121196841288022894. A player who hit it described it: "His patterns were easy enough to dodge - except for one homing skull with a countdown ... Then the countdown hit 0. Instant kill ... The final boss is a 40-second dps check." https://steamcommunity.com/app/2218750/discussions/0/3836550304890643661/
- The developer's explanation (community manager, Steam, 6 Jun 2023): "Originally it was meant that you have 6 seconds before you die by the timer and only in edge cases to be beatable without this mechanic [the Token]. We did not manage to add this mechanic for the EA launch, so we extended the time of the timer ... we wanted to give freedom in how you beat the game, having only one valid way of finishing something is not it and therefore we swapped the mechanic to the boss getting gradually faster over time instead of being instant death ... The boss itself without the mechanic did not get easier, contrary, the boss should be even a bit harder now." https://steamcommunity.com/app/2218750/discussions/0/3814032755145903075/
- The rework (9 Jun 2023): "Death timer has been removed. The Lord of Pain will now get stronger over time. Lord of Pain HP have been reduced a bit. Adding a mechanic to ease the Lord of Pain fight." and "we added a mechanic where the lord gets harder as time passes. Additionally, there is also a hidden mechanic in the Haunted Caverns to help you with that fight!" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5129083846342681607
- The **secret (Lord Hex)**: two blood trails lead from the Bloodstained Pages to two Shrines of Pain (one large circle, one with three small circles); kill enough enemies inside each circle (players report 100) to get half of the Protective Pendant each. The completed pendant "fires a single projectile towards the first and second form of the Lord of Pain, which counts as a guaranteed crit" and "deals final damage equal of 50% of the Lord's health, regardless of Agony or Torment Rank"; "Fragile stacks increase the damage dealt by the projectile" https://halls-of-torment.fandom.com/wiki/Haunted_Caverns. Players have used Fragile stacking to one-shot both phases: "If you manage to throw enough to double the damage taken by the boss in the few seconds for the item to strike, you can just OS both phases." https://steamcommunity.com/app/2218750/discussions/0/4344355442320728556/
- A known AI bug (July 2023): "in the second phase he just stopped attacking and walked forward while I melted him ... Happens about 30% HP left" https://steamcommunity.com/app/2218750/discussions/0/3803902828477690255/

### 2.2 Ember Grounds (Hall II) — Lord of Regret

Unlocked by the Imp Chieftain. "Scorched souls and flame demons ... it starts out faster into the action" (Dev Journal #3, link above). Source for the table: https://halls-of-torment.fandom.com/wiki/Ember_Grounds

| Time left | Elapsed | Encounter | Type |
|---|---|---|---|
| 23:50 | 6:10 | Flamedancer | boss |
| 21:50 | 8:10 | Slime (Magma Elite) | elite |
| 15:50 | 14:10 | Slime (Magma Elite) | elite |
| 13:50 | 16:10 | Wraith Warlord | boss — unlocks Forgotten Viaduct |
| 05:50 | 24:10 | Wyrm Queen | boss — unlocks Warlock |
| 00:00 | 30:00 | Lord of Regret | Lord |

- **Flamedancer**: added as "New boss: 'FlameDancer' in Ember Grounds" in the 3 Mar 2023 playtest https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5070528176566335986, and "The Flamedancer, first boss of Ember Grounds, got two new attack patterns" on 23 Mar 2023 https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5125698536879963118. Pattern details: not found.
- Early on, "Some bosses are substitutes for now and are slightly different versions from the first stage" (9 Mar 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5070528810292760847 — re-skinned bosses were used as placeholders while the stage was built.
- **Lord of Regret** (wiki stub, player-written): "Summons brain looking 'mines' that count as enemies"; "Shoots a line of circles on the ground that eventually fire will come up from the ground"; "Throws Light-Sabers that spin around randomly"; "HAS A MASSIVE HEALTH BAR!!!" https://halls-of-torment.fandom.com/wiki/Lord_of_Regret. The orbs ("bubbles", "meatballs", "truffles") are the defining mechanic and the main complaint. Players explain: "the meatballs do not damage you themselves. Walking into them causes a time delayed explosion, so you can run through them to set them off and clear the field" https://steamcommunity.com/app/2218750/discussions/0/6643422659549887504/. Before the fix the orbs soaked projectiles and auto-aim: "All of the bubbles soak up all of your damage. I just spent literally 20 minutes chipping away at him" (same thread); "a boss getting stuck in his own attack? ... They are very slow and the boss can't walk through them so you quickly get a huge clump of them with the boss pretty much useless in the center" https://steamcommunity.com/app/2218750/discussions/0/6643422659557406944/; "Even once he's dead the orbs STILL don't disappear, which forced me to rush and grab it before it was lost forever to the orbs" https://steamcommunity.com/app/2218750/discussions/0/3836550304886542271/.
- Fix announced 17 Jul 2023: "The Lords of Ember Grounds and the Viaduct will be changed to have less health and scale in difficulty as time passes, just as the Lord of Pain in the first level. The additional projectiles and indestructible guards will no longer be valid targets for abilities and auto-aim." https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6079346804886487570 — shipped 31 Aug 2023 as "All final stage bosses have lower health but they increase in difficulty over time" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355657088929.
- **Secret**: follow red-handed skeleton statues to the Ember Altar, then the gleam of the Ember Eye to a **Cyclops** mini-boss; killing it gives the Cracked Eye, after which "the truffles (bombs from the Lord of Regret) no longer inflict damage" https://halls-of-torment.fandom.com/wiki/Ember_Grounds. Note the hex is a *hidden mini-boss fight* that disarms the Lord's add mechanic.
- 2026 bug fix shows the internals: "Fixed the mining attack incorrectly using a hardcoded bomb count instead of the intended value. His wave and delta attacks will also now properly abort if he dies mid-attack." (10 Mar 2026) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1826362059932521 — so his kit is named internally as a mining (bomb) attack, a wave attack and a "delta" attack.

### 2.3 Forgotten Viaduct (Hall III) — Lord of Despair

Unlocked by the Wraith Warlord. "the first stage in which we want to try out different layouts and enemy behaviours. Enemy behaviours are tailored to the stage geometry." (16 May 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6557848386959232761. Source for the table: https://halls-of-torment.fandom.com/wiki/Forgotten_Viaduct — this stage's table also gives an "end" time, i.e. how long the wave window lasts.

| Time left (start–end) | Encounter | Type |
|---|---|---|
| 27:40–26:20 | Wraith Guard (Elite) | elite |
| 24:00–22:30 | Wraith Horseman | boss — unlocks Shield Maiden |
| 21:40–21:20 | Gargoyle (Elite) | elite |
| 19:45–18:20 | Wraith Guard (Elite) | elite |
| 16:00–14:30 | Frost Knight | boss — unlocks Frozen Depths |
| 11:40–10:20 | Wraith Arbalist (Elite) | elite |
| 08:00–06:30 | Hydra | boss — unlocks a starting ability |
| 05:50–05:40 | Gargoyle (Elite) | elite |
| 05:30–05:20 | Wraith Arbalist (Elite) | elite |
| 00:00 | Lord of Despair | Lord |

Boss windows on this stage are 1.5 minutes wide (24:00–22:30, 16:00–14:30, 08:00–06:30). "Elites on Viaduct have a bit less health, but now there are 6 of them - more abilities!" (25 May 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5151600576587852750.

- **Marching Ghosts** — a stage-wide timer made visible: they "spawn at the start of the round in detachments of 56 (4 rows of 14), at the southwest and northeast corners of the map respectively. From there they march towards the middle of the map, meeting in the middle right before the timer elapses completely." 10,000 HP, 110 contact damage, damage factor 0.1%. "the Marching Ghosts summoned by the Lord of Despair cannot be killed." https://halls-of-torment.fandom.com/wiki/Marching_Ghost. The two armies converging on the centre are a diegetic countdown to the Lord.
- **Possessed Effigies** — Weeping-Angel statues that "doesn't move when looked at by the character", damage factor 0.1%, "will die after 21 hits", block piercing projectiles https://halls-of-torment.fandom.com/wiki/Possessed_Effigy.
- **Lord of Despair**: wraith/lich on the theme of the dead army; "Wraith lance attacks will also play a sound now (Lord of Despair and Wraith Horseman)" (beta 20 Jun 2023, released 27 Jun 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5124581515272412296. He summons unkillable Marching Ghosts and uses illusions and invincibility phases (from the secret's lore text and effect). A player who loved him: "My favorite so far is the Lord of Despair. What a fantastic boss, so beautifully designed ... his obnoxious ghost minions (really too many!) and that Hall 'theme' reminded me of The Dead Army ... The dead knight in the horse was also a fantastic mini-boss" https://steamcommunity.com/app/2218750/discussions/0/6643422659550501285/. A critic: "Stage 3 should get some unique movement kind of thing imo, like switching places with its ghosts" https://steamcommunity.com/app/2218750/discussions/0/3803903461249040332/.
- **Secret**: a raven circles the Torn Pages; approach it and it flies on (granting "Raven Wings" +40% movement speed); follow it to a Sarcophagus with "30 000 Base Health, with a Damage Factor of 50%"; inside is the Sentinel Orb: "the Lord of Despair will not have any invincibility phases" https://halls-of-torment.fandom.com/wiki/Forgotten_Viaduct.

### 2.4 Frozen Depths (Hall IV) — Lord of Hate

Unlocked by the Frost Knight. A cave system: "The cave structure will not only limit your movement, it will also enable you to plan ahead on how and where to engage enemies." (17 Jul 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6079346804886487570. Release notes: "New unknown enemies await with 3 unique bosses and a new lord." https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355657088929. Wave table marked "work in progress" on the wiki https://halls-of-torment.fandom.com/wiki/Frozen_Depths:

| Time left | Encounter | Type |
|---|---|---|
| 27:40 | Ice Wisp | elite |
| 23:30 | Frost Ghoul | elite |
| 21:40 | Basilisk | boss — unlocks Beast Huntress |
| 20:00 | Elite Frost Crawler | elite |
| 16:00 / 15:30 | Polar Beast (×2) | elite |
| 11:55 | Twisted Construct | boss — unlocks Chambers of Dissonance |
| 7:00 | Ice Prism | elite |
| 6:00 | Elder Giant | boss — unlocks Norseman |
| 0:00 | Lord of Hate | Lord |

- Launch backlash and the boss fix (5 Sep 2023): "The most common complaint was the increased difficulty, especially in the new stage ... Frozen Depth Bosses: reduced trigger distance for ranged attacks to avoid player getting off-screened; made projectile based attack patterns of bosses less frustrating; slower movement; less dense patterns; smaller damage areas; increased size of hit areas (the ones that receive damage, not the ones that deal damage)" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355676063710. This is the single best checklist in the whole news feed for making a horde-boss fair.
- Readability follow-up (7 Sep 2023): "Player's Frost Avalanche ability effects have been moved below characters sprites and enemy projectiles. Enemies' frost avalanche effects have a higher contrast and stand out more against the frozen depth background." https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5159491482909241076. And in Dec 2025: "Ice Colomns of Champions and other enemies get now properly telegraphed." https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1818118366173035
- **Lord of Hate** attacks reported by a guide (secondary, search summary only): a "Scatter Shot Strike" of small circles "spreading gradually from Lord of Hate's position", a "Pulsing Circular Strike" of rings "between which you can stand safely", and a "Linear 6-way Strike" https://primagames.com/?p=185809. The wiki's secret text adds a **spin attack** and a **pounce attack**. Players call him "Spin-to-Win Lord": "he is extremely BS with BS hitboxes and ability spam ... when he does his spinning rush attack, walk directly towards him and strafe to the side. He will soar past you due to momentum" https://steamcommunity.com/app/2218750/discussions/0/836123461384574322/; another kited him for "more than 20 mn ... I couldn't dodge his dashes and those weird pink flame attacks, I had to find a small elevation on the map" https://steamcommunity.com/app/2218750/discussions/0/715612499312958532/.
- **Secret**: four glowing orbs float away as you approach and lead to a **Frost Ghoul Lieutenant** mini-boss; it drops the Hating Heart: "the Lord of Hate's attack patterns become simpler ... will perform the spin attack more often than the pounce attack ... After performing the spin attack, the Lord of Hate receives a debuff to defense. The Hating Heart icon pulses during this time." https://halls-of-torment.fandom.com/wiki/Frozen_Depths. This is the only hex that *creates a punish window and signals it in the HUD*.

### 2.5 Chambers of Dissonance (Hall V) — Lord of Discord

Unlocked by the Twisted Construct; "three new bosses and a final Lord boss"; "Players that have maxed out their builds won't have any trouble unless maybe playing with Agony turned on" (13 Feb 2024) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5589599109282862901. Wave data on the wiki is incomplete https://halls-of-torment.fandom.com/wiki/Chambers_of_Dissonance:

| Time left | Encounter | Notes |
|---|---|---|
| 20:00 | Void Caller | boss — kill unlocks the Shrine of Torment (the end-game difficulty system) |
| 10:00 | The Village | boss — 1,000 gold |
| not found | Twisted Knight | boss — 1,000 gold + start ability; a player found it harder than the Lord: "It took me a few attempts to kill all the bosses on level 5 whereas I beat the final boss 5 times" https://steamcommunity.com/app/2218750/discussions/0/6597293740384347264/ |
| 00:00 | Lord of Discord | Lord |

- Lord of Discord HP, player-reported only: "the final boss has 400,000 base HP at 0 difficulty. This is scaled up based on your difficulty meter ... Assuming you hit roughly max difficulty, 5,500,000 HP." (Mar 2024; unverified) https://steamcommunity.com/app/2218750/discussions/0/4291440317148437305/. The same post describes an exploit: large-hitbox bosses get stuck on pillars and "The boss wont attack at all when you are at this range. It's a completely free kill."
- **Secret** (a light puzzle): rotate eight relays (bump to turn 90°) so a beam reaches the Dissonator Monolith; it then fires at intervals, dealing "7000 damage to the Lord of Discord, and 1000 damage to other enemies" https://halls-of-torment.fandom.com/wiki/Chambers_of_Dissonance. Quest: "Deal 100 000 damage with the Dissonator Monolith" (QuestData).
- "Lord hexes ... You probably already have encountered one for the Lord of Pain in the Haunted Caverns. Now we've added one in each level ... Lords have new and improved sounds" (11 Mar 2024) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5679673637666927551.

### 2.6 The Vault (final hall) — Lord of Greed

Release notes, 24 Sep 2024 https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6341720536520860655:
- "unlocked by purchasing 30 items from the Wellkeeper. To enter the vault you'll need to spend some coins. The price is (mostly) up to you. The more you pay the more modifiers are added to the Vault. They may be positive, negative, or… ambiguous. Every 4th modifier adds a Torment Shard to the final drop."
- "The Vault lord does not spawn automatically after 30 minutes but requires you to activate him. A Vault run lasts for as long as the lord is alive. After the 30 minute mark the monsters' strength continuously rises."
- Wiki detail: the Lord sits on a throne "sealed by 4 Twisted Pillars", each linked to a Pylon of "50 000 Base Health"; destroying all four unseals him. Torment Level rises by 1 at 4, 8, 12, 16 and 20 minutes; each adds 0.33 base defence. No well, no Agony, no artifacts; gold only from the Alms fallback trait https://halls-of-torment.fandom.com/wiki/The_Vault. Tribute modifiers include "+20% Boss Health" and "+30% Boss Health" https://halls-of-torment.fandom.com/wiki/Module:VaultModifierData.
- Speed challenge: "Vault Speedster" — beat the Lord of Greed in under 9 minutes (secondary, TrueAchievements via search) https://www.trueachievements.com/a595461/vault-speedster-achievement.
- Endless tail: "With this change we can easily go up to Torment Level 40+ and the Vault is quite some time longer after the current 95 minutes after which it starts breaking." (8 Oct 2024) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6350729003512729329. Players hit the soft wall: "Even if you can reliably make it past 60 minutes, your ability to kill anything goes down and down until nothing is dying anymore" https://steamcommunity.com/app/2218750/discussions/0/4703539869281972918/. A tip: "You can farm endlessly in the Vault, as long as you dont pick up the Torment Shards dropped by the Lord of Greed" https://steamcommunity.com/app/2218750/discussions/0/693123995207396277/ — i.e. the run ends when the reward is collected, not when the boss dies.
- Beating him unlocks the post-game and the outro cinematic; the Bard update later greets you "after you've seen the outro cutscene" (28 Oct 2025) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1814309641609664.
- Bug: "The Lord of Greed and Scriptor could not be damaged by projectiles" (12 Feb 2025) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1791482680850412.

### 2.7 The Boglands (DLC, Oct 2025) — Lord of Blight

- "Keep decimating their numbers to force the Lord of Blight to rise from their hiding spot. How fast can you conquer the Boglands? ... Instead of having a fixed time, the Lord triggers after defeating 25 000 Enemies." https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1814309641609664. The wiki and players now say 20,000 ("the Lord of Blight triggers upon 20 000 kills" https://halls-of-torment.fandom.com/wiki/Boglands; "He spawns after 20.000 kills" https://steamcommunity.com/app/2218750/discussions/0/735909930464360603/) — presumably a post-launch change; patch note not found.
- Lord of Blight is mounted at first ("I had just knocked the bog guy off his mount and had him to about 50%" https://steamcommunity.com/app/2218750/discussions/0/616556383851321497/), echoing the Lord of Pain's two-bar structure.
- Mid-bosses: Bog Serpent and Blightfiend (QuestData); spawn conditions not found.
- Secret: glowing roots lead to an **Evil Tree** with a visible "40 000 HP" health bar; killing it opens a fissure leading to the **Blight Worm**, which drops a Torment Shard https://halls-of-torment.fandom.com/wiki/Boglands. Quest: "Find and kill the Blight Worm before your final encounter with the Lord of Blight."
- Kill mode spread to all halls in 2026: "One of the main motivators for the Boglands Kill Mode was feedback about possibly shorter runs ... To unlock it, you need to finish a quest on each map, usually the first damage quest, to show that you can deal enough damage for Kill Mode not to drag on forever ... We've added UI feedback and information to make it clearer when the lord will spawn." (4 Sep 2026) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1842846814446281

### 2.8 The Lost Archives (DLC, due 22 Oct 2026)

Announced, unreleased at time of writing: "New map: the Lost Archives which unlocks when acquiring 5 or more marks of any characters. The Archives will be similarly difficult to the Boglands." https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1839041357029299. Bosses: not announced.

## 3. Scaling: how bosses cope with weak-to-absurd builds

### 3.1 Base game: no caps, but four levers

1. **Lords that escalate over time instead of a hard timer.** After the Lord of Pain rework every Lord got "lower health but they increase in difficulty over time" (31 Aug 2023, link above). This converts a binary DPS check (40-second curse) into a soft one: a weak build can still win by dodging an ever-faster Lord; a strong build never sees the escalation. The developers' stated principle: "having only one valid way of finishing something is not it" (Steam, 6 Jun 2023, link above).
2. **The Lord Hex per hall** — an optional, in-world "catch-up" that halves (Pain), disarms (Regret), removes invulnerability from (Despair), simplifies (Hate) or bombards (Discord) the Lord. It costs the player route time and attention during the 30 minutes, so it is a skill-and-knowledge alternative to grinding power. Several players say it trivialises the first Lord ("makes him very easy, almost trivial" https://steamcommunity.com/app/2218750/discussions/0/4344355442320728556/), which is the point.
3. **Slow resistance and slow floors on big enemies**: "Resistance: champion (25%), elite (50%), boss (66%), lord (80%). Limit: champion (30%), elite, boss, lord (50%)" (30 Oct 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5229301621590571094. Crowd control that trivialises trash cannot freeze a Lord in place. Elemental effects were also capped ("all elemental effects will be capped to stacks of 20", 17 Jul 2023, link above).
4. **Meta-progression is the intended answer.** The developers refused an easy mode: "There will be no 'easy mode', it's not necessary. The game becomes easier the longer you play by gaining gold, blessings new and better items and also unlocking better traits." (Steam, 6 Jun 2023, link above). And they protect over-powered builds: "We don't try to kill off OP builds, it's a single player experience anyways" (27 May 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5151600576595745659; "we do not want to get rid of 'OP' builds. We understand that having the possibility to create insanely powerful combinations is part of the fun" (14 May 2024) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5768625435399294703.

The result at the top end, from players: "With proper gear/traits and blessing i can now melt world 1 lord in 6~10 secs, world 2 in 30 secs, and world 3 in 20 secs" https://steamcommunity.com/app/2218750/discussions/0/3833171785690571532/ ; "Bosses melt in less than 30 seconds on any build on any character if you picked traits properly" https://steamcommunity.com/app/2218750/discussions/0/3801651208776706346/. At the bottom end: "Had a 50 minutes fight with the world 2 boss yesterday" (same 3833171785690571532 thread). The game accepts this 300× spread and does not cap damage on bosses.

### 3.2 Agony (hard mode, per hall, unlocked by killing that hall's Lord)

- First version (31 Aug 2023): performance-driven — "Each killed enemy increases agony, while monsters that are alive reduce agony over time ... Aside from monsters, only reviving reduces agony." https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355657088929. It rubber-banded; a player: "i read that agony decreases when bosses are alive. but even if i try to kill the bosses immediately when they spawn, it takes SO LONG that a second boss arrives meanwhile" https://steamcommunity.com/app/2218750/discussions/0/3816292540667889944/.
- 30 Oct 2023: "Agony is now generated over time instead of killing monsters. Earliest possibly Agony rank ups are every 4 minutes with Agony 5 being achievable at 20 minutes in ... a revive now decreases Agony by 1 rank ... Adding damage scaling for all stages (stronger on lower stages) -> 2.5% - 10% per Agony level" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5229301621590571094.
- Dec 2023: "Agony decay has been entirely removed ... Agony will increase by 1 level every 5 minutes ... Some of you may die, but it's a sacrifice we are willing to make" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5395938616794161700. Current wiki value: "1 Agony Rank is gained every 4m 48s (24m for 5 Ranks)", max rank 5, revive costs 20% of the meter https://halls-of-torment.fandom.com/wiki/Agony.
- Oct 2024: "Agony will add 1 Defense to each enemy per rank." https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6350729003512729329
- Champions (yellow outline) are Agony's roaming mini-bosses: base spawn every 150 s, minus 9 s per Agony rank, ×0.95 per Torment rank; "First champions do now spawn after 90 seconds to avoid clashing with regular 2nd monster wave elites" (13 Sep 2023) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5211283418277167291. Champion HP = Base Health (5,000 for most) + Hall Strength × multiplier, where Hall Strength interpolates linearly over the run from 500→19,000 (Hall I) up to 9,000→114,000 (Halls IV–Vault) and 10,000→150,000 (Boglands) https://halls-of-torment.fandom.com/wiki/Hall, https://halls-of-torment.fandom.com/wiki/Module:ChampionData. "Changed how champions scale. It should happen less often now that they have dramatic damage spikes" (1.0 notes, link above).

The Agony design history is a clean case study: a performance-linked difficulty meter that punished slow boss kills was replaced by a pure clock, because players could not see or control it.

### 3.3 Torment (artifacts) and the Lords as artifact-holders

- 1.0: "Defeating lords in Agony now grants Artifact drops"; "There are a total of 30 artifacts ... of which you can use as many as you want. Using more artifacts improves drop chances, rarity of loot, and amount of champions" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6341720536520860655. The pre-release pitch: "find the 30 artifacts that the lords hold onto in agony mode" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6240387642453550199.
- Per Torment rank (current wiki): enemy health ×1.11, defence ×1.10, damage +2%, speed +1.5%, XP +5%, champion spawn time ×0.95 https://halls-of-torment.fandom.com/wiki/Torment. History: Oct 2024 changed health from ×1.2 to ×1.12 "because ... some enemies were approaching and hit the highest HP possible in the game, causing bugs" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6350729003512729329; Oct 2025 "Health x1.11 -> x1.09, Defense x1.10 -> x1.09, Movement Speed +1.5% -> +1.0%" https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1814309641609664 (the wiki may lag this change).
- Torment Shards from Lords: guaranteed 1, then three extra rolls with probabilities TR/10, (TR−2)/18, (TR−4)/26, so 4 shards are certain at Torment Rank 30 https://halls-of-torment.fandom.com/wiki/Torment_Shard.
- Boss-specific artifacts: **Malignant Mirror** — "Three Lords appear at the end of a run, instead of a single Lord"; **Demonic Cube** — "Elites, Bosses, and Lords gain additional abilities"; **Torn Stage Curtain** — "Enemies will keep spawning after the Lord appears"; **Hastening Sands** — "-10 Minutes Run Time, +30% Spawn Rate, +20% Movement Speed (All)" https://halls-of-torment.fandom.com/wiki/Module:ArtifactData. Malignant Mirror has caused bugs where killing the bonus Lords despawns the "prime" one without loot https://steamcommunity.com/app/2218750/discussions/0/616556383851321497/ and "When multiple lords died at once, not all of them would spawn their Torment Shards" (5 Nov 2025) https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1815580768232711.

### 3.4 Time versus kills

- 30-minute clock (Halls I–V); Hastening Sands makes it 20.
- Vault: no clock; Lord unsealed by the player; enemies keep scaling after 30:00.
- Boglands: kill threshold (25,000 at launch, 20,000 now) — a strong build summons the Lord sooner, which turns power into speed rather than into a trivial fight. Kill mode is being offered for all halls in the 2026 free update, gated behind each map's first damage quest "to show that you can deal enough damage for Kill Mode not to drag on forever" (4 Sep 2026, link above).

## 4. Readability: how the fight stays legible in the horde

What the developers actually did, in order:

| Date | Change | Source |
|---|---|---|
| Feb 2023 | Outline colour by tier: elites blue, bosses red (champions later yellow) | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5059268099240713442 ; https://halls-of-torment.fandom.com/wiki/Champion |
| Mar 2023 | Ember Grounds gets its own soundtrack; boss music loops (May) | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5121196841288022894 ; https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5151600576591973606 |
| Jun 2023 | Lance attacks of Lord of Despair and Wraith Horseman get a sound cue | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5124581515272412296 |
| Jul–Aug 2023 | Lord adds (Regret's orbs, Despair's guards) removed from auto-aim and ability targeting | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6079346804886487570 |
| Sep 2023 | Frozen Depths bosses: shorter ranged trigger distance (no off-screen shots), slower, less dense patterns, smaller damage areas, bigger hurtboxes | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355676063710 |
| Sep 2023 | Opacity slider for the player's own ability effects; player Frost Avalanche drawn *below* enemy projectiles; enemy effects higher contrast | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355676063710 ; https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5159491482909241076 |
| Sep 2023 | Champion projectiles slowed "and shouldn't off-screen the player so often" | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5211283418277167291 |
| Mar 2024 | "Lords have new and improved sounds" | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5679673637666927551 |
| Mar 2024 | Hotfix "Fixing one shot kills caused by Wyrms on Ember Grounds" (enemy projectile bugs) | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/7309977427435186497 |
| Dec 2025 | Ice columns of champions "now properly telegraphed" | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1818118366173035 |
| 2026 | Kill mode UI shows "when the lord will spawn" | https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1842846814446281 |

The wide-screen caveat is telling: "When in widescreen mode: We are aware that you will see monsters popping in the middle of the screen. We do not change the gameplay/balancing to accommodate various screen ratios." (1.0 notes, link above). Encounter ranges are tuned to a fixed view.

Remaining problems, per players: "one can't almost see them at all with all this demented visual noise, and one must play multiple times to get a glimpse and appreciate their design" https://steamcommunity.com/app/2218750/discussions/0/6643422659550501285/ ; "Visual clutter makes it hard to see your cursor AND to see lord's attacks" https://steamcommunity.com/app/2218750/discussions/0/3836550304886542271/ ; a reviewer found bosses "a little generic, often oversized versions of smaller enemies, so it's all the more surprising when they break that rule", singling out the mounted horseman and the hydra https://www.thexboxhub.com/halls-of-torment-review/.

## 5. Player opinion: loved, hated, and why

| Boss | Verdict | Representative quotes |
|---|---|---|
| Lord of Pain | Most loved *and* most hated; the only Lord that "feels like a Lord" | Hate: "Even normally this boss is waaaay to overtuned ... a 10 minute fight by itself. It honestly made me hate the game" https://steamcommunity.com/app/2218750/discussions/0/4344355442320728556/ ; "if you don't pick speed and level it up you lose ... requiring it is poor design" https://steamcommunity.com/app/2218750/discussions/0/3801651208779515558/ ; on the curse: "giving the middle finger to the player?" https://steamcommunity.com/app/2218750/discussions/0/3836550304890643661/. Love: "1st boss may have tons of HP but this is what makes him an actually boss ... his speed can teach you some great things about movement ... the only Lord that feels like a Lord after so long time is till the first" (4344355442320728556); "The 1st one is both the hardest and most polished, having a more involved moveset and tied to a level-gimmick" and "It's my favorite boss of the three since it feels very bullet-hell" https://steamcommunity.com/app/2218750/discussions/0/3803903461249040332/ ; "the first boss stat-checking your build ... is a good thing. Past some point, you'll need either the ms, the dps, or some real tankyness, and that feels tense and fun" (same thread). |
| Lord of Regret | Most hated; "bullet sponge", "time sink" | "Is the Lord of Regret the worst boss in the entire history of gaming? ... In lieu of an interesting moveset, he instead had ten million friggin' HP" https://steamcommunity.com/app/2218750/discussions/0/3833172326396523543/ ; "it is an annoying 10-20 mins fight. I always stop playing this game after fighting him bcs its exhausting. Make him more interesting and dangerous." https://steamcommunity.com/app/2218750/discussions/0/3801653351441373590/ ; "he spawns, he spawns his bubbles, he dies a 3 step process that takes seconds not exactly the menacing roadblock one would like at the end of a hall" (late-game view, 4344355442320728556); "it would be so much better if the bombs could also damage the boss" https://steamcommunity.com/app/2218750/discussions/0/6643422659550501285/ |
| Lord of Despair | Liked for theme and spectacle | "My favorite so far ... fighting him felt awesome" (6643422659550501285); criticised for "little pauses make it baby mode" (3803903461249040332) |
| Lord of Hate | Divisive: hitboxes and dashes | "my least favorite boss because he is extremely BS with BS hitboxes and ability spam" https://steamcommunity.com/app/2218750/discussions/0/836123461384574322/ ; "omg I love how I micro the fight against lord of hate with archer" https://steamcommunity.com/app/2218750/discussions/0/715612499312958532/ |
| Lords 4–5 generally | "ground AoE zig-zag line attack" disliked | "The game introduces some very cool patterns that force you to adapt your trajectory everywhere in the first level, then they kinda disappear, and those two bosses just get the worst one" (3803903461249040332) |
| Bosses in general (EA, mid-2023) | "HP bags" | "they are hp bags repeating the same 4 attacks over and over ...i sometime have to pause the game, because boredom makes me lose focus" (6643422659550501285); "Lords take an unnecessary amount of time, with very few, very simple attacks" https://steamcommunity.com/app/2218750/discussions/0/3818543707180647487/ ; "Then where you tired at 30min and wanna be rewarded you need to face a bullet sponge boss" https://steamcommunity.com/app/2218750/discussions/0/3803903751088262515/ |
| Counter-view | Bosses are a long-term goal, not a per-run gate | "Losing isn't fun, and it's not meant to be fun. It's meant to trigger an impulse for you to improve" https://steamcommunity.com/app/2218750/discussions/0/3814032755154865216/ ; "skipped him, cleard map 2, cleard map 3 and killed the Lord ... came back to Lord 1 an killd him in 10 seconds. You really feel the power." (6643422659550501285); "the fact that you cant beat the boss the first time you encounter it isnt a huge deal" https://steamcommunity.com/app/2218750/discussions/0/3801651208776706346/ |

Patterns in the complaints:
- **The 30-minute tax.** The Lord arrives after half an hour of play, so a loss or a slog there is felt as wasted time ("There's no excuse for wasting this much of my time" https://steamcommunity.com/app/2218750/discussions/0/3801652295714578800/). Repeated requests for 15/20-minute runs were eventually answered with Hastening Sands and kill mode https://steamcommunity.com/app/2218750/discussions/0/4635986619924496708/.
- **Single-target damage versus horde-clear builds.** Survivors builds optimise for area clear; a high-HP single target punishes them. "i dont want to have to build and play specifically to kill a boss, i want to have fun with different things and most options in the game mean the boss takes ages" https://steamcommunity.com/app/2218750/discussions/0/3803903461255991004/. The community answer is debuffs (Transfixion, Radiant Aura, Fragile) and crit stacking (same thread).
- **Adds that block damage.** The worst-rated mechanic in the game was the Lord of Regret's orbs absorbing projectiles and auto-aim; the developers' fix was to make them untargetable and to give a hex that makes them harmless.
- **Move-speed checks.** Lord of Pain's triple dash and enrage speed force a movement stat; some see this as a fair "stat check", others as removing build choice.
- **Late game: bosses become trivial.** Once meta-progression is maxed, even Agony Lords die in seconds, which the developers addressed with Torment artifacts (Demonic Cube, Malignant Mirror) rather than by inflating boss HP.

## 6. Lessons for Survivor Unchained

1. **Use three visibly distinct tiers with distinct rewards.** HoT's blue elite → red boss → Lord ladder pays out ability draft → equipment choice → meta currency/unlock. Each tier has a clear purpose in the run and in the account.
2. **Mid-run bosses are the progression gates; the final boss is the mastery test.** HoT unlocks the next hall from a boss at 6–16 minutes, not from the Lord, so new players progress without beating the hardest fight. For SU's 15:00 blessing and 30:00 boss, consider letting the 15:00 encounter (or a mid-run boss) gate night-to-night progression.
3. **Never ship an unavoidable death timer as a DPS check.** The 40-second curse was the most resented mechanic in EA and was replaced within weeks by an escalating boss (faster over time). Escalation keeps a weak build in the fight and lets skill substitute for numbers.
4. **Offer an in-world, optional "boss hex" per arena.** HoT's secrets (halve HP, disarm adds, remove invulnerability, simplify patterns with a HUD-signalled punish window, a turret that shoots the boss) give under-powered players a knowledge route and turn the 30 minutes before the boss into preparation. SU's day-side ARPG could seed these.
5. **Boss adds must never soak the player's auto-aim or projectiles.** Exclude summoned hazards from targeting, give them a contact-trigger with a visible fuse, and clear them on boss death.
6. **Tune boss patterns for a crowded screen:** no attacks triggered from off-screen, slower and sparser bullets, smaller damage zones, larger hurtboxes; draw player effects under enemy projectiles; give an opacity slider; add sound cues to lunges. HoT shipped every one of these after complaints.
7. **Keep CC from trivialising bosses with resistances and floors, not immunities**: slow resistance 66% for bosses and 80% for Lords with a 50% slow floor still rewards CC builds a little.
8. **Accept a huge power spread but stop runaway numbers breaking things.** HoT lets late builds melt Lords in seconds and moved difficulty to opt-in modifiers (Agony clock, Torment artifacts, three-Lord Malignant Mirror, Demonic Cube). It had to cut per-rank HP scaling from ×1.2 to ×1.12 (later ×1.09) when HP hit engine limits. Use additive-plus-modest-multiplicative scaling and cap it.
9. **Let power shorten the night.** Kill-count Lord spawns (Boglands) and a player-unsealed Lord (Vault) convert strength into speed; the endless phase should scale until the player chooses to collect the reward (HoT: the run ends when the shard is picked up).
10. **Make the victory lap short and the reward physical.** The Lord drops a crystal; picking it up is the win; the well teleports to you. A single, visible pickup is a clean "you won" beat; avoid making the player walk through a still-dangerous field to cash out.

## Gaps

- Numeric HP for any boss or Lord: not published by the developers or the wiki; the only figure is one player's claim for the Lord of Discord (400,000 base, ~5.5 million at max Agony).
- Attack lists for most mid-bosses (Imp Chieftain, Skeleton Lord, Lich, Flamedancer, Wraith Warlord, Wyrm Queen, Wraith Horseman, Frost Knight, Hydra, Basilisk, Twisted Construct, Elder Giant, Void Caller, The Village, Twisted Knight, Bog Serpent, Blightfiend), Lord of Discord, Lord of Greed and Lord of Blight: not found in readable sources (Prima/PC Invasion guides blocked; wiki.gg blocked; Reddit blocked).
- Spawn time of the Twisted Knight and full Chambers wave table; Boglands mid-boss triggers.
- Exact Lord-of-Pain escalation rate ("gets faster over time"): not published.
- Whether normal-mode spawning stops when the Lord appears is inferred from the Torn Stage Curtain artifact text.
- Reddit opinion: r/HallsOfTorment could not be fetched; opinion is drawn from Steam discussions only.

## Verification

Adversarial check, 3 Oct 2026. I re-fetched the Steam news items through the ISteamNews API (appid 2218750; the akamaihd links redirect to steamcommunity.com announcement pages), pulled the wiki pages live through the Fandom MediaWiki API, and downloaded the Steam threads directly.

1. **Elite blue / boss red outlines (17 Feb 2023).** CONFIRMED. "Playtest Update 2023-02-17" says verbatim: "Elites now have a blue outline while bosses have red outlines" and "Increased speed of Elites and Boss Monsters".
2. **Haunted Caverns wave timings.** CONFIRMED against the live wiki (rev. 25 Dec 2025): 27:40 Sturdy Elite, 24:00 Imp Chieftain, 19:45 Shield Elite, 16:00 Skeleton Lord, 11:40 Mage Elite, 08:00 Lich, 00:00 Lord of Pain. This is community data, not a developer source.
3. **40-second Curse; dev says the intended timer was 6 s, countered by an item.** CONFIRMED. The wiki Curse page says "kills the player after 40 seconds ... only continue fighting with Revivals". In the thread, user Ulyaoth says "I liked the 40sec timer" (8 Jun 2023). The 6-second quote was posted by "June the Fool", tagged Developer – Chasing Carrots, on 6 Jun 2023 (US time). Minor correction: the notes call this poster the "community manager", but the forum tag says Developer. A 6 Apr 2023 patch independently says "we plan to add a quest item that allows you to cancel the curse projectile" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5121196841288022894).
4. **June 2023 rework quote.** PARTLY RIGHT (citation is wrong). The four bullets ("Death timer has been removed. / The Lord of Pain will now get stronger over time. / Lord of Pain HP have been reduced a bit. / Adding a mechanic to ease the Lord of Pain fight.") come from "HoT Beta Update | 2023-06-06" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5151601211244614602), not from the 9 Jun post. The 9 Jun live post (5129083846342681607) contains only the prose: "we added a mechanic where the lord gets harder as time passes ... hidden mechanic in the Haunted Caverns". The content is accurate. The beta shipped on 6 Jun and went live on 9 Jun.
5. **Protective Pendant: guaranteed crit, 50% of Lord HP regardless of Agony/Torment, Fragile increases it.** CONFIRMED on the live wiki (community-written). A player (Nelartux, Mar 2024, thread 4344355442320728556) corroborates the Fragile interaction. No developer source states the 50% figure.
6. **July 2023: Ember/Viaduct Lords get less HP and scale over time; projectiles and guards untargetable.** CONFIRMED verbatim in "HoT Journal | 2023-07-17". It was a plan at that point: it went to beta on 31 Jul 2023 ("All lords now work by getting stronger over time and having reduced Health pools", 5124584686261074502) and live on 31 Aug 2023. The "capped to stacks of 20" quote is also confirmed.
7. **Frozen Depths boss fixes plus opacity setting.** CONFIRMED verbatim in "HoT Update 2023-09-05", under the "Frozen Depth Bosses" header, together with "added opacity setting for player ability effects".
8. **Slow resistance and limits.** CONFIRMED verbatim in "HoT Update 2023-10-30": "Resistance: champion (25%), elite (50%), boss (66%), lord (80%)" / "Limit: champion (30%), elite, boss, lord (50%)". Caveat: this is the Oct 2023 value, and no later change turned up in the feed's 98 items.
9. **Vault Lord unsealed via 4 Pylons of 50,000 base HP; the run lasts while the Lord is alive; strength rises after 30 min.** CONFIRMED. The 1.0 notes (6341720536520860655) carry the three developer sentences verbatim. The live wiki (rev. 30 Nov 2025) has the Pylon count and HP, which are community data. Note a tension: the developers say the run lasts "as long as the lord is alive", but a player tip (§2.6) says the run actually ends when the shard is picked up. Treat the "ends on pickup" reading as player-reported.
10. **Boglands kill trigger: 25,000 at launch, 20,000 now.** CONFIRMED as stated. Launch notes say "the Lord triggers after defeating 25 000 Enemies". The live wiki (rev. 17 May 2026) says "20 000 kills", and a player (Jan 2026, thread 735909930464360603) says "He spawns after 20.000 kills." I found no patch note for the change in the 98-item API feed, so the reduction stays unexplained. Also, the 2026 Kill Mode notes say per-map kill counts were "balanced", so the number may change again.
11. **Artifact texts (Malignant Mirror, Demonic Cube, Torn Stage Curtain).** CONFIRMED in the live Module:ArtifactData (rev. 24 Nov 2025). The full Mirror text is "Three Lords appear at the end of a run, instead of a single Lord." Torn Stage Curtain requires the Bard hero and the "Aftershow Performer" quest.
12. **Player opinion quotes.** PARTLY RIGHT (attribution). The Lord of Regret quote is exact: Arcane Azmadi, 30 May 2023, thread 3833172326396523543. The post goes on immediately with "Of course he isn't, that's hyperbolic in the extreme", and "ten million HP" is hyperbole, not a measurement. The "only Lord that feels like a Lord" quote is NOT in that thread. It comes from Ulyaoth, 27 Feb 2024, in https://steamcommunity.com/app/2218750/discussions/0/4344355442320728556/. The table in §5 cites it correctly.

Other spot checks: the Torment HP change from ×1.2 to ×1.12 is confirmed (experimental 8 Oct 2024, live 10 Oct 2024). Torment Health going from ×1.11 to ×1.09 is confirmed (14 Oct and 28 Oct 2025), so the wiki's ×1.11 is stale. "Agony will add 1 Defense to each enemy per rank" is confirmed. "Agony will increase by 1 level every 5 minutes" is confirmed (experimental 7 Dec 2023, live 14 Dec 2023). The first champions spawning after 90 s is confirmed (13 Sep 2023). The well teleporting to the player is confirmed (1.0 notes).
