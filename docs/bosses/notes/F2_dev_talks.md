> Research notes for `docs/bosses/`, kept as written. Where the **Verification** section at the end corrects a claim, the correction stands; `RESEARCH.md` uses the corrected version.

# F2 — Developer talks, postmortems and interviews on boss design

Strand: developer-side sources (GDC talks, postmortems, interviews, patch notes written by the developers) on boss design relevant to a survivors-like night arena and an isometric ARPG day half. Research date: 3 October 2026.

Conventions: every claim carries a URL. "(secondary)" = seen only in a search-engine summary or a third-party article, not in a primary source I could open. "Not found" = I looked and could not verify. Video talks could not be transcribed in this environment (YouTube and the Amara subtitle downloads were not reachable), so for video-only talks I report only what text pages about them say.

---

## 1. Supergiant Games — Hades (patch notes as a design diary)

Supergiant's Early Access patch notes on Steam are the best primary developer record of how Hades' bosses were tuned. Source for everything in this section: Steam News API for app 1145360 (https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=1145360&count=300&maxlength=0&format=json&feeds=steam_community_announcements), with per-post URLs below.

**Phase damage caps.** Early Access Patch 043 (March 2020) lists: "Fixed rare cases where boss damage limits between phases could be bypassed at the start of fights" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/2698159409992734118). This confirms Hades caps damage at phase thresholds so a strong build cannot burst through a phase transition — the opposite choice to Diablo IV's Season 10 shield-break (section 6).

**Bosses react to the player's losing streaks.** Same patch: "Fixed some losing-streak events for certain bosses playing too infrequently if you met the requirements" (same URL). The bosses have dialogue keyed to how often the player has lost to them — repeated defeat feeds narrative rather than only frustration.

**Extreme Measures as a boss-variant system.** Hades' Pact of Punishment condition "Extreme Measures" changes boss fights rather than just numbers. Examples from developer notes:
- The Nighty Night Update (March 2020): "The Minotaur: updated spin attack, specific to the effect of Extreme Measures (Pact)" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/2579938650942085981).
- Early Access Patch 039 (January 2020): "The Fury Sisters: adjusted some of their attack timings under Extreme Measures (Pact)" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/2597949245066272359).
- The Blood Price Update (June 2020): "The Fury Sisters: increased health and attack speed under Extreme Measures (Pact)" and "Theseus: reduced damage of explosive attack under Extreme Measures (Pact)" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/3384966595888900267).
- v1.0 Launch Update patch notes (September 2020): "The Minotaur: whirlwind attack telegraphs more distinctly while under Extreme Measures (Pact)"; "Extreme Measures: increased Heat for third rank; added fourth rank"; "Extremer Measures: new! Unlock this brutal variant of the Final Boss"; "Final Boss: added variant of this battle while under Extreme Measures (Pact)" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/3819572206267800157).

Design reading: the hard-mode modifier is authored per boss (new moves, new arena behaviour), and when it made an attack harder the team also made its telegraph clearer ("telegraphs more distinctly") — difficulty went up while readability was protected.

**Boss rewards and anti-cheese.** v1.0 notes: "Increased Darkness rewards when vanquishing Bosses"; "Reduced damage Bosses take from using Deflect effects against them"; "Vanquisher's Keep: new! Earn bonus Gemstones from vanquishing Underworld bosses" (same v1.0 URL). The Blood Price Update added "Unshakable Mettle (Poseidon x Athena): new! You can't be stunned, and resist damage from bosses" — i.e. a draftable boon whose value is boss-specific (Blood Price URL above).

**Mini-boss tiering.** Blood Price notes: "Bloodless Slam-Dancers, Wave-Makers, and Burn-Flingers no longer appear as Tartarus mini-bosses" and "Doomstone: new! This Tartarus mini-boss is what Brimstones want to be when they grow up" (Blood Price URL). Mini-bosses are often promoted versions of ordinary enemies the player already knows.

