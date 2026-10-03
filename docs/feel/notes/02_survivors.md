# 02 — Survivors-likes: what makes them feel so good

Research brief for a dark-fantasy hybrid with 30-minute "ember arena" night runs (auto weapons, hordes, level-up drafts of skills and blessings, a boss at 30:00).
Compiled 2026-10-03. Every claim carries a source URL. **[S]** = sourced number, **[E]** = my estimate or inference.

**Method note.** Besides articles, wikis and interviews, I pulled the most recent ~2,000 English Steam reviews for each of 10 games through Steam's public review endpoint (`store.steampowered.com/appreviews/<id>?json=1`, run on 2026-10-03) and counted keyword hits per 1,000 reviews. These are recent reviews, so they lean towards fans who stuck with each game. Use the counts to compare games, not as absolute measures. Reddit could not be fetched from this environment (blocked), so the player vocabulary below comes from Steam reviews, Steam discussion threads and aggregated review-theme summaries (Vaporlens).

---

## 1. Scoreboard (Steam, all languages, pulled 2026-10-03)

| Game | Steam reviews | Positive % | Negative % in recent sample | Store id |
|---|---|---|---|---|
| Vampire Survivors | 266,128 | 98.3% | 5.0% | 1794680 |
| Brotato | 119,396 | 95.9% | 5.5% | 1942280 |
| Megabonk | 106,646 | 94.3% | 10.5% | 3405340 |
| Deep Rock Galactic: Survivor | 48,377 | 86.2% | 17.9% | 2321470 |
| HoloCure (free) | 40,824 | 99.0% | 1.5% | 2420510 |
| Halls of Torment | 31,911 | 95.3% | 8.8% | 2218750 |
| 20 Minutes Till Dawn | 29,162 | 90.3% | 17.8% | 1966900 |
| Soulstone Survivors | 26,875 | 91.3% | 10.4% | 2066020 |
| Death Must Die | 21,782 | 90.1% | 18.3% | 2334730 |
| Magicraft | 16,931 | 92.8% | 4.8% | 2103140 |

