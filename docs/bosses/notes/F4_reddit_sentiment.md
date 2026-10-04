> Research notes for `docs/bosses/`, kept as written. Where the **Verification** section at the end corrects a claim, the correction stands; `RESEARCH.md` uses the corrected version.

# F4 — Reddit sentiment on survivors-like bosses

Strand: what players on Reddit actually say about bosses in survivors-likes (and adjacent ARPGs and roguelites), gathered for the Survivor Unchained boss-fight design document. The game's night half (30-minute ember arenas, a great blessing at the start and at 15:00, a boss at 30:00, endless after the win, the ember fading at dawn) maps closely onto the Vampire Survivors and Halls of Torment structure, so those two communities get the most space.

## 1. Method and access notes

Reddit itself stayed unreachable from this environment by the direct routes:

- `https://old.reddit.com/r/HallsOfTorment/search.json?q=boss&restrict_sr=1&sort=top&t=all` returned HTTP 302 (redirect to a block/login wall), no JSON.
- `https://api.reddit.com/r/VampireSurvivors/search?...` and `https://www.reddit.com/r/VampireSurvivors/search.json?...` returned HTTP 403 (an HTML block page).
- PullPush (`https://api.pullpush.io/reddit/search/submission/?q=boss&subreddit=HallsOfTorment`) returned HTTP 429: "Rate limit exceeded. This website does not provide free scraping resources for agents."

**What worked:** the Arctic Shift Reddit archive API (`https://arctic-shift.photon-reddit.com/api/posts/search`, `/api/posts/ids` and `/api/comments/search?link_id=...`). It mirrors Reddit submissions and comments, scores included. Every quote below comes from that archive and is cited with the canonical reddit.com permalink so a person can check it. Its full-text *comment* search (`body=`) timed out every time, so I searched post titles by keyword over several date windows (2021 to 2026), ranked them by score and then pulled the top comments of each relevant thread.

Notation: "post 263, 41 comments" is the archived post score and comment count. "(+46)" is a comment's archived score. Scores are archive snapshots and may differ slightly from live Reddit. Quotes keep the original spelling, including American spellings and swearing.

Coverage caveats:
- r/survivorslikes and r/roguelites are dominated by developer self-promotion posts ("what do you think of my boss?"), so they hold few player-opinion threads about bosses in general.
- I found **no** Reddit thread specifically about Halls of Torment's "Lord of Regret". The titles that turned up name the Lord of Pain, Lord of Greed, Lord of Blight and Lord of Discord (search results listed under §3). Treat anything on "Regret" as not found in this strand.
- Title searches for "sponge" in the survivors subreddits returned nothing, so the "HP sponge" sentiment below comes from thread bodies and comments, plus the Diablo and Path of Exile subreddits, where the word turns up in titles.

---

## 2. Vampire Survivors: the Reaper as an "anti-boss"

The Reaper (Red Death) arrives when the 30:00 clock runs out. It is the most-discussed "boss" in the genre, even though the game does not really treat it as a boss. Reddit sentiment splits into three strands.

### 2.1 New players read it as a boss they failed against, and that confuses them

- "How do you not get absorbed and demolished by the 30:00 reaper?" (post 145, 70 comments) — the OP says: "I do fine throughout the game… But as soon as the 30:00 reaper shows up, I'm immediately swallowed up and destroyed." The top replies reframe it: "Yeah, that's how you know you've beaten the stage. The grand reward is death" (+309), and "being killed by the red Reaper is the normal way to end a run" (+195). https://www.reddit.com/r/VampireSurvivors/comments/1gti88k/how_do_you_not_get_absorbed_and_demolished_by_the/
- "Can't beat any bosses" (post 48): "once I reach 30:00 min I immediately die and then it says stage complete… I'm not even sure I've ACTUALLY completed a whole level!" Replies: "No, you won, that is the end of the level" (+62). A blunter reply (+23): "Sometimes you get so strong you are basically immortal, so the game has this boss saying 'You won, now go fuck yourself'." https://www.reddit.com/r/VampireSurvivors/comments/1dsf7qi/cant_beat_any_bosses/
- "Didn't know this could happen. Died exactly at 30:00, not to the reaper but to regular enemies. Still counts as a win." (post 356). Top reply: "Task failed successfully!" (+82). An argument follows over whether a death after 30:00 is a "win": "If you die after 30 mins you get a `stage completed` screen - that's a win" (+17). https://www.reddit.com/r/VampireSurvivors/comments/uv9zwl/didnt_know_this_could_happen_died_exactly_at_3000/
- "I didn't know you could kill the reaper that appears at the end" (post 185): "im kinda new to the game. so i though he's just a stage ender" (+30), and "Congrats. You finished the tutorial phase of the game" (+25). https://www.reddit.com/r/VampireSurvivors/comments/1rcjx54/i_didnt_know_you_could_kill_the_reaper_that/

**Read-across:** the ending works as theatre ("the grand reward is death"), but it keeps producing confused "how do I beat this?" threads, year after year. The game never says clearly that the timer was the win condition.

### 2.2 Killing the Reaper is a later goal, and players hate how "HP sponge" it is