**Theseus and the origin of a boss.** Supergiant creative director Greg Kasavin argued for Zagreus as protagonist over Theseus, who became an Elysium boss alongside Asterius (https://www.nintendolife.com/news/2021/03/hades_almost_had_theseus_as_the_hero_instead_of_zagreus) (secondary — search summary). A direct Kasavin quote on boss design philosophy: not found in text; the Noclip Hades documentary and Kasavin interviews are video-only in this environment.

---

## 2. Dodge Roll — Enter the Gungeon

Q&A with Dave Crooks, Game Developer (Gamasutra), 19 April 2016 (https://www.gamedeveloper.com/design/q-a-the-guns-and-dungeons-of-i-enter-the-gungeon-i-):

- Process: "There are 21 bosses in the game total. The design process for them is fairly varied. In general either our artist (Joe Harty) or myself would pitch the idea for the boss, and as a team we would hash out the basic details. After that, our gameplay programmer (David Rubel) would start experimenting with bullet patterns, which the whole team would give feedback on."
- On the first boss: Gatling Gull is a favourite "because he was our first boss and has had the most refinement".
- On the identity boss: the Beholster "because he is the easiest symbol for our game and what we are trying to make (D&D meets bullet hell)".
- On the skill-check boss: the High Priest "because his attacks are ruthless and varied, and mastering him means you are probably good enough to beat anything Gungeon is going to throw at you."
- On difficulty: "Yes. Our game has always been designed and intended for players who are attracted to challenge... I want to say that it is absolutely possible to do so even with the starting gun."
- On the core verb: the dodge roll was the first non-shooting mechanic, with Dark Souls-style invincibility frames as the model for handling "the massive amount of bullets" (same URL, paraphrased by the fetch tool).

Elsewhere Crooks is reported as saying bosses should "put pressure on the player in THIS way, but they will feel good because they have mastered the dodge roll" (https://gameranx.com/features/id/48447/article/enter-the-gungeon-interview-with-dodge-rolls-dave-crooks-the-past-present-and-future/) (secondary — search summary only).

Design reading: bosses are composed from bullet patterns prototyped by a programmer, then judged by the team; each boss tests the player's one defensive verb in a different way; the first boss gets the most polish because every player meets it.

---

## 3. Studio MDHR — Cuphead, and Game Maker's Toolkit on Cuphead

**Game Maker's Toolkit, "How Cuphead's Bosses (Try to) Kill You"** — Mark Brown, 19 October 2017, about 12 minutes. The episode listing describes it as examining "the game's patterns, phases, telegraphing, and predictability" (https://thetvdb.com/series/game-makers-toolkit/episodes/6374015; subtitles hosted at https://amara.org/v/C3BEq). The transcript itself could not be retrieved here, so no verbatim quotes are given.

**Game Informer, "How Studio MDHR Builds a Cuphead Boss"** — Ben Bertoli, 27 December 2022 (https://gameinformer.com/feature/2022/12/27/how-studio-mdhr-builds-a-cuphead-boss):
- Jared Moldenhauer on a final phase: "You have to learn to dodge and aim while reducing your play space. We had that pattern down first before we had any concrete idea or layout of what exactly this stomach would look like." — the pattern came first and the art was fitted to it.
- Chad Moldenhauer on iteration: "There's tons of back and forth. There's really serendipitous times where you start building off of a concept, and every idea that comes up is perfectly linked and has this 'Aha!' moment."
- Jared on background polish: "It's only noticeable if you do a bad job and it becomes jarring."

**Critic analysis (not developer):** Barry Irick, Epilogue Gaming, 28 January 2019, argues "every attack on every boss in the game is telegraphed"; Isle One bosses teach single skills, Isle Two combines them, Isle Three adds mechanical twists; the Devil tests "all of the skills you have learned throughout the game" (https://epiloguegaming.com/cupheads-boss-design/).

Design reading: final phases shrink the play space; patterns are designed before the art; every attack is telegraphed.

---

## 4. poncle — Vampire Survivors (the Reaper, timed bosses, the chest)

**Interviews.** I found no interview in which Luca Galante explains the Reaper or the 30-minute cap; the Noclip mini-documentary ("The Making of Vampire Survivors", 2023, narrated through a Dracula puppet voiced by Galante) is the most likely place, but it is video-only (https://www.gamingonlinux.com/2023/07/check-out-the-mini-vampire-survivors-documentary/page=1/; https://80.lv/articles/vampire-survivors-developer-on-its-design-sudden-success). What text interviews do say:
- On balance, Pocket Tactics, Connor Christie, 25 October 2024: "It's absolutely not balance; balance is completely out of the window. I just want to make stuff that is fun." and "I still treat Vampire Survivors as my little project that is made for me to have fun with." (https://www.pockettactics.com/vampire-survivors/interview).
- On the chest: Wikipedia records that Galante "worked in the gambling industry" and used "his knowledge of flashy graphics for slot machines as part of the appeal for the game's chest-opening animations", citing news.com.au, 23 February 2022 (https://en.wikipedia.org/wiki/Vampire_Survivors). A quotation attributed to a Verge interview — in slot machines the player "is actually spending money every time they press it, and because of that, there's a huge attention to detail on the sounds, the animations, and the sequences, because you have so few elements to work with" — appeared only in a search summary; I could not open the Verge article (secondary).

**The Reaper (developer patch notes).** The game's own Steam announcements (Steam News API, app 1794680: https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=1794680&count=300&maxlength=0&format=json&feeds=steam_community_announcements) are the primary record:
- Road to v1.0, Day 1 (7 October 2022): the Seventh Trumpet relic "allows you to doot at The Reaper and send it away /j. It enables the Endless stage modifier, effectively allowing you to play any stage for as long as you want, without having to worry about The Reaper. The enemy waves will start over from the first one, but enemies will also grow stronger and more resistant with each cycle." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4613399405944101375).
- Patch 1.0 (20 October 2022), ENDLESS MODE: "The Reaper won't spawn at the final minute. Reaching the final minute of a stage will make the enemy waves to restart from minute 0, completing a 'cycle'. Enemies gain 100% of their base Max Health per cycle. Enemies spawn frequency and amount is increased by 50% per cycle. Enemies deal 25% more damage per cycle. The player's max damage cap is diminished by 1 per cycle. The merchant respawns on every cycle and sells '+1 Revival' instead of Golden Eggs." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4714731755412623841).
- Wikipedia summary of the default rule: "When the time limit is reached, all enemies are cleared from the stage, and a final powerful enemy named The Reaper spawns" (https://en.wikipedia.org/wiki/Vampire_Survivors).

Design reading: in Vampire Survivors the Reaper is not a fight but an *ending* — the "boss" at the cap is a run-terminator. Endless is opt-in via a relic and is expressed as cycles with flat, published multipliers.

**Timed mini-bosses carry the draft.** Patch 0.5.0 (12 April 2022): "Most Treasure Chests containing Arcanas are carried by bosses spawning at minute 11:00 and 21:00. You can carry a maximum of 3 Arcanas at the same time." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4353300134244350780). Patch 0.5.1: "Added a toggle in Stage Selection to disable Arcanas. Disabling them also disables the extra minibosses at 11:00 and 21:00" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4348797798086850885). Patch 1.11 (16 August 2024): Darkana VI "spawns an additional stage boss every minute. These bosses might carry special treasure chests, including Arcana Treasure chests..." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6909171012599282476).

This is the closest precedent for Survivor Unchained's great blessing at 15:00: poncle ties the mid-run major draft to a *boss carrying the chest*, so the blessing is earned by a kill at a fixed minute rather than simply granted.

**Bosses that must be sought out.** Ode to Castlevania (31 October 2024): "There are a lot of bosses in the Ode to Castlevania stage, but you'll have to actively seek most of them instead of waiting for the right minute for them to appear. You'll find new icons on the map to help you navigate the stage." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6146943657173896938).

**Boss crowd-control caps.** 35th Anniversary Patch (January 2022): "Tweak: capped Garlic's maximum knocback debuff for bosses" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4237325463676704990). 1.0.113: "removed Orologions from certain boss fights" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/4706851091183792873) — Orologions are the time-freeze pickups (secondary inference from the name; the patch notes do not explain why).

---

## 5. Chasing Carrots — Halls of Torment (Godot survivors-like)

**Interview.** Fullcleared, 19 September 2024 (https://fullcleared.com/features/inside-halls-of-torment-an-interview-with-chasing-carrots/): "The player should always stay in direct control of the character and be able to move in a precise manner." "We never unnecessarily impede the player's movement and hit boxes are sized in the player's favor." No boss-specific quotes in the interview. The W4 Games interview with Chasing Carrots (Godot) returned 404 when fetched (https://www.w4games.com/blog/w4-games-news-1/interview-with-chasing-carrots-developer-of-halls-of-torment-120); per a search summary the team moved from Unity to Godot and Halls of Torment was their first Godot game (secondary).

**Patch notes as boss-design record** (Steam News API, app 2218750: https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2218750&count=300&maxlength=0&format=json&feeds=steam_community_announcements):
- Playtest Update 2023-02-17: "Increased speed of Elites and Boss Monsters"; "Elites now have a blue outline while bosses have red outlines" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5059268099240713442). Colour-coded tiers to read threats in a horde.
- Update 2023-03-09: "Some bosses are substitutes for now and are slightly different versions from the first stage" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5070528810292760847).
- Update 2023-03-23: "The Flamedancer, first boss of Ember Grounds, got two new attack patterns." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5125698536879963118).
- Update 2023-08-31: "All final stage bosses have lower health but they increase in difficulty over time." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355657088929). A soft enrage expressed as escalating difficulty rather than a large HP pool.
- Update 2023-09-05, Frozen Depths bosses: "reduced trigger distance for ranged attacks to avoid player getting off-screened"; "made projectile based attack patterns of bosses less frustrating — slower movement, less dense patterns, smaller damage areas"; "increased size of hit areas (the ones that receive damage, not the ones that deal damage)" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5141476355676063710).
- Update 2023-10-30: "Monsters can now have slow resistance and limits on how slow they can be. Resistance: champion (25%), elite (50%), boss (66%), lord (80%). Limit: champion (30%), elite, boss, lord (50%)" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5229301621590571094). A published, tiered crowd-control resistance ladder.
- Update 2024-05-14 on power creep: "While it was a challenge to beat the 2nd boss in the Haunted Caverns in the early days without any meta progression, today even surviving 30 minutes isn't that difficult anymore... While we're planning to reduce the strength of certain abilities, characters, or items, this doesn't mean we want to get rid of 'OP' builds. We understand that having the possibility to create insanely powerful combinations is part of the fun" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5768625435399294703).
- HoT 1.0 (24 September 2024): "It's now more likely to find new items from Boss Chests" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6341720536520860655).

