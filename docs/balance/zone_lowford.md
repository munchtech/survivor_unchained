# The Low Ford: zone sim (M5-F)

**Today's self-firing bots; the pressing bots are M3's.** The real Prologue zone through HeadlessHost, from the Wake to the gate: the night's placed beats, the Barrow Knight, the Grave-Caller, the Ford-Warden (the films fall back to their captions headless), the dawn and the day stretch. Falls go through the zone's own OnDeath (the rise at her last lamp-post). A warden (calling) on her first weapon, no gear worn beyond the Watch Chest's jerkin (left in the pack: the bots do not dress).

Command: `dotnet run -c Release --project godot/balance -- zone --zone lowford --bots human,careless,deft,plain,standing --seeds 8 --tier 2 --also 1:human+deft --out docs/balance/zone_lowford.md`

Films: C01 11.8 s, C02 19.9 s, C03 23.1 s, C04A 13.5 s (godot/data/cinematics/*.json, the shots' "dur" summed; C04 B plays in the Waystation, not here); **68.3 s** added to each run for the with-films hour. Play-only time is the sim's seconds less the headless fallbacks that stand in for C02 and C03 (the Intro and Victory stages).

Kills are hers (fodder / elite / champion / boss). Packs: night and day beats put down (pack, ambush, ring). Gear: ground drops (all of it rolled: carriers, champions, the strongbox, the Warden), by tier; shown = not Hidden by the Default preset (LootFilter.Judge with the toggles on; first sightings not counted). Upgrade: a drop better than the best of its slot so far (Drops.Power over the worn piece by the upgrade margin), not worn. Fighting: a roused foe within 24 m.

## Per bot (medians; worst case in brackets)

| Tier | Bot | Runs | Through | Minutes play (worst) | Minutes with films | Kills f/e/c/b | Packs | Champions | Falls (worst) | Rises | Gear C/U/R/E/Set+L | Shown | Upgrades | Gold (taken / fell) | Lv Warden / gate (lowest) | Meters | Fighting % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| II | human | 8 | 8 | 5.3 (6.1) | 6.5 | 139/5/5/1 | 16 | 5 | 0 (0) | 0 | 2/3/4/0/1 | 10 | 5 | 15 / 165 | 3 / 5 (4) | 1049 | 39 |
| II | careless | 8 | 7 | 5.2 (8.3) | 6.3 | 142/5/5/1 | 16 | 5 | 0 (1) | 0 | 4/2/4/0/1 | 11 | 6 | 15 / 195 | 3 / 5 (4) | 996 | 40 |
| II | deft | 8 | 8 | 5.5 (8.4) | 6.7 | 138/5/5/1 | 16 | 5 | 0 (0) | 0 | 3/3/3/0/1 | 10 | 6 | 15 / 156 | 3 / 5 (4) | 1072 | 41 |
| II | plain | 8 | 8 | 5.5 (5.8) | 6.6 | 133/5/5/1 | 16 | 5 | 0 (1) | 0 | 3/2/4/1/1 | 11 | 6 | 15 / 169 | 3 / 5 (4) | 1092 | 42 |
| II | standing | 8 | 8 | 6.0 (8.8) | 7.1 | 144/5/4/1 | 16 | 4 | 3 (8) | 3 | 5/2/3/1/1 | 10 | 5 | 15 / 187 | 3 / 5 (4) | 733 | 46 |
| I | human | 8 | 8 | 5.3 (5.9) | 6.4 | 142/5/5/1 | 16 | 5 | 0 (0) | 0 | 2/3/3/0/1 | 10 | 6 | 15 / 170 | 3 / 5 (4) | 980 | 40 |
| I | deft | 8 | 8 | 5.1 (5.5) | 6.2 | 136/5/5/1 | 16 | 5 | 0 (0) | 0 | 2/3/4/1/1 | 9 | 6 | 15 / 189 | 3 / 4 (4) | 996 | 39 |

## The presses (M3; medians, presses and damage shares averaged over the runs)

| group | runs | mark gap in fights from 0:45 (s, med / worst) | Resolve spent /min | Resolve at max % | presses /min | damage shares % | Flare casts / first (s) / share % / boss share % | falls (where) |
|---|---|---|---|---|---|---|---|---|
| T2 human | 8 | 32 / 37 | 413 | 5 | groundbreaker 7.9, heroic_leap 0.2 | groundbreaker 37, sunder 32, oathblade 22, heroic_leap 4, flare 4, dash 0 | 2 / 136 / 4 / 15 |  |
| T2 careless | 8 | 27 / 39 | 421 | 6 | groundbreaker 7.5, heroic_leap 0.2 | groundbreaker 39, sunder 33, oathblade 22, flare 3, heroic_leap 3, dash 0 | 1 / 162 / 3 / 10 | Exit@(25,-88) by pillager x1; Post@(12,36) by risen x1 |
| T2 deft | 8 | 36 / 200 | 400 | 0 | groundbreaker 9.3, heroic_leap 0.3 | groundbreaker 41, sunder 30, oathblade 20, heroic_leap 6, flare 3, dash 0 | 2 / 143 / 3 / 13 |  |
| T2 plain | 8 | 31 / 43 | 282 | 29 |  | sunder 44, oathblade 29, groundbreaker 22, flare 5, dash 0 | 2 / 139 / 5 / 23 | Post@(19,38) by risen x1 |
| T2 standing | 8 | 37 / 77 | 303 | 29 |  | sunder 46, oathblade 28, groundbreaker 21, flare 5 | 2 / 134 / 5 / 20 | Exit@(38,-87) by pillager x2; Exit@(2,-102) by wolf x2; Post@(14,38) by risen x1; Post@(8,36) by risen x1 |
| T1 human | 8 | 35 / 47 | 401 | 4 | groundbreaker 8.1, heroic_leap 0.2 | sunder 35, groundbreaker 33, oathblade 25, heroic_leap 4, flare 3, dash 0 | 2 / 140 / 3 / 10 |  |
| T1 deft | 8 | 27 / 36 | 393 | 0 | groundbreaker 9.2, heroic_leap 0.3 | groundbreaker 35, sunder 34, oathblade 21, heroic_leap 6, flare 3, dash 0 | 2 / 134 / 4 / 15 |  |

## Per hour (medians of each run's rate; play-only / with films)

| Tier | Bot | Kills/hr | Packs/hr | Champions/hr | Gear shown/hr | Minutes per upgrade | Rises/hr |
|---|---|---|---|---|---|---|---|
| II | human | 1680 / 1385 | 180 / 148 | 56 / 46 | 110 / 91 | 1.1 / 1.4 | 0 / 0 |
| II | careless | 1702 / 1402 | 180 / 149 | 58 / 47 | 125 / 103 | 0.9 / 1.1 | 0 / 0 |
| II | deft | 1596 / 1327 | 173 / 143 | 53 / 44 | 108 / 90 | 1.0 / 1.1 | 0 / 0 |
| II | plain | 1577 / 1304 | 169 / 140 | 55 / 45 | 116 / 96 | 0.9 / 1.1 | 0 / 0 |
| II | standing | 1513 / 1278 | 159 / 133 | 40 / 34 | 98 / 82 | 1.1 / 1.4 | 25 / 21 |
| I | human | 1703 / 1396 | 183 / 150 | 57 / 47 | 109 / 89 | 0.9 / 1.1 | 0 / 0 |
| I | deft | 1747 / 1419 | 184 / 150 | 59 / 48 | 107 / 87 | 0.9 / 1.1 | 0 / 0 |

## Against ARPG.md 7.1's first hour (tier II, the human bot, per hour with films)

| | Target | Measured (per hour) | In this zone (one run) | Verdict |
|---|---|---|---|---|
| Kills | ~500 | 1385 | 150 | over |
| Packs (each with a captain) | ~40 | 148 | 16 | over |
| Champions | 4-6 | 46.1 | 5 | over |
| Gear shown (Default filter) | ~25 | 91 | 10 | over |
| An upgrade worth wearing | every ~8 min | every 1.4 min | 5 | more often |
| The Legendary | 1, certain, from the Ford-Warden | 8/8 runs | Warden's ground gear: 1 | on |
| Levels | 1-5 in the hour | gate level 5 | | on |

The Warden's drops, all tier II runs: Legendary drowned_coat x42.

## The campaign gates (7.1, tier II)

| Gate | Measured | Verdict |
|---|---|---|
| The human rises 1-3 an hour | 0.0/hr (median; runs 0,0,0,0,0,0,0,0) | fail |
| The deft at most once an hour | 0.0/hr (worst run 0.0) | pass |
| The standing bot falls to every champion pack | falls 4,8,5,2,1,3,2,1; fell at the Post 3/8, the Barrow 0/8, by day 7/8 | fail (5 champions: a fall each needs 5+) |
| Levels within ±20% (level 5 by the hour's end) | gate level 5 | pass |
| Drops within ±20% (~25 shown an hour) | 91/hr | fail |
| (kills within ±20%, ~500 an hour) | 1385/hr | fail |

**Read the rates with the zone's length:** the whole Low Ford plays in about 6.5 minutes (with films), so every per-hour rate is that run scaled by about 9.3x. One rise in a run reads as 9.3 an hour, so the rise gates cannot pass or fail fairly until the first hour is an hour of ground (see The ground). Per run, the totals (kills, packs, champions, gear, level 5 at the gate) are the numbers to set against the table's first hour: today's zone gives the first hour's levels and champions in an eighth of its time, and about a third of its kills, packs and gear.

Gold: the bots take only what they walk over (the coins are not pulled to her by day); the column gives what she took and what fell.

## The ground

- The route (the goals' walk: the camp, the night's 10 beats, the ford; the day's start, its 8 beats, the gate): **148 m by night + 208 m by day = 356 m**. (The meta's ROAD path, the camp to the ford: 262 m.)
- Walked by the human bot (tier II median), fights' footwork included: 513 m by night, 503 m by day, 1016 m in all (2.9x the route).
- Packs placed: 10 by night, 6 by day, 16 in all: **4.5 packs per 100 m of route** (6.7 by night, 2.9 by day).
- The first hour's ~40 packs at today's density: **889 m** of route (+534 m, +24 packs more than today).
- The zone at about 45 minutes: today it plays in 6.5 min with films (55 m of route a minute, everything in it). At today's pace and density, 45 minutes is **2471 m** of route (6.9x today, +2116 m more), holding **111 packs** (+95 more).
- So ~40 packs fill about 16 minutes at today's pace; the extra minutes to 45 are walking, films, towns' worth of story, or denser fights (bigger packs, more per beat).

## Seconds per beat (median; woke to down) and her level at its fall (median)

| Beat | II human | II careless | II deft | II plain | II standing | I human | I deft |
|---|---|---|---|---|---|---|---|
| n_lone | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 |
| n_three | 0 s, L1 | 1 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 |
| n_first | 3 s, L1 | 3 s, L1 | 2 s, L1 | 4 s, L1 | 3 s, L1 | 3 s, L1 | 2 s, L1 |
| n_cart | 9 s, L2 | 9 s, L2 | 9 s, L2 | 10 s, L2 | 11 s, L2 | 9 s, L2 | 8 s, L2 |
| n_road1 | 1 s, L2 | 2 s, L2 | 2 s, L2 | 3 s, L2 | 3 s, L2 | 2 s, L2 | 1 s, L2 |
| n_road2 | 2 s, L2 | 2 s, L2 | 2 s, L2 | 2 s, L2 | 3 s, L2 | 2 s, L2 | 1 s, L2 |
| n_post | 3 s, L2 | 3 s, L2 | 3 s, L2 | 4 s, L2 | 2 s, L2 | 3 s, L2 | 1 s, L2 |
| n_road3 | 3 s, L3 | 1 s, L3 | 3 s, L3 | 4 s, L3 | 2 s, L3 | 1 s, L2 | 1 s, L2 |
| n_road4 | 2 s, L3 | 2 s, L3 | 1 s, L3 | 2 s, L3 | 3 s, L3 | 1 s, L3 | 1 s, L3 |
| n_ford | 3 s, L3 | 2 s, L3 | 3 s, L3 | 4 s, L3 | 3 s, L3 | 5 s, L3 | 2 s, L3 |
| boars | 14 s, L4 | 13 s, L4 | 12 s, L4 | 15 s, L4 | 17 s, L4 | 14 s, L4 | 12 s, L4 |
| kerchiefs | 22 s, L4 | 24 s, L4 | 29 s, L4 | 24 s, L4 | 27 s, L4 | 18 s, L4 | 24 s, L4 |
| road_ambush | 5 s, L4 | 7 s, L4 | 9 s, L4 | 7 s, L4 | 8 s, L4 | 5 s, L4 | 7 s, L4 |
| wallow | 15 s, L4 | 19 s, L4 | 15 s, L4 | 22 s, L4 | 20 s, L4 | 18 s, L4 | 15 s, L4 |
| track_ambush | 6 s, L4 | 7 s, L4 | 8 s, L4 | 9 s, L4 | 9 s, L4 | 7 s, L4 | 6 s, L4 |
| wolves | 5 s, L4 | 4 s, L4 | 4 s, L4 | 5 s, L4 | 4 s, L4 | 4 s, L4 | 4 s, L4 |
| stage Wake | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s |
| stage Rising | 3 s | 3 s | 3 s | 3 s | 2 s | 3 s | 3 s |
| stage Road | 2 s | 2 s | 2 s | 2 s | 2 s | 2 s | 2 s |
| stage Ambush | 14 s | 14 s | 15 s | 16 s | 18 s | 15 s | 14 s |
| stage Road2 | 5 s | 7 s | 8 s | 8 s | 9 s | 9 s | 5 s |
| stage Post | 43 s | 38 s | 45 s | 48 s | 35 s | 38 s | 41 s |
| stage Barrow | 40 s | 41 s | 40 s | 44 s | 39 s | 41 s | 39 s |
| stage ToFord | 13 s | 12 s | 14 s | 10 s | 14 s | 17 s | 8 s |
| stage Intro | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s |
| stage Boss | 62 s | 61 s | 61 s | 62 s | 69 s | 62 s | 61 s |
| stage Victory | 39 s | 39 s | 39 s | 39 s | 39 s | 39 s | 39 s |
| stage Dawn | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s |
| stage Exit | 119 s | 117 s | 127 s | 123 s | 150 s | 110 s | 112 s |

## Quiet between beats (median seconds from the previous beat's down to this beat's wake; negative = woke before the last fell)

| Beat (after the one before it in the data) | II human | II careless | II deft | II plain | II standing | I human | I deft |
|---|---|---|---|---|---|---|---|
| n_three (after n_lone) | 5.0 s (6) | 5.0 s (7) | 5.0 s (6) | 5.0 s (6) | 4.1 s (8) | 5.0 s (5) | 5.0 s (5) |
| n_first (after n_three) | 7.0 s (8) | 7.1 s (8) | 7.2 s (8) | 7.2 s (8) | 6.1 s (8) | 6.3 s (8) | 6.6 s (8) |
| n_cart (after n_first) | -1.1 s (8) | -2.2 s (8) | -1.9 s (8) | -4.5 s (8) | 0.0 s (8) | 0.0 s (8) | -0.5 s (8) |
| n_road1 (after n_cart) | 4.6 s (7) | 4.3 s (8) | 4.1 s (7) | 4.3 s (7) | 4.1 s (8) | 5.2 s (7) | 4.1 s (6) |
| n_road2 (after n_road1) | 4.9 s (8) | 4.7 s (8) | 4.3 s (8) | 5.0 s (8) | 4.1 s (8) | 4.5 s (8) | 4.3 s (8) |
| n_post (after n_road2) | 4.3 s (8) | 4.5 s (7) | 4.4 s (8) | 5.1 s (8) | 4.5 s (7) | 4.3 s (7) | 4.3 s (5) |
| n_road3 (after n_post) | 26.7 s (8) | 26.3 s (8) | 30.0 s (8) | 34.0 s (6) | 20.7 s (8) | 26.7 s (7) | 30.8 s (6) |
| n_road4 (after n_road3) | 4.3 s (8) | 4.7 s (8) | 5.0 s (8) | 5.0 s (8) | 4.1 s (8) | 4.7 s (8) | 5.0 s (8) |
| n_ford (after n_road4) | 40.8 s (7) | 41.3 s (6) | 41.7 s (7) | 41.9 s (4) | 41.9 s (8) | 43.0 s (8) | 43.7 s (4) |
| boars (after n_ford) | 124.6 s (7) | 121.8 s (5) | 123.4 s (7) | 126.3 s (4) | 124.3 s (8) | 119.9 s (8) | 124.1 s (4) |
| kerchiefs (after boars) | 6.3 s (8) | 6.3 s (7) | 6.2 s (8) | 6.0 s (8) | 6.7 s (8) | 6.5 s (8) | 6.7 s (8) |
| road_ambush (after kerchiefs) | 4.0 s (8) | 5.0 s (7) | 4.7 s (8) | 5.1 s (8) | 6.3 s (6) | 3.9 s (8) | 4.3 s (8) |
| wallow (after road_ambush) | 13.0 s (8) | 11.6 s (7) | 11.7 s (8) | 12.1 s (8) | 10.6 s (6) | 12.6 s (8) | 13.0 s (8) |
| track_ambush (after wallow) | 3.2 s (8) | 3.5 s (7) | 2.8 s (8) | 2.8 s (8) | 2.8 s (8) | 3.7 s (8) | 3.7 s (8) |
| wolves (after track_ambush) | 6.4 s (8) | 7.0 s (7) | 6.6 s (8) | 5.3 s (8) | 5.9 s (8) | 5.8 s (8) | 6.8 s (8) |

Pack wakes while a champion (not its own pack's, nor the Knight at its own escort) lived within 25 m of her and was **awake** (the count that matters): II human: 0 in 8 runs; II careless: 0 in 8 runs; II deft: 0 in 8 runs; II plain: 0 in 8 runs; II standing: 0 in 8 runs; I human: 0 in 8 runs; I deft: 0 in 8 runs.

The same counting a champion that is still resting (the Knight asleep at the post 12 m from n_road2, for one): II human: 17; II careless: 17; II deft: 18; II plain: 15; II standing: 14; I human: 15; I deft: 17.

## Falls, rises and runs that did not get through

- II human: falls by stage: none; risen at: none.
- II careless: falls by stage: Exit 1, Post 1; risen at: lowford.bank 1, checkpoint 1.
  - s6: stuck: Exit beat boars at (17,-34) goal (12,-37) (after 9.0 min)
- II deft: falls by stage: none; risen at: none.
- II plain: falls by stage: Post 1; risen at: checkpoint 1.
- II standing: falls by stage: Post 5, Exit 19, Boss 2; risen at: checkpoint 5, act1.post1 15, lowford.door 2, lowford.bank 4.
- I human: falls by stage: none; risen at: none.
- I deft: falls by stage: none; risen at: none.