- "So.... The Reaper is killable right?" (post 236). Top answer (+137): "his health is multiplied by your level. His base HP is 655,350. At level 114, his HP is 74,709,900. So... Yeah, but it's gonna take a bit." Another (+15): "Just a reaper spawning every minute with over half a billion HP, no big deal." https://www.reddit.com/r/VampireSurvivors/comments/1hamjls/so_the_reaper_is_killable_right/
- "Is it impossible to kill a Grim Reaper without special items?" (post 161, 65 comments). Top reply (+135): "Unless I can kill them immediately I just quit, it's such a waste of time." Someone works through the maths (+77): at level 65 and an assumed 5,000 DPS, "it will take you… 2 hours and 15 mins to kill the first reaper." Others (+27, +26): "without either of the super weapons it won't end the level, nor it will drop golden eggs. So it's pointless to do, just quit"; "They drop nothing… there is no reason to try and kill one without the stage items." https://www.reddit.com/r/VampireSurvivors/comments/1gpbduf/is_it_impossible_to_kill_a_grim_reaper_without/
- "How do you get past the 30 minutes in reaper boss?" (post 17): "the reaper has super speed and stun locks me". Replies point to the unlock chain (Clock Lancet, Laurel, the Yellow Sign): "Treat it as the end of the round until you get far enough in the game progression… this game is much deeper than it first appears" (+15). https://www.reddit.com/r/VampireSurvivors/comments/1hekbo5/how_do_you_get_past_the_30_minutes_in_reaper_boss/
- A 2024 thread on the Ode to Castlevania DLC asks whether you must beat the Reaper twice (post 169, 54 comments): https://www.reddit.com/r/VampireSurvivors/comments/1g9gyvu/confused_you_have_to_beat_the_reaper_twice/ (title only; I did not read the comments).

**Read-across:** players accept a *scripted* run-ender. What they resent is a fight that *can* be won but pays nothing and costs hours. The level-scaled HP is called "a waste of time", "pointless", "just quit".

### 2.3 Killing it, when you finally can, is a celebrated milestone

There are plenty of high-scoring "finally" posts: "I just killed Reaper for the first time with Flower-Farting Dog" (post 203) https://www.reddit.com/r/VampireSurvivors/comments/16ij0kp/i_just_killed_reaper_for_the_first_time_with/ ; "Finally beat my first reaper today!" (post 114) https://www.reddit.com/r/VampireSurvivors/comments/1hqc7yk/finally_beat_my_first_reaper_today/ ; "I FINALLY KILLED THE REAPER" (post 105) https://www.reddit.com/r/VampireSurvivors/comments/1q5yz7s/i_finally_killed_the_reaper/ ; "Killed the reaper for the first time" (post 146) https://www.reddit.com/r/VampireSurvivors/comments/1weff46/killed_the_reaper_for_the_first_time/ . On the 2026 "didn't know you could kill" thread, one commenter says: "To me, this is the point opens up the 'end game'" (+29). https://www.reddit.com/r/VampireSurvivors/comments/1rcjx54/i_didnt_know_you_could_kill_the_reaper_that/