Design reading: in a horde game, boss problems are mostly *readability* problems — off-screen attacks, overly dense projectile patterns, small hurtboxes. Chasing Carrots fixed them by shortening trigger range, thinning patterns and enlarging the boss's own hurtbox.

---

## 6. Blizzard — Diablo III (Mosqueira era) and Diablo IV

**Josh Mosqueira, GDC 2015, "Against the Burning Hells: Diablo III's Road to Redemption with Reaper of Souls".** Exists; per its preview the talk covered "the evolution of core philosophy, itemization and rewards", removing the Auction House, "the evolution of randomness" and rooting out "internal design biases" (https://gamedeveloper.com/design/make-room-in-your-gdc-2015-schedule-for-these-standout-talks) (secondary — from search summary of the preview; the article page itself was not opened). No text record of boss- or Torment-specific content was found.

**BlizzCon 2013 Reaper of Souls panel** (transcript, Blizzplanet): Mosqueira introduced "brand new villain to the world of Diablo in the form of Malthael — the angel of death"; Kevin Martens on Adventure Mode: "Go anywhere, slay anything." and "Diablo is about getting awesome loot and killing monster to do that, and we have these two things in the game that weren't working well together." (https://diablo.blizzplanet.com/blog/comments/blizzcon-2013-diablo-iii-reaper-of-souls-preview-panel-transcript). The monster-design section of the same panel (designer named "Love" in the transcript) says: "In a game like Diablo, monsters really live to die. That's what they are born for."; "We have to make sure that we make things very clear and simple; and we are also looking for things that are gonna be memorable."; "We want behaviors that you can understand, okay. And we are looking for things that are going to change the way you play." (https://diablo.blizzplanet.com/blog/comments/blizzcon-2013-diablo-iii-reaper-of-souls-preview-panel-transcript/5).

**BlizzCon 2014 "Diablo III: What's Next" panel, 7 November 2014** — Wyatt Cheng on Greater Rift Guardians: "Our general philosophy on randomness is that we are not trying to treat randomness as a goal within itself but we are trying to use it as a tool to keep the replayability of Diablo III as high as possible." and "we don't want randomness to dictate your success or failure, we want it to be: 'Hey, what was my distribution?,' 'Hey, What was my rift guardian?' And your success or failure will depend on how well you change how you play to take on this guardian." (https://blizzplanet.substack.com/p/blizzcon-2014-diablo-iii-whats-next-panel-transcript).

This is directly relevant to a 30-minute timed arena that ends in a randomly selected boss: the Rift Guardian is a random end-of-timer boss, and Blizzard's stated goal was that the random pick changes *how* you play, not *whether* you can win.

**Diablo IV — stagger and immunity phases.**
- Blizzard patch 2.6.0 notes (11 March 2026): "Bosses now build Stagger approximately twice as fast as before. Stagger buildup no longer decays over time. Once you make progress toward a Stagger, it will not drain. After a boss is Staggered, they gain increased Stagger Resistance for 20 seconds. While this resistance is active, the boss is 5 times harder to Stagger." (https://news.blizzard.com/en-gb/article/24266869).
- Season 10 (Season of Infernal Chaos) lair-boss change: at 1/3 and 2/3 HP lost the boss gains a shield for 5 seconds; breaking it skips the invulnerability phase; the first shield equals 1/3 of max HP and the second 2/3; invulnerability phases cannot trigger in the first 10 seconds of the fight (https://www.icy-veins.com/d4/news/boss-invulnerability-reworked-in-diablo-4-season-10) (secondary — Icy Veins pages returned 403; seen in search summary only). The same summary gives a 30-second post-stagger cooldown, which conflicts with the 20 seconds in the later 2.6.0 notes; treat the earlier figure as unverified.
- Season 8 (April 2025): Rock, Paper, Shotgun, via Steam: "the big thing this season is its new main mechanic, boss powers" — defeating bosses grants their powers for builds (https://steamstore-a.akamaihd.net/news/externalpost/Rock,%20Paper,%20Shotgun/1797185861803308); a Season 8 Campfire Chat recap says defeating any lair boss may spawn a smaller Belial offering doubled loot (https://diablo.blizzplanet.com/blog/comments/diablo-iv-campfire-chat-ptr-2-2-0).

Design reading: Diablo IV moved from forced immunity phases (which flatten build power) to a skippable damage check (which rewards it). Hades went the other way (damage caps between phases). For a survivors-like whose fantasy is build power, the Diablo IV direction fits better.

---

## 7. Grinding Gear Games — Path of Exile and Path of Exile 2

- ExileCon 2023 talk "The Bosses and Monsters of Path of Exile 2" by game director Mark Roberts, published 21 September 2023: "Mark discusses the various aspects of boss design in Path of Exile 2, showcases some bosses from Path of Exile 2, and invites members of the audience to test their might against the bosses on stage" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5219165352625017158). Video only; no transcript found.
- Jonathan Rogers, PAX West interview with Maxroll, 3 September 2023 (https://maxroll.gg/poe/news/pax-west-path-of-exile-2-interview-with-jonathan-rogers): "I think it's important that players die early to get them used to the idea that dying is fine." / "I feel like the number of times you should die to a boss is like two times before you're able to fight it, and that's for every boss in the game. By the time you get to the end of the game you should have died like 200 times." / "One of the things we pride ourselves on is PoE2 so that the boss mechanics are all avoidable. They're all telegraphed, you can dodge, roll out of the way if you want to."
- Mark Roberts at gamescom 2024 (translated from German, Mein-MMO, 26 August 2024): PoE2 bundles "the best of what is possible in boss encounters from an action-RPG environment with Soulslike mechanics"; over 100 bosses at launch (https://mein-mmo.de/path-of-exile-2-bosse-dark-souls-vergleich-schwierigkeit/) (secondary — translated and summarised).
- PoE2 patch-note evidence (Steam News API, app 2694490):
  - "Fixed an issue where some of the Mighty Silverfist's attacks were not correctly telegraphing that they were unavoidable." — PoE2 has a distinct visual language for unavoidable attacks (The Third Edict: What We're Working On, 3 September 2025: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1809869179987885).
  - Arbiter of Divinity changes, 0.5.4b (2 July 2026): "The voicelines used by the boss are now guaranteed for his notable skills, as opposed to having a low chance to play." "The voicelines used by the boss now have less variance, so you can better correlate specific lines to specific skills." "Increased the windows of time between certain attacks and many of the combo skills to make dodge rolling these skills more consistent. This is also accompanied by a number of visual telegraphing improvements and reduction in aggression on target tracking speed." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1836506165569121). Voice lines are treated as telegraphs.
  - Upcoming Plans for 0.2.1 (21 May 2025): reducing "two of the Ritual types that were just a ruckus of purple chaos explosions and reducing the danger and increasing the telegraphing of the Volatile Plants monster modifier. Combined, these were responsible for over half of all player deaths in the endgame!" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1800357164389149). Death telemetry drove the fix.
  - 0.5.0 (22 May 2026): "All Pinnacle Bosses now have quest versions that can be accessed deterministically, alongside repeatable non-quest versions that offer a greater challenge." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1833334318572662).
- Path of Exile 1: Legacy of Phrecia event (January 2026) used "enraged bosses" and "All unique monsters will also enrage on low life" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1821922921822108). A Shacknews E6 2022 interview with Chris Wilson and Rory Rackham covers the Sentinel-era Uber bosses but the article carries no quotes (https://shacknews.com/article/130937/shacknews-e6-2022-path-of-exile-uber-boss-exilecon). A Chris Wilson ExileCon talk specifically on boss design: not found.

---

## 8. Mega Crit — Slay the Spire

- GDC 2019, Anthony Giovannetti, "'Slay the Spire': Metrics Driven Design and Balance" — exists on GDC Vault (members-only video): the team "took a metric-driven focus early in development, and continued to make heavy use of data-driven development throughout the Early Access process" (https://www.gdcvault.com/play/1025731/Slay-the-Spire-Metrics-Driven; preview dated 29 January 2019: https://www.gamedeveloper.com/design/learn-i-slay-the-spire-i-s-metrics-driven-approach-to-game-balancing-at-gdc-2019). Boss-specific statistics from the talk: not found in text.
- Early Access patch notes (Steam News API, app 646570):
  - "Boss Map Icons" listed among Early Access highlights (Slay the Spire 1.0: Farewell Early Access, 23 January 2019: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/2425653583379004051) — the act boss is shown in advance so the player can draft towards it.
  - Weekly Patch 46 (October 2018): "Experimenting with how Neow reacts to the player not reaching the boss" and a fixed set of choices "for those who don't reach the Act 1 boss (Neow's Lament or HP bonus)"; "Reptomancer has been buffed and designated as an elite monster" (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/2403126706517852502). Failing before the first boss feeds a consolation into the next run.
- Slay the Spire 2, Neowsletter May 2026: The Doormaker was removed because "while this boss provided some interesting micro-decision-making situations in his fight, he was a bit more complex than what we want." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1833334318573127).
- Composer Clark, Neowsletter February 2025: "the threat level needs to feel present as you're climbing, but when you reach the Boss, that threat level needs feel amped up. That amping up can be found in the orchestration, harmonies, tempo, and restating motifs found in the main Act music in new ways." (https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1791580425976349).

---

## 9. David Brevik — Diablo Classic Game Postmortem (GDC 2016)

- Exists: GDC Vault "Classic Game Postmortem: Diablo" (https://gdcvault.com/play/1023469/Classic-Game-Postmortem); announced 16 December 2015 as a one-hour session on how Diablo went "from a single-player, turn-based claymation DOS game to the genre-defining classic it became" (https://www.gamedeveloper.com/audio/david-brevik-will-deconstruct-i-diablo-i-in-a-gdc-2016-classic-game-postmortem); video posted May 2016 (https://www.gamedeveloper.com/design/video-i-diablo-i-a-classic-game-postmortem).
- Brevik on the switch to real time: "I just made the turns happen 20 times a second, or whatever it was, and it all just kind of worked, magically." and "I remember taking the mouse. I clicked on the mouse, and the warrior walked over and smacked the skeleton down." (https://www.pcgamer.com/uk/the-moment-the-arpg-was-born) (secondary — quotes seen in search summary; PC Gamer page body not retrievable).
- Boss-specific content (the Butcher, Diablo): not found in any text record of the talk.

---

## 10. Vlambeer — "The Art of Screenshake" (INDIGO 2013)

- Exists: Jan Willem Nijman, about 40 minutes; Kenney's list describes it as "Jan Willem Nijman (50% of Vlambeer) talks about screenshake, why is it that one game plays great and another similar one feels terrible?" (https://kenney.nl/learn/must-see-videos-for-indie-developers). Venue INDIGO Classes 2013 per search summary (secondary).
- The same toolkit in Nijman's own words, from a 2013 Rock, Paper, Shotgun interview on Nuclear Throne quoted by Tom Armitage (infovore.org, 22 October 2013): screenshake that "degenerates quickly"; enemy knockback that "adds some motion to the enemy in the bullet's direction (3 pixels per frame)"; a hit flash of "frame white, then two frames of the character looking hit"; and a freeze of "about 10-20 milliseconds whenever you hit something"; impact sounds varied by "material – meat, plant, rock or metal" (https://infovore.org/?p=5275).
- A third-party recreation of the talk lists its steps as animation, rate of fire, bigger bullets, hit pause, screenshake, player knockback and permanence (https://dkliao.itch.io/the-art-of-screenshake-recreation/devlog/451576/quick-breakdown-of-all-the-effects) (secondary — page returned 404 when fetched).

Relevance: a horde game cannot freeze 10–20 ms on every hit of hundreds of enemies; hit-stop and big shakes are best reserved for boss hits, boss phase breaks and the kill — boss feedback is where screenshake budget should go.

---

## 11. Not found / not verified

- A Game Maker's Toolkit video titled "What Makes a Good Boss Fight": not found; TheTVDB's episode list shows "How Cuphead's Bosses (Try to) Kill You" (S03E20, 19 October 2017) as the boss-specific GMTK episode, plus "What Makes a Good Combat System?" (S04E07, 27 May 2018) and "What's The Point Of Hard Games, Anyway?" (S11E09, 16 September 2025) (https://thetvdb.com/series/game-makers-toolkit/allseasons/official).
- A Greg Kasavin text interview specifically on boss design: not found. Kasavin's GDC 2021 talk "Breathing Life into Greek Myth: The Dialogue of Hades" (with Darren Korb) exists (https://gdcvault.com/play/1026975/Breathing-Life-into-Greek-Myth); it covers the 22,000+ line script and Early Access as "a huge boon for the narrative" (secondary — search summary). Noclip's six-part Hades documentary exists (https://www.thegamer.com/noclip-last-episode-behind-scenes-hades-documentary-supergiant-games/) (secondary).
- Chris Wilson ExileCon talk specifically on boss design: not found.
- Mosqueira GDC 2015 content on Torment or bosses: not found.
- Luca Galante on the Reaper's rationale: not found.

---

## Lessons for Survivor Unchained

1. **Let the 15:00 great blessing come from a kill.** Vampire Survivors puts its Arcana chests on bosses at 11:00 and 21:00 (patch 0.5.0). A mid-run elite or mini-boss at 15:00 that drops the blessing chest turns a timer event into a fight, and the chest-opening can carry the slot-machine-style payoff Galante is known for.
2. **Decide what 30:00 means.** In Vampire Survivors the Reaper ends the run; in Diablo III the Rift Guardian is the run's real test. Survivor Unchained's 30:00 boss is a *real* fight followed by endless play — so, like Wyatt Cheng's stated goal, a random boss pick should change *how* the player fights, not *whether* the build can win.
3. **Make endless legible.** poncle published flat per-cycle multipliers for endless (+100% base HP, +50% spawns, +25% damage per cycle). After the dawn boss, show the player a cycle counter and the scaling, with the ember fading as the in-world reason it must end.
4. **Reward build power at phase breaks — don't erase it.** Diablo IV moved from forced immunity phases to breakable shields; Hades caps damage between phases. For a power-fantasy horde game, take the Diablo IV approach: a short shield window that a strong build can break to skip a phase, with no immunity in the first seconds.
5. **Readability first in a horde.** Halls of Torment's fixes are a checklist: no off-screen boss attacks, thinner and slower projectile patterns, larger boss hurtboxes, distinct outline colours per tier (blue elite, red boss). PoE2 adds: a separate visual language for unavoidable attacks, guaranteed voice-line cues per signature skill, and longer gaps between combo hits.
6. **Publish a CC-resistance ladder.** Halls of Torment's slow resistance (champion 25%, elite 50%, boss 66%, lord 80%, with floors) and Vampire Survivors' boss knockback cap stop auto-fire crowd control from trivialising bosses. Pick tiers early so drafted weapons can be balanced against them.
7. **Soft enrage through escalation, not HP bloat.** Halls of Torment gave final-stage bosses "lower health but they increase in difficulty over time" — a better fit for a timer-based arena than a long, spongy health bar.
8. **Hard modifiers should be authored per boss, and the telegraph should get clearer as attacks get harder** (Hades' Extreme Measures; "telegraphs more distinctly").
9. **Let bosses remember the player.** Hades has boss dialogue on losing streaks; Slay the Spire has Neow react to failing before the first boss. The day-half ARPG story can carry this: night bosses who comment on earlier deaths, and a small consolation for the next run.
10. **Design the pattern before the art, and cut complexity that only experts enjoy.** MDHR designed the pattern before the boss's look; Mega Crit removed a boss for being "more complex than what we want".
11. **Spend the juice budget on bosses.** With hundreds of enemies on screen, hit-stop, big screenshake and white flashes should be reserved for boss hits, phase breaks and the kill (Nijman).
12. **Use death telemetry.** GGG found two hazards caused "over half of all player deaths in the endgame"; Mega Crit balanced from a metrics server. Log cause of death per boss attack from the first playtest.

---

## Verification

Adversarial check, 3 October 2026. Steam announcement URLs redirect to JS-rendered pages, so post bodies were checked against the full text in the Steam News API (GetNewsForApp, by gid) for apps 1145360, 1794680, 2218750, 2694490, 646570, 2868840 and 238960.

1. Hades EA Patch 043 (v0.27191, 24 Mar 2020): phase damage limits and losing-streak fixes. **Confirmed.** Verbatim text: "Fixed rare cases where boss damage limits between phases could be bypassed **at the start of fights**" and "Fixed some losing-streak events for certain bosses playing too **infrequently**". The body text quotes these correctly. Any shorthand ("too rarely") is a paraphrase and should not be shown in quotation marks.
2. Hades v1.0 (17 Sep 2020): Minotaur whirlwind telegraph; Extremer Measures; Final Boss Extreme Measures variant. **Confirmed** verbatim. Extra quotes in section 1 also checked and confirmed: Nighty Night (Minotaur spin attack), Patch 039 (Fury timings), Blood Price (Theseus explosive attack; Unshakable Mettle), and the v1.0 lines for Extreme Measures fourth rank and Darkness rewards.
3. Crooks Q&A (19 Apr 2016): 21 bosses, Harty/Crooks pitch, Rubel does bullet patterns, High Priest is the mastery check. **Confirmed.**
4. Jared Moldenhauer, "We had that pattern down first..." (Game Informer, 27 Dec 2022). **Confirmed** verbatim. It is about Glumstone the Giant's third phase.
5. GMTK Cuphead episode: 19 Oct 2017, 12 min, patterns/phases/telegraphing/predictability. **Confirmed** by the TheTVDB listing.
6. VS Patch 0.5.0 (12 Apr 2022): Arcana chests carried by bosses at 11:00 and 21:00. **Confirmed** verbatim.
7. VS Patch 1.0 (20 Oct 2022) endless mode. **Confirmed** verbatim. Precision note: the text says the Reaper "won't spawn **at the final minute**". It does not say the Reaper never appears in Endless.
8. Galante quote (Pocket Tactics, Connor Christie, 25 Oct 2024). **Confirmed.** The page says "Updated October 25, 2024", so the original interview may be older.
9. HoT 2023-09-05, Frozen Depths bosses. **Confirmed** verbatim. "Enlarged boss hurtboxes" correctly renders "increased size of hit areas (the ones that receive damage...)".
10. HoT 2023-10-30 slow resistance 25/50/66/80 % and limits 30/50 %. **Confirmed.**
11. HoT 2023-08-31, "All final stage bosses have lower health but they increase in difficulty over time." **Confirmed** verbatim.
12. Wyatt Cheng, BlizzCon 2014. **Confirmed.** The full sentence is: "we don't want randomness to dictate your success or failure, we want it to be: 'Hey, what was my distribution?,' 'Hey, What was my rift guardian?'" The ellipsis in the claim hides "what was my distribution?", and section 6 quotes the sentence in full.
13. Diablo IV 2.6 (11 Mar 2026) stagger changes. **Confirmed**: twice as fast, no decay, 20 s resistance, 5x harder to stagger. The Blizzard article is headed "Patch Notes (2.6)". The note's "2.6.0" is presumably the same build.
14. D4 Season 10 lair-boss shields at 1/3 and 2/3 HP lost, which skip the immunity phase. **Confirmed (secondary).** Icy Veins still returns 403. Search summaries of the same Icy Veins article and of PCGamesN (https://www.pcgamesn.com/diablo-4/patch-notes-season-10) agree on the 5 s shield, the 1/3 and 2/3 max-HP shield sizes, and the 10 s minimum before invulnerability can trigger.
15. Jonathan Rogers (Maxroll, 3 Sep 2023): die to each boss about twice; "boss mechanics are all avoidable. They're all telegraphed". **Confirmed** verbatim.
16. PoE2 0.5.4b (2 Jul 2026): voice lines guaranteed and less variable; wider windows between combo attacks. **Confirmed, with a scope correction.** All three changes apply only to the **Arbiter of Divinity** fight, not to PoE2 bosses in general. Section 7 scopes this correctly; any summary saying "bosses" should say "the Arbiter of Divinity". The same post also moves the **Arbiter of Ash** voice line to the start of its fiery-lanes skill, which is a further example of voice as telegraph.
17. GGG 0.2.1 plans (21 May 2025): Ritual types and Volatile Plants caused over half of endgame deaths. **Confirmed** verbatim. **Correction to Lessons item 12:** it says "two hazards". The source names three: two Ritual types plus the Volatile Plants modifier, "combined".
18. Mark Roberts, ExileCon 2023, "The Bosses and Monsters of Path of Exile 2". **Confirmed.** It was published 21 Sep 2023 on PoE1 app 238960 (YouTube id 5ji6yuWJnac).
19. StS2 Doormaker removal, "a bit more complex than what we want" (Neowsletter, May 2026, 23 May). **Confirmed** verbatim. The cited gid is the cross-post on Slay the Spire 1 (app 646570). A later post says "over the complexity threshold of what we want and had lingering issues". The replacement boss is Aeonglass, and Major Update #2 v0.107.1 (19 Jun 2026) shipped the removal to the main branch.
20. GDC 2019 Giovannetti "Metrics Driven Design and Balance". **Exists, but one detail is wrong.** GDC Vault currently lists it as **free** content, not members-only (https://www.gdcvault.com/play/1025731/Slay-the-Spire-Metrics-Driven). So the video is watchable, and boss-specific statistics may be recoverable from it.
21. Brevik, GDC 2016 Classic Game Postmortem: Diablo. **Confirmed** to exist.
22. Nijman (via RPS interview, quoted on infovore.org 22 Oct 2013): "degenerates quickly", knockback "3 pixels per frame", freeze "about 10-20 milliseconds whenever you hit something". **Confirmed.** These lines come from an interview, not from the "Art of Screenshake" talk itself, and section 10 attributes them that way.

Skim of the rest: also spot-checked VS 0.5.1 (arcana toggle disables the 11:00 and 21:00 minibosses), VS 1.11 Darkana VI, PoE2 0.5.0 deterministic Pinnacle quest versions, PoE2 Third Edict Silverfist telegraph, and StS Weekly Patch 46 Neow. All confirmed verbatim. Nothing implausible was found beyond the corrections above.