Source: Steam appreviews API (e.g. https://store.steampowered.com/appreviews/1794680?json=1). The most-reviewed games (VS, Brotato, Megabonk, HoloCure) are also the simplest to read and the quickest to "get". The 86–91% band (DRG:S, 20MTD, Death Must Die, Soulstone) is where grind, meta-progression gates or narrow viable builds draw complaints (see §5).

Other scale signals: Megabonk sold 1M copies in two weeks and peaked at **117,336** concurrent players (https://en.wikipedia.org/wiki/Megabonk). Brotato passed **10M** copies by 2025 (https://en.wikipedia.org/wiki/Brotato). VS reached 70,000+ concurrent players in Feb 2022 (https://en.wikipedia.org/wiki/Vampire_Survivors). HoloCure launched on Steam to 45,000 concurrent players at 99% positive (via https://en.wikipedia.org/wiki/HoloCure_%E2%80%93_Save_the_Fans!). In May 2026 Steam adopted "Bullet Heaven" as the official genre tag, after a poll with 8,000 responses (https://en.wikipedia.org/wiki/Vampire_Survivors%E2%80%93like).

---

## 2. Vampire Survivors: the template

### 2.1 Galante's own words
- **Slot-machine craft.** In slots, "there's a huge attention to detail on the sounds, the animations, and the sequences, because you have so few elements to work with" (Galante to The Verge, quoted at https://mechanicsofmagic.com/2024/05/22/critical-play-vampire-survivors/). Elsewhere: "there must be a delicate balance between reward and difficulty" (translated from https://multiplayer.it/articoli/vampire-survivors-intervista.html).
- **Downplays direct gambling design:** "I was mostly working on systems and details rather than game design" (https://www.androidpolice.com/vampire-survivors-developer-interview/).
- **The chest:** "I put a lot of work into making a super rewarding and over-the-top treasure chest animation that matches a catchy little sound." He wrote it after noticing that a slot game he had worked on had a good chest jingle that did not match its animation (same source).
- **Draft size:** "settling on three to four options when leveling up felt like the perfect balance… I really don't like only having two options… more than three to four felt overwhelming" (same source). **[S] 3–4 choices.**
- **Controls:** he compares VS to Pac-Man, "you control a sprite that can only move in four directions". He automated attacks to make the game "lighter and more immediate" and cited Bayonetta and Dynasty Warriors as influences. He saw streamers using it "as a pastime while chatting" (https://multiplayer.it/articoli/vampire-survivors-intervista.html).
- **Fun over balance:** "It's absolutely not balance; balance is completely out of the window. I just want to make stuff that is fun" (https://www.pockettactics.com/vampire-survivors/interview).
- The look began as free asset packs, "very chaotic [and] messy" (https://www.gamedeveloper.com/design/vampire-survivors-development-sounds-like-an-open-source-fueled-fever-dream). The main inspiration was the mobile game *Magic Survival* (https://en.wikipedia.org/wiki/Vampire_Survivors).

### 2.2 The treasure chest: a slot machine in the middle of combat
- Sequence: gameplay pauses, swirling lights move in and out of the chest, possible rewards cycle "like a slot machine reel", special music surges and the gold counter ticks up (https://mechanicsofmagic.com/2024/05/22/critical-play-vampire-survivors/). The animation can be skipped with ESC "after getting a handful of treasures" (https://vampire.survivors.wiki/w/Treasure_Chest).
- **Odds [S]:** the 1-item chest has a 50% base chance, the 3-item chest 10% if that roll fails, and the 5-item chest 3% if both fail. These are per-boss values multiplied by Luck, and "only the quality of the chest is affected by Luck". Gold by tier: **100–200 / 300–600 / 500–1,000**. There are **three different jingles** (Treasure A/B/C) for the three tiers. Generally **only one evolution per chest**, and chests usually enable evolutions only after **10:00** (https://vampire.survivors.wiki/w/Treasure_Chest).
- Players respond to it directly: "My dopamine levels spike as soon as the treasure chests start rolling and the music starts playing" (Steam review, VS, 61h, appreviews sample).

### 2.3 Level-up draft and XP curve
- **3 or 4 options [S]**, with P(4th option) = 1 − 1/Luck. Reroll, Skip and Banish are bought as meta PowerUps. Skips and Rerolls stop working once the inventory is full (https://vampire.survivors.wiki/w/Level_up).
- **Banish cap [S]:** at most 10 uses at max rank, against "100+ level-up choices per game". It works because "the player's ability to make use of Banish only scales with the potential need" (https://gmdq.substack.com/p/vampire-survivors-banish-mechanic).
- **XP curve [S]:** level 2 costs 5 XP. Each level then costs +10 more XP up to level 20, +13 per level for 21–40 and +16 per level from 41. Levels 20 and 40 each add a one-off **600 / 2,400** XP tax, offset by **+100% Growth** for that level (https://vampire.survivors.wiki/w/Level_up; https://vampire.survivors.wiki/w/Growth). In practice levels come every few seconds early on, the pace eases around 20, and the curve is linear rather than quadratic, so late levels never take "minutes/hours" (Steam thread https://steamcommunity.com/app/1794680/discussions/0/3717188244455231479/?ctp=3).
- **Inventory [S]:** 6 weapons + 6 passives. Once both are maxed, level-ups give gold or healing (https://en.wikipedia.org/wiki/Vampire_Survivors).
- **Limit Break [S]:** an optional modifier (after unlocking Great Gospel) that lets maxed gear keep levelling in small steps (Might +1%, Area +5%, Speed +5%, Amount +1, Pierce +1, Crit +2.5% and so on) instead of dropping to gold or healing (https://primagames.com/tips/how-to-limit-break-in-vampire-survivors). With Limit Break, players report reaching level **~14,000** by 30:00 and say "everything is just exploding with coins all the time" until "the game engine collapses" (https://steamcommunity.com/app/1794680/discussions/0/3717188244455231479/?ctp=3).

### 2.4 The XP gem economy: vacuum, cap and "level-up explosion"
- Gem tiers: blue ≤2 XP, green ≤9 XP, red above that (https://vampire-survivors.fandom.com/wiki/Experience_Gem).
- **Cap [S]: 400 gems on the map.** Above the cap, new XP goes into one red gem, so picking it up fires a burst of several level-ups in a row (https://steamcommunity.com/app/1794680/discussions/0/4650551739541818271). This is the source of the "level-up explosion" players describe. It works as a performance cap and as a jackpot at the same time.
- Collecting gems sets off a "chorus of chimes… reminiscent of coins clattering out of an old slot machine" (https://mechanicsofmagic.com/2024/05/22/critical-play-vampire-survivors/). Vacuum pickups (Vacuum/Rosary-style screen pickups) cash in the whole board at once, the same move as hitting a jackpot.

### 2.5 Minute-by-minute shape: Mad Forest, the 30-minute stage [S]
From the wave table at https://vampire.survivors.wiki/w/Mad_Forest ("min count" is the minimum number of enemies the spawner keeps alive, "interval" is the spawn tick):

| Phase | Minutes | Min alive | Interval | Set pieces |
|---|---|---|---|---|
| Onboarding | 0–1 | 15 → 30 | 1.0s | First boss (Glowing Bat) + treasure at **1:00** |
| First pressure | 2–4 | 30–50 | 0.25–1.0s | First **bat swarm (x3) at 2:00**, treasure at 3:00 |
| Mid set pieces | 5–9 | 10–100 | 0.5–1.5s | **Flower Wall at 5:00** (30s), Mantichana boss, swarms 80% at 7–8 |
| **Build online** | 10 | 10 | 0.5s | **Evolution treasure** begins at 10:00, Flower Wall 60s |
| **Spike** | 11 | **300** | **0.1s** | Skeleton flood + **Arcana boss** |
| Escalation | 12–20 | 20–150 | 0.1–1.0s | Treasure almost every minute; Ghost Swarm x21 at 13; Giant Werewolf at 15; Giant Mummy at 20 |
| Endgame | 21–29 | **200–300** | 0.1s | **Arcana boss at 21**, Flower Walls, Giant Blue Venus at 25, swarms at 27 and 29 |
| Cap | 30:00 | — | — | Screen cleared; **the Reaper** spawns, +1 Reaper per minute |

Takeaways: (a) there is a boss or treasure event roughly every 1–2 minutes and almost every minute after 10:00; (b) the density doesn't climb steadily. It swings, with quiet minutes (min count 10–20) right next to 300-enemy floods; (c) the 10:00 evolution unlock lines up with the first big spike at 11:00, so the player's "build comes online" moment and the game's escalation arrive together; (d) at 30:00 the game clears the screen to silence before the Reaper arrives. Critics describe the same rhythm: "periods where players comfortably dominate enemies are followed by periods of increased tension" (https://stuff.co.za/?p=164881). Every 30-minute map caps the run with the Reaper, and shorter maps run 15 or 20 minutes (https://en.wikipedia.org/wiki/Vampire_Survivors).

### 2.6 Arcanas: blessings at fixed times [S]
You pick 1 Arcana at the start. Special bosses at **11:00 and 21:00** drop Arcana chests that offer **4 random Arcanas (6 once 23+ are unlocked, plus 1 free reroll)**, for **3 Arcanas per run** (https://vampire.survivors.wiki/w/Arcana). On shorter stages the bosses come at 5:00 and 10:00. This is the closest existing model for our "blessings": rare, timed, rule-bending picks kept apart from the normal level-up draft.

### 2.7 "Screen full of weapons" and its cost
- NME: "killing absolutely thousands of enemies, often so quickly you'll struggle to keep track"; "trying to stack up as many evolved weapons as possible" (https://nme.com/reviews/game-reviews/vampire-survivors-review-3332668).
- The cost: "I can't see anything anymore due to the weapon effects". Clock Lancet "blots out the entire screen". Players call late runs "virtually unplayable", and poncle reportedly said it doesn't "intend to add anything like an opacity slider" (https://steamcommunity.com/app/1794680/discussions/0/4631482569784862180). From the review sample: "LET US TURN DOWN OR TURN OFF WEAPON EFFECTS I CANT SEE A DAMN THING" (37h, positive); "most runs devolve into a mess of spam and eye-bleed where you just AFK until it ends" (6h, positive).
- RPS's Ed Thorn: most clones did a poor job of separating the player from the visual clutter compared with VS (https://en.wikipedia.org/wiki/Vampire_Survivors%E2%80%93like). VS's 8/16-bit sprites, flat backgrounds and limited palette are part of why it still reads well at high density.

---

## 3. Per-game notes: the one idea each game adds

### Brotato: arena waves plus an autochess shop
- **Structure [S]:** 20 waves. Wave 1 lasts **20s**, each wave adds **+5s** up to **60s** at wave 9, waves 9–19 stay at 60s and wave 20 is **90s** with **1–2 bosses**. On higher Dangers, Horde or Elite waves (40/60 split) appear around waves 11–12 and 14–15, plus a guaranteed Elite at 17 or 18 (https://brotato.wiki.spellsandguns.com/Waves). A full run is ≈ **17–18 minutes of combat** [E, summed from the above].
- **Shop [S]:** 4 slots. Waves 1–2 always offer 2 weapons + 2 items; from wave 6 each slot is 65% item and 35% weapon. Reroll cost = ⌊wave×0.75⌋ + ⌊wave×0.40⌋, rising by ⌊wave×0.40⌋ per reroll. Slots can be locked across waves. Tier odds open in steps: T2 from wave 2 (+6%/wave, max 60%), T3 from wave 4, T4 from wave 8 (max 8%) (https://brotato.wiki.spellsandguns.com/Shop).
- **Intent:** Gervraud combined "survivor-likes with hordes of enemies" with "autochess games with a shop" (https://en.wikipedia.org/wiki/Brotato). "Most weapons and items are designed to be effective without requiring particular thought, while offering potential synergies for those wishing to optimize" (translated, https://news.xbox.com/fr-fr/2024/02/09/entretien-exclusif-avec-thomas-gervraud-brotato-le-jeu-qui-a-de-la-patate/).
- **Players:** short runs are a reason to keep playing (https://vaporlens.app/app/1942280/brotato). Among recent negative reviews, "too hard/difficult" (16%) and RNG (14%) lead; in the full sample, "can't see" is ~1/1000 (appreviews sample). The pause between waves acts as a breather and a planning step, which longer continuous runs lack.

### HoloCure: polish, more control, collabs and stamps
- **Draft [S]:** **4** options. Reroll ×10, **Hold ×5** (pins an option to the next level-up) and Eliminate ×10, all bought in the meta shop. Rerolled options get lower weights. XP: 79 for level 2, then `round((4(L+1))^2.1) − round((4L)^2.1)` (https://holocure.wiki.gg/wiki/Level_Up).
- **Collabs [S]:** two max-level weapons fuse at a Golden Anvil. The anvil drops once two eligible weapons reach Lv7+, at a base rate of **1/100 that grows by 1/2000 per minute**. There are 31 collabs and 4 super collabs (collab + item), with 5 weapon slots so at most 4 collabs (https://holocure.wiki.gg/wiki/Collabs). This is VS's evolution with a visible recipe and a physical drop to chase.
- **Stamps [S]:** 3 slots per weapon, each up to Lv3 (e.g. ATK +15%, Haste −15% attack time, Life Steal 5% max HP/s, plus a purely cosmetic "Reverse" stamp). They drop at **1/780** from enemies and always from Silver YAGOOs (https://holocure.wiki.gg/wiki/Stamps).
- **Critics:** GamesRadar called it "the best Vampire Survivors imitator… can go toe-to-toe with the hit that inspired it" but "a much slower burn when it comes to fulfilling the power fantasy" (via https://en.wikipedia.org/wiki/HoloCure_%E2%80%93_Save_the_Fans!). Superjump points to "beautifully animated weapon effects" and the ability to "drop unneeded items or reroll" (https://www.superjumpmagazine.com/holocure-setting-the-standard-for-fan-made-games/). Kay Yu, previously lead animator on *River City Girls*, requires each character to have "some unique mechanic that determines how that character plays" (https://www.moguravr.com/holocure-developer-interviews/).
- **Complaints [S]:** visual clutter (27% of negative themes), "excessive damage numbers and effects obstruct character visibility", and performance (28%) (https://vaporlens.app/app/2420510/holo_cure_save_the_fans.md).

### Halls of Torment: Diablo dress, slow and itemised
- 30-minute endurance runs; Diablo-1/2 look, gear kept in a hub chest, gear carried between runs through **wells**, 11 characters (https://godisageek.com/reviews/halls-of-torment-review). **Abilities** come from Tomes/Scrolls of Mastery at fixed map spots and from elites, not from level-ups. You can hold up to **6 abilities**, each with up to 3 upgrades of which 2 can be picked per run (https://hallsoftorment.fandom.com/api.php?action=parse&page=Ability&prop=wikitext&format=json). Level-ups grant traits. Splitting "pick up a new verb" (map loot) from "tune your stats" (level-up) is a model we can use for **skills (map/elite) vs. blessings (level draft)**.
- Jim Sterling: "you can make a successful build that looks positively conservative in terms of filling the screen" and the game is "not just basic things like damage and health" (Block, Force). 8.5/10, marked down for hard freezes (https://www.thejimquisition.com/post/halls-of-torment-stat-s-all-folks-review).
- **The most relevant warning for a 30-minute run:** "30-minute runs feel excessively long and tiring" is a named negative theme (https://vaporlens.app/app/2218750/halls_of_torment). From the review sample: "30 minute rounds are like torture. There is eventually a item that turns them into 20 min rounds which is clutch"; "give us an option to x2 it" (Halls of Torment reviews, appreviews sample). Run-length complaints are **9.0/1000** reviews, the highest of the 10 games (VS 5.0, Megabonk 2.5, Brotato 3.5). Negative reviews also mention "boring" (18%) and "slow" (11%).

### 20 Minutes Till Dawn: manual aim and darkness
- Twin-stick with **manual aim** (auto-aim optional). You reload whenever you are not shooting. Modes: 20 min, 10 min Quickplay, Endless (https://gigazine.net/gsc_news/en/20230415-20-minutes-till-dawn). Upgrades come as **sets of 4** chained trees ("you'll need to pick the first to be able to get the rest"), with bosses at **5 and 15 min** and a "dim light around the character surrounded by darkness" (https://www.keengamer.com/articles/reviews/pc-reviews/20-minutes-till-dawn-review-surviving-the-swarm/).
- **The darkness cuts both ways:** 14 mentions say the "limited color palette (black, white, red/green) causes significant eye strain" (https://vaporlens.app/app/1966900/20_minutes_till_dawn). Run-length is mentioned 104/1000 in the sample, mostly as praise for short runs. The darkness fits our theme but needs care.

### Soulstone Survivors: a big skill-and-rune catalogue with clutter and grind
- 350+ active and passive skills, runes, and crafted weapons that change a character's affinity (https://lootlevelchill.com/reviews/soulstone-survivors-review/). Early praise for "gameplay feel" and a steady 60 FPS (http://www.gamingonlinux.com/2022/11/soulstone-survivors-might-dethrone-the-likes-of-vampire-survivors-for-me).
- **Negatives [S]:** grind 33%, repetition 27%, performance 21% ("late-game performance severely degrades"), clutter 8% (https://vaporlens.app/app/2066020/soulstone_survivors.md). Players describe "a circus of red circles" at max difficulty and a flamethrower that "hits significantly outside of the shown hitbox" (https://steamcommunity.com/app/2066020/discussions/0/3591086730702915808). The sample has the most "can't see" hits (20/1000) and the most grind hits (86/1000) of any game. Soulstone does ship a Settings > Graphics > Special Effects Visibility slider (per a search summary of https://steamcommunity.com/app/2066020/discussions/0/3591086730691827584; thread not opened directly).

### Deep Rock Galactic: Survivor: verbs beyond walking
- **Mining** turns terrain into a tool: "create bottlenecks to funnel enemies into, as well as escape routes"; "So many survivor-likes struggle to create a worthwhile play-space, but that's not the case here" (https://rogueliker.com/deep-rock-galactic-survivor-early-access-review). Missions: mine an ore quota → boss → **extract before the timer runs out** (https://lootlevelchill.com/reviews/deep-rock-galactic-survivor-review/).
- **Overclocks** are the payoff, which drags down the rest: "Every upgrade just feels like I'm saving up for the actual fun upgrades, the overclocks" (Steam review, 23h). "Certain overclocks are simply worse… making each run feel the same" (lootlevelchill). **Grind appears in 30% of negative reviews and meta upgrades in 21%**, the highest of any game (appreviews sample).

### Death Must Die: Hades-style god blessings
- "6 Gods with 10+ Skills each" at Early Access, randomised Diablo-style items, "choose every little building block of your loadout" (https://earlygame.com/general-news/death-must-die-meet-the-game-with-hades-diablo-and-vampire-survivors-elements). Players call it a "Fantastic dark-fantasy roguelike" and say "vampire survivors and hades had a child" (Steam reviews, appreviews sample). This is the closest market comparison for our dark fantasy with blessings.
- It has the highest negative share in the recent sample (18.3%). The causes are spread out: balance 9%, hard 9%, grind 7%. One review sums up the fatigue: "10 hour: Cool 30 hour: ok 45 hour: mmmmmm" (appreviews sample).

### Magicraft: spell crafting
- 100 spells, 100 staves and 80 relics; the "ultra-high degrees of freedom" mean even the developers have not tried every combination (https://store.steampowered.com/app/2103140/Magicraft/). Players: "if you get a build you are aiming for, you feel unstoppable"; "all about exploiting or breaking the game"; UI is "not quite polished… less complex than noita" (appreviews sample). Synergy is mentioned 20/1000, second only to 20MTD (36).

### Megabonk: 3D movement plus "number go up"
- Built by a solo developer who wanted VS "in 3D, with more focus on movement" (https://en.wikipedia.org/wiki/Megabonk). Movement: jump, slide, speed boosts, extra jumps: "slide all the way down a hill on a sword while all your abilities fire off — it's so satisfying and dumb"; "everything is very visually readable despite how much crazy stuff is happening" (https://www.gamingonlinux.com/2025/09/megabonk-is-risk-of-rain-2-fused-with-vampire-survivors-and-its-glorious/page=1/).
- **Structure [S]:** about **10 minutes per stage**, then a **Final Swarm**; find the boss portal or survive. Shrines on the map (XP magnet, stat charge, greed risk-reward) (https://www.dtgre.com/2025/10/megabonk-beginners-guide-survive-first-10-minute-run.html). One negative review: "around 10 or so minutes in a level before 'the final wave'… rush through the entire thing" (appreviews sample). The timer adds tension, but some players feel it rushes exploration.
- FullCleared: "very weak you can feel at the start, but with each passing minute you feel stronger"; "RNG is still king" (https://fullcleared.com/reviews/megabonk-review/). In the sample Megabonk has the highest "dopamine" rate after VS (18/1000), the most "movement" mentions (28/1000) and **zero** "can't see" complaints in its negative reviews. RNG (15%) and balance (8%) lead its negative reviews.

### Risk of Rain 2 / Binding of Isaac: time as the difficulty dial
- RoR2: coefficient = (playerFactor + minutes × 0.0506 × difficulty × players^0.2) × 1.15^stages. That is about **+0.10 per minute on Rainstorm**, shown on screen as Easy → … → "HAHAHAHA" (https://riskofrain2.wiki.gg/wiki/Difficulty). Showing the clock as a threat is the model for a visible night meter. (Isaac: no specific numeric source gathered in this pass; its relevance is item-synergy stacking, which Magicraft and HoloCure collabs already cover.)

---

## 4. Themes across games

### 4.1 The reward loop, and why "gambling" is accurate but incomplete
Three nested slot machines: (1) **gems**, many small chimes all the time; (2) **level-up**, a pause with 3–4 cards about every 5–20 s early on [E]; (3) **chest**, a rare jackpot with a reel, music and gold counter, with a 3% gold tier. Academic commentary credits VS with near-miss effects ("every run in which players don't reach the 30 minute mark") and layered rewards ("No run ever feels wasted") (https://theconversation.com/vampire-survivors-how-developers-used-gambling-psychology-to-create-a-bafta-winning-game-203613; https://stuff.co.za/?p=164881). Galante himself plays down using gambling design directly, and his stated concern is matching sound and animation (Android Police, above).

### 4.2 The words players use (Steam sample, mentions per 1,000 reviews)

| Term | VS | Megabonk | HoT | Soulstone | Brotato | HoloCure |
|---|---|---|---|---|---|---|
| "addict-" | **138** | 81 | 77 | 56 | 62 | 63 |
| "dopamine" | **32** | 18 | 11 | 9 | 5 | 2 |
| "brain off / mindless / brainrot" | 16 | 14 | 12 | **20** | 8 | 5 |
| "satisf-" | 21 | 6 | 25 | 24 | 11 | 9 |
| "one more run" | 11 | 8 | 9 | 10 | 4 | 2 |
| "can't see / clutter / particles" | 6 | 0 | 4 | **20** | 1 | 1 |
| "grind" | 16 | 18 | 32 | **86** | 10 | 22 |
| "lag / fps / crash" | 6 | 6 | **34** | 20 | 6 | 8 |
| "relax / chill / cozy" | 14 | 10 | 17 | 22 | 14 | 19 |

(appreviews sample; regexes in method note.) Representative short quotes: "pure dopamine", "Dopamine generator", "A good game to just turn your brain off", "Brainrot for millenials", "evolving garlic into a war crime", "the early dopamine hit from this game is real… after like 2 weeks… that feeling dies down" (Megabonk, 67h). "Crunchy" barely appears in reviews (≤2/1000). It is a developer and critic word, not a player word.

### 4.3 What players complain about
- **"Slow start / boring early game."** VS: 24 mentions of a "slow and boring" early game (https://vaporlens.app/app/1794680/vampire_survivors). Players say "It starts slow…" and "Starts off kinda slow and difficult but once you focus on unlocking stuff…". HoT: "boring on the first few runs. But once you start unlocking stuff, it gets really good." This is mostly **meta-progression** slowness, not the first minute of a run.
- **"Autopilot / AFK" once the build is done.** "you just AFK until it ends" (VS); "Hate how repetitive and automatic this game is" (HoT, negative). Explicit "autopilot/idle/afk" hits are rare (≤6/1000), but the complaint shows up instead as "boring", which appears in 7–18% of negative reviews in every game.
- **"Can't see anything."** Concentrated in Soulstone (3D effects, telegraph circles), HoloCure (damage numbers) and VS (specific evolutions). Near zero in Megabonk and Brotato, which have readable silhouettes and low effect density.
- **Lag and crashes** grow with entity count late in a run: HoT 21% of negatives, Soulstone 21% performance theme, HoloCure 28%.
- **"Same every run" / narrow viable builds:** 20MTD 34 balance mentions, DRG:S overclock tunnelling, Soulstone "characters feel almost identical".
- **Grind gating fun:** DRG:S 30% of negatives, Soulstone 33% theme.
- **Run length:** only HoT, the 30-minute benchmark, draws repeated "too long" complaints. VS gets few despite the same 30-minute length, likely because its density swings and almost-every-minute treasures keep a 30-minute run varied [E].

### 4.4 Which feel better, and why (critics plus players)
1. **VS:** best reward audio and visuals per element. Minimal, readable sprites. Weakest on late-game readability.
2. **HoloCure:** praised as polished and fully free, with an animator's eye for effects and more player control (Hold/Eliminate). Some find the power fantasy a "slower burn".
3. **Megabonk:** movement as feel (slides, jumps) plus clean readability; criticised for RNG.
4. **Brotato:** short waves and a shop make each wave a complete mini-loop; low clutter.
5. **HoT / Soulstone / DRG:S / DMD:** deeper systems, but grind, length and clutter drag them down. HoT is praised for a "methodical" dark mood; Soulstone is the cautionary example for clutter.
Lifeless clones fail on **readability** (RPS) and on **audiovisual payoff per event**, not on the number of systems.

---

## 5. Pacing synthesis for a 30-minute run
- **Event cadence [S, VS]:** a treasure or boss about every 60–120 s; something new almost every minute after 10:00.
- **Density swings [S, VS]:** the minimum alive count ranges from 10 to 300 within the same run, with the spawn tick dropping from 1.0s to 0.1s after 11:00.
- **Build online [S, VS]:** evolutions enabled from 10:00 (one-third of the run); special-boss blessings at 11:00 and 21:00.
- **Brotato rhythm [S]:** combat bursts of 20–60 s plus a shop pause; total ≈17–18 min [E].
- **Megabonk rhythm [S]:** about 10 min per stage plus a Final Swarm, so a 30-min session ≈ 3 stages [E].
- **HoT warning [S]:** 30 minutes of uniform pressure reads as "torture". Players welcome items that shorten it to 20 minutes.

---

## Implications for the ember-arena night run

1. **Split the 30:00 night into 3 acts with set-piece hinges at ~10:00 and ~20:00.** Unlock evolutions or "ascensions" at 10:00, as VS does [S], and put a blessing boss at 11:00 and 21:00 [S, VS Arcana timing]. Act 3 (20–30) is the screen-clearing power trip.
2. **Schedule a named event (elite, swarm, chest, shrine) every 60–90 s, and every ≤60 s after 10:00** [S, derived from VS Mad Forest]. Our biggest risk is Halls of Torment's "30 minutes feels like torture" [S], so cadence matters more than raw difficulty.
3. **Swing density instead of ramping it.** Alternate quiet minutes (≈10–30 alive) with surge minutes (≈150–300 alive, 0.1 s spawn tick) [S, VS]. Start at ~15 alive and 1 s ticks [S]. Aim for about 1 quiet minute per 2 surge minutes in Act 3 [E].
4. **Draft 3 cards, a 4th from Luck, never 2 or 5+** [S, Galante]. Give 1 free reroll per act, banish capped at ~3–5 per run, and a "hold/pin" ×3 (HoloCure [S] has ×5 hold and ×10 reroll/eliminate as meta unlocks) [E for our numbers].
5. **XP curve: ~5 XP for level 2, +10 per level to 20, then steeper, with one tax level and a Growth refund** [S, VS formula]. Target ≈ 1 level every 8–15 s in minutes 0–3, every 30–45 s by minute 15, and ≈ 60–90 level-ups per run [E; VS cites "100+ choices" per game, S]. That leaves 60–90 drafts as content.
6. **Cap ground XP orbs (~400) and pool the overflow into one large "ember" orb** [S, VS's 400 cap]. Picking it up chains several level-ups with escalating chimes. It caps performance and doubles as a jackpot.
7. **Make the chest a full slot-machine sequence: pause, reel, a distinct jingle per tier, gold counter.** Tier odds around 1-item 50% / 3-item 10% / 5-item 3% before Luck, with gold roughly 1× / 3× / 5× [S, VS]. Make it skippable after the first 3 openings [S]. Allow 1 evolution per chest [S].
8. **Keep blessings apart from skills.** Skills (new attack verbs) come from map elites and tomes, as in Halls of Torment [S]. Blessings (rule-bending god boons, Death Must Die / Hades style) come from timed god altars or bosses, picking 1 of 3–4 [S/E]. The level-up draft handles stat and upgrade tuning. This keeps every pick legible.
9. **Show evolution recipes and give fusion its own drop.** Use a HoloCure-style Golden Anvil (base ~1/100 drop, rising per minute) once two eligible pieces reach max [S]. Players chase what they can see.
10. **Commit to readability from day one: an effects-opacity slider (0–100%), a damage-number toggle, and a player silhouette that is always on top.** VS refused the slider and gets "I CAN'T SEE A DAMN THING" [S]. Soulstone ships one and still draws the most clutter complaints (20/1000) [S]. Set the default player-effect opacity to ≈60–70% in Act 3 [E].
11. **Use darkness as a gameplay radius, not an all-over filter.** 20MTD's dark palette is praised for atmosphere but draws eye-strain complaints [S]. Keep a ~6–8 tile ember-lit radius at full contrast, mark off-screen threats with rim glows, and keep pickups lit everywhere [E].
12. **Give one active movement verb (dash or slide, ~3–5 s cooldown) and bend the arena around it.** Megabonk (movement 28/1000, highest "satisfying controls" praise) and DRG:S (mining makes funnels and escape routes) [S] show that extra verbs fight "autopilot". Also consider breakable ember barricades to create chokepoints [E].
13. **Protect the endgame from autopilot: the 30:00 boss should demand movement and reading tells, and blessings should create risk-reward choices (e.g. curses that raise density for more rewards).** "Boring" makes up 7–18% of negatives in every game [S]. VS's Reaper-at-30 works as a run cap, not as a fight.
14. **Keep meta-progression a sidegrade, not a gate.** DRG:S grind appears in 30% of negatives and Soulstone grind is a 33% theme [S]. Make the first night winnable with zero meta upgrades in ~2–5 attempts [E].
15. **Budget performance for 300+ enemies, projectile caps and pooled effects.** Crashes and lag drive HoT (21% of negatives) and HoloCure (28% theme) [S]. Target 60 FPS at 400 enemies + 400 orbs on min-spec, and merge or limit per-weapon projectile visuals [E].
16. **Offer a "short night" option (15 or 20 min) as a mode or late unlock.** HoT players love the item that cuts runs to 20 minutes [S]. VS ships 15/20/30-minute stages [S]; 20MTD has a 10-minute Quickplay [S].
17. **Put the budget into audio and juice per event rather than more systems.** Gem chimes in a "chorus", three chest jingles, a level-up stinger, and tight sound-to-animation sync [S, Galante]. Players say "dopamine" 32/1000 in VS and 2/1000 in HoloCure [S]. That gap comes from the audiovisual payoff, not from system count.
18. **Give the player-facing clock a named threat ladder (RoR2's "Easy → HAHAHAHA", ≈+0.1 coefficient per minute [S]), e.g. ember phases Dusk → Gloam → Witching → Ashfall → Dawn-Eater** [E naming]. This makes the 30 minutes feel like a story arc rather than a countdown.