The community also treats the Reaper as an icon. "I drew The Reaper" (post 380) and several Red Death linocut-print posts score 800+ (e.g. post 868: https://www.reddit.com/r/VampireSurvivors/comments/1wkp47y/red_death_vampire_survivors_inspired/). A single, distinctive end-of-night figure has become the game's mascot of dread.

### 2.4 The mid-run "stalker" Reapers

Some stages have roaming Reapers or "Stalkers". These draw more anger than the 30:00 one. "I hate this reaper so much" (post 263): "This guy has ruined so many gallo tower and capella magna runs." Replies explain the counters, which are a map element (the Rosary) or killing the stage's crab. One pushback (+23) says it isn't a fair skill test: "So it's a skill issue when new players don't know map elements? What a cringe response." Another (+45) simply says: "The green one is worse." https://www.reddit.com/r/VampireSurvivors/comments/1bogo4b/i_hate_this_reaper_so_much/

**Read-across:** a hunter that can't be harmed mid-run, with an answer hidden on the map, reads as unfair unless the counter is taught.

### 2.5 Other Vampire Survivors boss points

- **Death spectacle wanted:** "More bosses should explode spectacularly when defeated" (post 89). "I really dig that many of the Castlevania bosses have flashy death animations and even unique sounds for when you land the killing blow, clueing you in that a chest just apppeared amongst the carnage… just having a little chime play anytime a chest is dropped would make me happy." The top reply pushes back (+50): "How many more animations do you want on the screen at once". https://www.reddit.com/r/VampireSurvivors/comments/1gk6j2w/more_bosses_should_explode_spectacularly_when/
- **Boss triggers lost under weapon effects:** "Suggestion: Make boss summoning circles always visible over weapon effects" (post 59): "It's kind of crazy you have to grope around all those weapon effects until you hit the circle!" A reply (+23) says the developers had flagged an update looking at "options to reduce weapon effects". (I have not checked that claim against a primary developer source.) https://www.reddit.com/r/VampireSurvivors/comments/1pa72vi/suggestion_make_boss_summoning_circles_always/
- **Visual saturation is a running joke:** "I can't see anything" (post 222; top reply "You are doing it right!" +48) https://www.reddit.com/r/VampireSurvivors/comments/1p92dcw/i_cant_see_anything/ ; "Limit Break, Phieraggi Only, AKA 'I Can't See Shit'" (post 264) https://www.reddit.com/r/VampireSurvivors/comments/vtngp0/limit_break_phieraggi_only_aka_i_cant_see_shit/ . In Vampire Survivors this is treated as *fun*, because by 30:00 there is no telegraphed boss to read.
- **Performance as the real final boss:** "Unable to beat this boss, shows up at the end of a run" (post 225) is a joke about a phone overheating; replies (+58) suggest an "ice bath" https://www.reddit.com/r/VampireSurvivors/comments/1mypg4r/unable_to_beat_this_boss_shows_up_at_the_end_of_a/ . Also "The final boss was the framerate all along" (post 18) https://www.reddit.com/r/VampireSurvivors/comments/1qb4bu3/the_final_boss_was_the_framerate_all_along/ .
- **Boss rush wanted:** "It's time they put in a new boss rush mode" (post 31): "a cool bonus map to unlock after defeating each boss of the CV map at least once" (+4). https://www.reddit.com/r/VampireSurvivors/comments/1gkeby5/its_time_they_put_in_a_new_boss_rush_mode/
- **Endless after the win:** "playing endless for the first time and now I'm asking myself how am I gonna die if nothing can get close to me" (post 138). Top answers: "you pause and quit when you get bored" (+109) and "That's the neat part! You don't!" (+62). https://www.reddit.com/r/VampireSurvivors/comments/1ay5m11/playing_endless_for_the_first_time_and_now_im/ . A related post: "Wanted to try and kill the reaper, hit 30 minutes, then realized I was on endless. So I let it go for 15 hours" (post 113). https://www.reddit.com/r/VampireSurvivors/comments/1d3d0gb/wanted_to_try_and_kill_the_reaper_hit_30_minutes/

---

## 3. Halls of Torment: Lords, DPS checks and early-access tuning

The subreddit (r/hallsoftorment) is small: top boss threads score in the 10s to 50s. It is still the closest match to Survivor Unchained's tone (dark fantasy, Diablo-flavoured) and to its structure (a timed or kill-count boss at the end of a hall).

### 3.1 Bosses started as "braindead health sponges" and were reworked

The most useful comment in this strand comes from "First boss is imbalanced" (2023, early access). It was a low-scoring comment, but it explains the history:

> "The first boss is imbalanced because it was the first and only boss they focused on updating. It was initially just a braindead health sponge exactly like Ember Grounds, then they went through several patches of changing it to reduce the health, increase the bosses damage output/general lethality, add the purple crystal quest, and other improvements." (+1) https://www.reddit.com/r/hallsoftorment/comments/14hxtis/first_boss_is_imbalanced/

In the same thread another player criticises the two-phase structure: "it has two phases, no other boss does… the first phase is significantly harder than the second one! Never seen this before… the necromancer fight changes nothing in the identity or the pace of the fight. It's just a prolongation, a chore since this the second phase is not at all threatening." Another player recalls a harsher version: "The first boss used to hit you with a curse timer which meant you had to kill him in 40 seconds and then again in the second form!" The top reply (+6) is "sounds like a skill issue, once you have enough movement speed… it really isnt a difficult fight." https://www.reddit.com/r/hallsoftorment/comments/14hxtis/first_boss_is_imbalanced/

**Read-across:** the HP sponge was the *starting point*, and the developers patched it into "less HP, more lethality, plus a map quest that weakens the boss". Players also notice when a second phase is just more of the first, and easier.

### 3.2 The curse timer: a DPS check players find tense but fair once explained

The Haunted Caverns boss ("the dog", the first Lord) puts a death curse on the player:

- "the final boss hits me with that curse and I'm dead in 40 seconds!" Replies explain: "It's a DPS check, get him down to half health and the timer starts over", and "If you get enough move speed, you can actually kite the curse." Revives can be spent to survive the instant deaths. The OP later reports: "I've now managed to out DPS the first phase with cleric, which reset the timer". https://www.reddit.com/r/hallsoftorment/comments/13z96e0/seriously_fun_game_any_tips_on_beating_the_final/
- "Any tips on killing final boss (dog) on Haunted Caverns?": "If you manage to eat through his first life bar before the countdown timer is up, it resets", and "Warrior with crit and kill him within 30 sec :) After that, you have to kill the knight within the next 30 sec too." https://www.reddit.com/r/hallsoftorment/comments/13r7t6r/any_tips_on_killing_final_boss_dog_on_haunted/

### 3.3 The map-quest "boss breaker" is popular

Several threads point newcomers to the blood-trail / purple-crystal quest. Each fragment comes from killing things inside a ring, and the combined trinket nukes the boss's first phase:

- "follow those blood trails… kill stuff in the ring(s)… when you have both it will kill the bosses first phase… and spawn the 2nd phase which is easier." (+6) https://www.reddit.com/r/hallsoftorment/comments/14xueey/the_first_maps_boss_is_the_hardest/
- "do the altars and get the two purple crystals… pick [the +100% damage buff] up right before the boss spawns. the crystal nuke will deal double damage and leave the boss with almost no HP." (+5) https://www.reddit.com/r/hallsoftorment/comments/14hxtis/first_boss_is_imbalanced/
- "Have you collected both purple fragments… as they make killing the boss easier." https://www.reddit.com/r/hallsoftorment/comments/195nsf1/question_about_lord_of_pain/

**Read-across:** players enjoy earning a boss shortcut *during the run* through exploration. It turns the 30-minute horde phase into preparation for the boss.

### 3.4 Movement speed is the counter-stat players name

Across threads the advice is the same: "Your best defence is movement speed. You really don't need block, parry or defence stat" (+4, Archer thread) https://www.reddit.com/r/hallsoftorment/comments/15au7c6/any_tips_on_archer_for_closing_out_the_boss/ ; "Movement speed is very important to dodge this boss's attacks" (Lord of Pain thread) https://www.reddit.com/r/hallsoftorment/comments/195nsf1/question_about_lord_of_pain/ ; "Just get some movement speed and you're fine" https://www.reddit.com/r/hallsoftorment/comments/14xueey/the_first_maps_boss_is_the_hardest/ . The Archer thread also describes a horde build failing the boss: "builds which wipe big hordes easily… but I find in the boss fight I just don't wipe him fast enough to make up for my general lack of evasiveness". https://www.reddit.com/r/hallsoftorment/comments/15au7c6/any_tips_on_archer_for_closing_out_the_boss/

### 3.5 Unreadable one-shots and bugs drive the angriest threads

- "Ember Grounds: I keep getting oneshot instant killed at 18 minutes left" (post 20, 26 comments): "the purple waves… once they traveled a certain distance they become dark green/black and will just one shot you… they are very hard to see when they turn black." (A later patch fixed the bug, per replies.) https://www.reddit.com/r/hallsoftorment/comments/1be6pp1/ember_grounds_i_keep_getting_oneshot_instant/
- "Help with Lord Of Greed" (post 10): after an update the boss "barely takes any damage… projectiles and abilities seem to pass right through him"; "the boss is bugged… I spent around 70k gold for this fight". A reply says a developer on Discord was "investigating the hitbox" (secondary, a Reddit report of a Discord comment). https://www.reddit.com/r/hallsoftorment/comments/1ijag8y/help_with_lord_of_greed/
- Console crash threads cluster around boss fights: "New update on Xbox doesn't fix crashes on lord of pain fight" (post 8, 12 comments). https://www.reddit.com/r/hallsoftorment/comments/1ovboqb/new_update_on_xbox_doesnt_fix_crashes_on_lord_of/

### 3.6 Kill-count spawns versus clock spawns

The Lord of Blight achievement ("defeat in under 18 minutes") shows the boss in one hall spawning on a kill counter rather than a clock: "Boglands, boss spawn in at 20k kills." Players chase spawn-rate traits to bring it forward. (Kill threshold as reported by a player; not verified against the wiki.) https://www.reddit.com/r/hallsoftorment/comments/1ooswix/defeat_the_lord_of_blight_in_under_18_min/

### 3.7 Victory posts

The victory posts are small but warm: "Finally killed Lord of Pain on Agony xD… Probably the most fun i've had in the game on this run :D" (post 11) https://www.reddit.com/r/hallsoftorment/comments/196gzcg/finally_killed_lord_of_pain_on_agony_xd/ ; "My first run ever! Could've been legendary... Died to giant dog boss" (post 12) https://www.reddit.com/r/hallsoftorment/comments/196k3wi/my_first_run_ever_couldve_been_legendary_died_to/ ; and the evocative "Just started playing 2 days ago, almost 4am, can hardly sleep, finally hit 30 minutes on Haunted Caverns, got the boss t[o]…" https://www.reddit.com/r/hallsoftorment/comments/14wo1cc/just_started_playing_2_days_ago_almost_4am_can/ . A related loss post: "The final boss killed me and I lost my fancy sparkle gloves and elven boots :(" https://www.reddit.com/r/hallsoftorment/comments/15gkzpg/i_cant_believe_i_made_it_this_far_warrior_on_the/

### 3.8 Music

The one thread asking for "more epic, intense, and fast paced" music (post 1) was roundly rejected: "it's spooky and intense, perfect vibe" (+9); "The music gives me Diablo vibes — the original Diablo… evocative and atmospheric" (+6). Several players said they mute it and play their own playlist (+6). https://www.reddit.com/r/hallsoftorment/comments/1hnb1ip/anyone_else_wish_the_music_was_more_epic_intense/

---

## 4. Other survivors-likes

### 4.1 Brotato: the wave-20 boss as a one-shot gear check

- "So frustrated… This seemed like a perfect game then ONE-SHOTTED by the boss??" (post 44, 45 comments). The replies are all build diagnosis: "Super low armor and health" (+60); "You're spreading yourself way too thin" (+34); "start getting some health and armor when you're getting close to wave 20" (+34 comment). https://www.reddit.com/r/brotato/comments/1kbegvg/so_frustrated_what_am_i_doing_wrong_here_this/
- Near-misses are brutal: "FUCK YOU FUCK YOU LAST BOSS WAS 2 HP I'VE BEEN AWAKE ALL NIGHT" (post 135). The top reply is "(turn retries on)" (+40), followed by a debate on whether retries are "easy mode" (+6). https://www.reddit.com/r/brotato/comments/1vbarng/fuck_you_fuck_you_last_boss_was_2_hp_ive_been/
- "just got my first danger 5 clear. killed the boss with 1 second left lol" (post 56) https://www.reddit.com/r/brotato/comments/1bxklev/just_got_my_first_danger_5_clear_killed_the_boss/
- Platform-specific boss bugs breed resentment: "Tell me again how struggling w/the Eel boss's attack on mobile is a skill issue" (post 23); reply: "Its a skill issue. However not player skill, its a mobile dev skill issue" (+23). https://www.reddit.com/r/brotato/comments/1lt0nm3/tell_me_again_how_struggling_wthe_eel_bosss/
- Boss kills as a showcase genre: "11 sec boss kill (D5 Soldier)" (post 41) https://www.reddit.com/r/brotato/comments/zzc0n5/11_sec_boss_kill_d5_soldier/

### 4.2 HoloCure: time-to-kill as a bragging metric

- "has anyone even beat a 20 minute boss in less than 10 seconds" (post 262, 86 comments) — replies list nuke builds: "Akirose can 1 shot any boss lol" (+165); "unleash the dance bop on the unfortunate boss" (+90). https://www.reddit.com/r/holocure/comments/11m5pff/okay_but_seriously_has_anyone_even_beat_a_20/
- "decided to save up belly dancing for whole level to 1 shot boss. Worth it." (post 167) https://www.reddit.com/r/holocure/comments/13bfnsh/decided_to_save_up_belly_dancing_for_whole_level/
- Players want *more* boss content: "Imagine Kay releases a game mode where you can challenge a raid boss with massive HP, numerous attack moves/patterns, and waves of enemies sent at you" (post 394, 66 comments). https://www.reddit.com/r/holocure/comments/18pz9vr/imagine_kay_releases_a_game_mode_where_you_can/

**Read-across:** a build that has spent 30 minutes charging up a single "deletion" moment is part of the fantasy. Bosses should be deletable by a committed build, and the fight should still have shape when the build is weaker.

### 4.3 Deep Rock Galactic: Survivor: the escape timer after the boss

- "Absolutely love the game by the 30 second timer when you beat the boss is so annoying" (post 23): "you end up unintentionally killing the boss while running around… having to immediately stop what you're doing and sprinting to the drill." The top-voted design critique (+10): "If you don't kill the boss, there is no timer… It doesn't make sense that the timer suddenly appears… Will make actually killing the boss the optimal play." A counterpoint (+3): "It's intentional, that you make a frantic loot-grab then escape at the last second." https://www.reddit.com/r/DRGSurvivor/comments/1atv8q9/absolutely_love_the_game_by_the_30_second_timer/
- "The Boss Never Came" (post 28): the boss got stuck off-screen behind terrain. "When I had it happen to me I found the boss… caught between terrain and the edge of the map." https://www.reddit.com/r/DRGSurvivor/comments/1b0f9vs/the_boss_never_came/
- "I wish they'd fix no movement. I've had multiple runs fail to the boss getting stuck across…" (post 18) https://www.reddit.com/r/DRGSurvivor/comments/1f1vuk9/i_wish_theyd_fix_no_movement_ive_had_multiple/

### 4.4 Soulstone Survivors: the single-target trap and lingering hazards

- "Titan Hunt 2… This fight went on for almost 10 minutes of me tickling the boss to death… Despite me dealing millions and billions worth of damage, I was somehow also not doing enough damage???" Top reply (+13): "Billions of Damage, Millions of Multitarget DPS, and very low Single Target DPS." https://www.reddit.com/r/SoulstoneSurvivors/comments/1lnlt48/titan_hunt_2_difficulty_this_fight_went_on_for/
- "The aoe lasting effects on the bosses should go away after a while": "the floor quickly ends up covered in damage and I can't stand anywhere at all… the bosses can get crazy tanky so I end up dead from tick damage". One reply defends it as anti-AFK design: "having the aoe makes players move more which is what the devs intended. I think the aoe time needs reducing though heavily." https://www.reddit.com/r/SoulstoneSurvivors/comments/1kjkbuu/the_aoe_lasting_effects_on_the_bosses_should_go/
- A boss that is "not something you're meant to beat" in the first scripted run confused at least one player: "Got rekt by the first final boss then everything else is super easy, did I miss something?" https://www.reddit.com/r/SoulstoneSurvivors/comments/1muncix/got_rekt_by_the_first_final_boss_then_everything/
- Players liked a boss whose reward reshapes builds: "I kinda like the new boss" (post 35), about Titan buffs. https://www.reddit.com/r/SoulstoneSurvivors/comments/1m5tz7u/i_kinda_like_the_new_boss/

### 4.5 Visual clarity across the genre

On "Grind Survivors — the visual clarity leaves something to be desired" (r/survivorslikes): "I feel as if an effect transparency slider is critical for these kinds of games. HOT, Soulstone Survivors, and Boneraiser spoiled me" (+6). Another reply: "Halls of torment has a slider in the options that allows you to add transparency to your own effects… Soulstone survivors has two buttons you can use to adjust effect transparency live during gameplay". https://www.reddit.com/r/survivorslikes/comments/1s01sfm/grind_survivors_the_game_is_fun_but_the_visual/

### 4.6 Developer-facing threads on r/survivorslikes

- Players welcome big set-piece bosses: "a neat spin on the survivors formula by adding some truly massive encounters and not simply more waves of popcorn enemies" (on a boss that scrolls past the screen). https://www.reddit.com/r/survivorslikes/comments/1rq87k9/when_the_boss_enters_the_screen_and_just_keeps/
- On a "soulslike bosses" survivors demo (Ember and Blade, post 93, 74 comments), a player complains that the counter tool is gated: "the parry/counter ability is a tier two unlock despite it being a vital ability for fighting the boss." https://www.reddit.com/r/survivorslikes/comments/1o85rye/what_if_vampire_survivors_had_dynasty_warriors/
- Making the boss round feel distinct: a dev lists "an animated intro" and "New music for the boss"; the one reply suggests "a name… for the boss… give them a name to refer to when talking about it." https://www.reddit.com/r/survivorslikes/comments/1tnjzyj/trying_to_make_the_boss_fight_round_more/
- Win condition versus endless (Mycofall dev poll, post 32, 28 comments): "I like win conditions but I also love endless modes… you have an end (wave 20 bosses in brotato / endboss in night swarm) and then you can decide if you want to continue in endless" (+19); "Generally I like a win condition just so I can have that feeling of accomplishment. Endless modes are fun but the choice is 'keep going or die' which isn't very motivating… Night Swarm… beat a boss, receive your achievement reward, and have the option to either return to the hub or start an endless round" (+14); and a dissent: "Endless is kinda ass. It generally funnels you to very specific builds and scaling vectors" (+2). https://www.reddit.com/r/survivorslikes/comments/1u5mjpr/do_you_prefer_endless_or_wincondition_mode_in/

---

## 5. Adjacent genres: ARPG and roguelite boss sentiment

### 5.1 Diablo IV: sponges, unreadable one-shots, death retaliation

- "I do hope Diablo 5 avoids the quadrillion health boss design" (post 263, 152 comments): "Surely… Blizzard can come up with better ways to make bosses 'hard' than by simply ramping up their health?" Replies: "Especially when they can still hit you during phasing but you can't do anything to them" (+48); "the immunity phases... God damn it's annoying" (+7); "They made a whole raid with boss mechanics other than 'one shot' and it has been collectively forgotten" (+7). https://www.reddit.com/r/diablo4/comments/1wom6xe/i_do_hope_diablo_5_avoids_the_quadrillion_health/
- "Stop artificially escalating boss damage at the last moments of the fight!" (post 164): "Increase the mechanics at-play in the final stages… that's great… But don't suddenly have the boss one-shotting you at 10% of their health remaining". Top replies: "killed him and he had those stupid red balls of death that shot off when he died and I couldn't even see where I was because he's so big" (+87); "I'm really tired of the post death retaliation mechanic that so many devs seem to love" (+74). https://www.reddit.com/r/diablo4/comments/1vg3xjy/stop_artificially_escalating_boss_damage_at_the/
- "Many of my deaths in this game confuse me, where is the telegraph that I am about to be oneshot" (post 77): "a grey tornado on a grey platform" (+30); "one shots are fine if it's some sort of omega attack. One shot from a stard enemy atk… terrible design" (+15). https://www.reddit.com/r/diablo4/comments/1cv6ah8/many_of_my_deaths_in_this_game_confuse_me_where/
- "Every boss fight is a damage sponge slog" (post 13), with pushback that gear was the issue. One reply accepts the trade-off: "Groups die instantly though so i dont mind having a longer fight with a boss." https://www.reddit.com/r/diablo4/comments/140mcli/every_boss_fight_is_a_damage_sponge_slog/

### 5.2 Path of Exile (1 and 2): telegraphs and clarity

- "For a move that does this much damage and sucks you in, it needs a better telegraph." (post 1,667, 270 comments). Comments: "All bosses in PoE 2 are like that. Kill it as fast as possible so he doesnt attack you" (+3), and on the campaign/endgame contrast: "during campaign… Nearly all felt very rewarding because they felt epic, I had to learn mechanics… It does not feel like that in endgame anymore… I want to melt them" (+6). https://www.reddit.com/r/pathofexile/comments/1hgg640/for_a_move_that_does_this_much_damage_and_sucks/
- "GGG please give T17 bosses better visual clarity" (post 141): "Standing still and dying to air, scuffed hitboxes, invisible degens… Lycia's big red slam has bigger hitbox than the sprite"; reply "there is no visual clarity in endgame" (+38). https://www.reddit.com/r/pathofexile/comments/1bxiekp/ggg_please_give_t17_bosses_better_visual_clarity/
- "Map design and visual clarity" (post 1,462) https://www.reddit.com/r/pathofexile/comments/1hk51na/map_design_and_visual_clarity/ (title only).
- An act-one sponge complaint ("Merveil act 1 is a tedious time consuming boring damage sponge") was downvoted to 0. Defenders argued that "GGG wants players to actually interact with the boss mechanics so the encounters are memorable instead of… one shotting some slightly bigger than normal monster" (+6). https://www.reddit.com/r/pathofexile/comments/rk2aae/merveil_act_1_is_a_tedious_time_consuming_boring/

### 5.3 Hades / Hades II: readable patterns and distinct wind-ups

- "I feel that Hades II's [REDACTED] fight is good, but… I wish he would telegraph his attacks more" (post 124): the scythe throw "hasn't done for like 3 minutes… I thought he was going to swipe at me and dodged right into the scythe." Top reply (+162): "If they just made his startup animations more distinct so you could more easily tell what attack he's about to do he'd be perfect. The scythe throw in particular is too hard to read for an attack that hits like a truck." Counterpoint (+11): "spend a run just watching his telegraphs… The way he pulls back the scythe before throwing it is distinct". https://www.reddit.com/r/HadesTheGame/comments/1ctr3bj/i_feel_that_hades_iis_redacted_fight_is_good_but/
- "Is it me or is charon the hardest boss?" (post 158): "I find him really easy to read personally, he just kinda...repeats himself" (+47); "mostly he's hard because he's pretty different than the other boss fights and you don't encounter him too often" (+29). https://www.reddit.com/r/HadesTheGame/comments/1jwu1nb/is_it_me_or_is_charon_the_hardest_boss/
- Damage caps on boss shields are felt as a hidden rule: "the real hardest part of these boss shields are the damage caps" (post 9). https://www.reddit.com/r/HadesTheGame/comments/1ok7d9c/the_real_hardest_part_of_these_boss_shields_are/

### 5.4 Risk of Rain 2

Mithrix (the final boss) is beloved as a character. Meme and lore threads score 2,000 to 3,500, for example "mithrix phase 4" (post 2,663) https://www.reddit.com/r/riskofrain/comments/ymb72j/mithrix_phase_4/ . A stage-boss difficulty tier list (post 1,330) notes one boss is "sometimes impossible to do in time if he spawns in an open area and you have no mobility" (+5). https://www.reddit.com/r/riskofrain/comments/1g8s7p8/have_now_reached_500_hours_heres_my_current_tier/ . "Captain losing half his abilities in a boss fight is terrible." (post 766) https://www.reddit.com/r/riskofrain/comments/tchthz/captain_losing_half_his_abilities_in_a_boss_fight/ (title only). The complaint is about a boss arena that removes a character's toolkit.

---

## 6. Cross-cutting themes (synthesis)

1. **"The end of the night" and "the boss" must not be confused.** Vampire Survivors' 30:00 Reaper is iconic, but it produces endless "how do I beat this?" threads (§2.1). Survivor Unchained has a *real, beatable* boss at 30:00 plus endless afterwards, so it needs the win to be unmistakable. The run-ending threat (the dawn fade) should be framed as something else entirely.
2. **HP sponges are the most-cited complaint, and the fix players praise is "less HP, more lethality, more interaction"** (Halls of Torment's rework, §3.1; Diablo "quadrillion health", §5.1). Level-scaled HP with no reward is called "a waste of time" (§2.2).
3. **Horde builds fail single-target checks, and players don't understand why** (Soulstone "billions of damage", the HoT Archer, §3.4, §4.4). The game needs to signal single-target power before 30:00.
4. **Telegraphs must survive the player's own effects.** Boss circles lost under weapon effects, black waves on dark floors, grey tornadoes on grey ground, invisible degens (§2.5, §3.5, §5.1, §5.2). An effect-transparency option is now an expected feature (§4.5).
5. **One-shots are accepted only as rare, clearly signalled "omega" attacks** (§5.1). Late-fight damage escalation and death-retaliation explosions are actively hated (§5.1).
6. **Distinct wind-ups beat raw difficulty.** Hades players forgive hard bosses that are readable and hate attacks that share a start-up with weaker ones (§5.3).
7. **In-run preparation for the boss is loved** (HoT purple-crystal quest, §3.3). It ties the 30 minutes of horde play to the fight.
8. **Deletion moments are part of the power fantasy** (HoloCure belly-dance one-shots, Brotato 11-second kills, §4.1–4.2). Bosses must allow them for committed builds without becoming trivial for everyone.
9. **Post-boss pressure needs to make sense** (DRG Survivor's 30-second timer, §4.3). Players want a choice after the win: leave with the reward, or continue into endless (§4.6).
10. **Bugs and performance at the boss moment are disproportionately damaging.** Invulnerable Lord of Greed, bosses stuck off-screen, console crashes on boss fights, phone overheating, frame-rate collapse (§2.5, §3.5, §4.3). The boss is the moment people post about.
11. **Spectacle and naming matter.** Death explosions and chimes are requested (§2.5), boss names help players talk about the fight (§4.6), and the Reaper's single iconic silhouette became fan-art fodder (§2.3). Players in the dark-fantasy community defended atmospheric music over "epic" music (§3.8).

---

## 7. Lessons for Survivor Unchained

1. **Make the 30:00 victory unmistakable.** Show a distinct "Ember Lord falls" beat: a death animation, a unique sound, a chime for loot and a clear "Night won" banner. Then offer a choice: *bank and leave* or *stay into endless*. Never let the dawn fade read as "the boss beat you". This avoids Vampire Survivors' perennial "did I win?" confusion.
2. **Cap boss HP so a good build can kill it in minutes, and build difficulty from attack patterns, not HP.** Don't scale boss HP with player level the way the Reaper does, and never put a beatable-but-pointless fight in the game. If an endless "dawn hunter" exists, make it obviously a run-ender, or reward killing it.
3. **Give a readable timer or DPS check, with a visible reset rule** (Halls of Torment's curse: "get him down to half health and the timer starts over"). State the rule in the UI the first time.
4. **Seed boss-prep objectives in the 0:00–30:00 horde phase.** Map shrines or ember fragments that weaken or reveal the boss, modelled on HoT's blood-trail crystals. The 15:00 great blessing is a natural place to offer a "boss-slayer" option, which also teaches single-target value before 30:00.
5. **Protect boss telegraphs from player VFX.** Draw boss wind-ups and ground warnings on a top layer above weapon effects, with high contrast against the dark-fantasy palette (no black-on-dark waves). Ship an effect-opacity slider from day one.
6. **Give every attack a distinct start-up pose and sound.** One-shot attacks only as rare "omega" moves with a long, unique warning. No hidden damage ramps near low HP, and no surprise death-retaliation bursts, or at least telegraph them heavily.
7. **Don't make phase two just a longer, easier phase one.** Each phase should change the fight's identity, or be cut.
8. **Allow "deletion" for committed builds, but give the fight shape when builds are weaker.** Celebrate fast kills (a time-to-kill stat on the victory screen) rather than nerfing them away.
9. **Don't gate the core boss counter behind deep meta-unlocks** (the Ember and Blade parry complaint). Movement and dash should be enough to learn the fight on the first night.
10. **Test the boss moment hardest on low-end hardware and consoles.** Cap enemy and particle counts during the boss, and make sure the boss can never get stuck off-screen. This moment generates the screenshots, the clips and the bug reports.
11. **Name the boss, give it a silhouette and an entrance.** Bosses with distinct identities become community icons (the Reaper, Mithrix). For music, the dark-fantasy audience preferred atmospheric dread to generic "epic", so a boss theme can intensify the arena's palette rather than switch genre.
12. **Keep post-boss timers generous or optional.** DRG Survivor's 30-second scramble shows that a sudden countdown after the kill feels unfair.

## Verification

Adversarial re-check on 2026-10-03. Each endpoint was re-queried. Post scores and comment counts come from Arctic Shift `/api/posts/ids`. Comment scores and text come from `/api/comments/search?link_id=...`. Scores are archive snapshots.

1. Access notes: **confirmed**. On re-test, old.reddit.com .json returned 302, api.reddit.com and www.reddit.com .json returned 403 (an HTML page), and PullPush returned 429 with the quoted message ("...does not provide free scraping resources for agents. Please contact the administrator on Discord..."). Arctic Shift returned 200.
2. VS 30:00 reaper thread (post 145, 70 comments; top reply +309, quoted verbatim): **confirmed**.
3. Reaper HP 655,350 × level, 74,709,900 at level 114 (+137): **confirmed** as a player report, and the arithmetic checks out. One caveat: a lower reply in the same thread (+9) says "65535*your level", so players do not all agree. https://www.reddit.com/r/VampireSurvivors/comments/1hamjls/so_the_reaper_is_killable_right/
4. "such a waste of time" (+135); no eggs and the level does not end (+27); "They drop nothing" (+26): **confirmed**.
5. HoT first-boss rework and "a chore": **confirmed** (both quotes are verbatim). Caveat: both comments score only +1, and the post scores 4, so they carry little weight as sentiment. The rework comment also says the devs had not yet applied these changes to bosses 2 and 3.
6. "It's a DPS check, get him down to half health and the timer starts over": **confirmed** (verbatim, +1, low weight).
7. Ember Grounds black/green waves that one-shot players: **confirmed** (+2). Later replies say an update fixed it ("I closed the game, had an update queued and bug was fixed!"). One player had already called it a likely bug.
8. Boss summoning circles suggestion (post 59, 4 comments): **confirmed**. The top reply (+23) says the next update will look at options to reduce weapon effects.
9. Explode-spectacularly post (89 points; the body asks for a chest-drop chime) and top reply (+50) "How many more animations do you want on the screen at once": **confirmed**.
10. DRG Survivor 30-second timer (post 23, 9 comments): **confirmed**. The +10 reply says that removing the timer would "make actually killing the boss the optimal play", which implies that the current timer makes not killing it optimal. The note paraphrases this rather than quoting it.
11. Soulstone "Billions of Damage... very low Single Target DPS" (+13): **confirmed**. Note: the OP's title says "almost 10 minutes", but a later reply mentions "87 minutes" for a different context.
12. Transparency slider "critical" citing HoT and Soulstone: **confirmed with a nuance**. Only one user (+6) uses the word "critical". Two others (+2 each) describe the HoT and Soulstone transparency options. "Users call it critical" overstates this slightly.
13. Endless vs win-condition (+19 Brotato/Night Swarm, +14 Night Swarm): **confirmed**.
14. Diablo IV: "quadrillion health" (post 263, 152 comments) and the escalating-damage post (164, 43 comments; replies +87 and +74): **confirmed**. The OP quote elides "for Goodness sakes", and the ellipsis marks this. https://www.reddit.com/r/diablo4/comments/1wom6xe/i_do_hope_diablo_5_avoids_the_quadrillion_health/
15. PoE "needs a better telegraph" (1,667 points, 270 comments): **confirmed**.
16. Hades II Chronos telegraphs (+162, verbatim): **confirmed**. Caveat: the post itself scores 124. Another reply (+11) says the scythe pull-back is distinct "it just takes learning".
17. HoT music (+9, +6): **confirmed with a nuance**. The post scores 1. Another +6 reply would welcome a DLC "that makes it more epic", so the request was not rejected outright.
18. HoloCure 20-minute boss thread (post 262, 86 comments): **confirmed**. Top replies: Baelz (+191) and Akirose one-shots (+165).

Skim of the remaining citations: all 71 cited post IDs resolve in Arctic Shift. Every post score and comment count spot-checked matched, including 1bogo4b (263, 41) and 1wom6xe (263, 152). The extracted ID list also contained a stray "search" token from a non-post URL fragment, but no citation is affected. No claims were found to be refuted.
