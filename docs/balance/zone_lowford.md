# The Low Ford: zone sim (M5-F)

**Today's self-firing bots; the pressing bots are M3's.** The real Prologue zone through HeadlessHost, from the Wake to the gate: the night's placed beats, the Barrow Knight, the Grave-Caller, the Ford-Warden (the films fall back to their captions headless), the dawn and the day stretch. Falls go through the zone's own OnDeath (the rise at her last lamp-post). A warden (calling) on her first weapon, no gear worn beyond the Watch Chest's jerkin (left in the pack: the bots do not dress).

Command: `dotnet run -c Release --project godot/balance -- zone --zone lowford --bots human,careless,deft,plain,standing --seeds 8 --tier 2 --also 1:human+deft --out docs/balance/zone_lowford.md`

Films: C01 11.8 s, C02 19.9 s, C03 23.1 s, C04A 13.5 s (godot/data/cinematics/*.json, the shots' "dur" summed; C04 B plays in the Waystation, not here); **68.3 s** added to each run for the with-films hour. Play-only time is the sim's seconds less the headless fallbacks that stand in for C02 and C03 (the Intro and Victory stages).

Kills are hers (fodder / elite / champion / boss). Packs: night and day beats put down (pack, ambush, ring). Gear: ground drops (all of it rolled: carriers, champions, the strongbox, the Warden), by tier; shown = not Hidden by the Default preset (LootFilter.Judge with the toggles on; first sightings not counted). Upgrade: a drop better than the best of its slot so far (Drops.Power over the worn piece by the upgrade margin), not worn. Fighting: a roused foe within 24 m.

## Per bot (medians; worst case in brackets)

| Tier | Bot | Runs | Through | Minutes play (worst) | Minutes with films | Kills f/e/c/b | Packs | Champions | Falls (worst) | Rises | Gear C/U/R/E/Set+L | Shown | Upgrades | Gold (taken / fell) | Lv Warden / gate (lowest) | Meters | Fighting % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| II | human | 8 | 8 | 7.6 (8.3) | 8.8 | 176/5/4/1 | 16 | 4 | 1 (1) | 1 | 3/2/3/0/1 | 10 | 6 | 15 / 194 | 3 / 5 (5) | 1913 | 36 |
| II | careless | 8 | 7 | 7.4 (10.8) | 8.5 | 158/5/5/1 | 16 | 5 | 0 (1) | 0 | 2/3/4/0/1 | 10 | 6 | 15 / 176 | 3 / 5 (4) | 1865 | 36 |
| II | deft | 8 | 7 | 8.1 (9.8) | 9.2 | 160/5/5/1 | 16 | 5 | 0 (1) | 0 | 2/3/3/1/1 | 10 | 6 | 15 / 178 | 3 / 5 (4) | 1854 | 41 |
| II | plain | 8 | 8 | 7.0 (8.0) | 8.1 | 175/5/5/1 | 16 | 5 | 0 (1) | 0 | 2/3/4/0/1 | 9 | 6 | 15 / 197 | 3 / 5 (5) | 1793 | 39 |
| II | standing | 8 | 8 | 5.6 (6.1) | 6.7 | 152/5/5/1 | 16 | 5 | 0 (1) | 0 | 2/2/2/1/1 | 9 | 5 | 15 / 154 | 3 / 5 (4) | 730 | 41 |
| I | human | 8 | 8 | 6.8 (8.1) | 7.9 | 165/5/5/1 | 16 | 5 | 0 (0) | 0 | 2/3/4/1/1 | 10 | 5 | 15 / 189 | 3 / 5 (5) | 1735 | 36 |
| I | deft | 8 | 8 | 7.0 (7.6) | 8.1 | 162/5/5/1 | 16 | 5 | 0 (0) | 0 | 2/3/3/0/1 | 9 | 6 | 15 / 178 | 3 / 5 (5) | 1768 | 36 |

## Per hour (medians of each run's rate; play-only / with films)

| Tier | Bot | Kills/hr | Packs/hr | Champions/hr | Gear shown/hr | Minutes per upgrade | Rises/hr |
|---|---|---|---|---|---|---|---|
| II | human | 1530 / 1323 | 126 / 110 | 34 / 29 | 78 / 68 | 1.4 / 1.6 | 4 / 3 |
| II | careless | 1459 / 1269 | 130 / 113 | 41 / 35 | 77 / 67 | 1.2 / 1.4 | 0 / 0 |
| II | deft | 1355 / 1182 | 119 / 104 | 35 / 30 | 75 / 65 | 1.4 / 1.6 | 0 / 0 |
| II | plain | 1602 / 1375 | 139 / 119 | 39 / 34 | 77 / 68 | 1.2 / 1.4 | 0 / 0 |
| II | standing | 1698 / 1420 | 170 / 141 | 53 / 44 | 92 / 77 | 1.2 / 1.4 | 0 / 0 |
| I | human | 1581 / 1354 | 142 / 122 | 44 / 37 | 88 / 75 | 1.4 / 1.6 | 0 / 0 |
| I | deft | 1475 / 1268 | 138 / 119 | 42 / 36 | 74 / 64 | 1.3 / 1.5 | 0 / 0 |

## Against ARPG.md 7.1's first hour (tier II, the human bot, per hour with films)

| | Target | Measured (per hour) | In this zone (one run) | Verdict |
|---|---|---|---|---|
| Kills | ~500 | 1323 | 187 | over |
| Packs (each with a captain) | ~40 | 110 | 16 | over |
| Champions | 4-6 | 29.0 | 4 | over |
| Gear shown (Default filter) | ~25 | 68 | 10 | over |
| An upgrade worth wearing | every ~8 min | every 1.6 min | 6 | more often |
| The Legendary | 1, certain, from the Ford-Warden | 8/8 runs | Warden's ground gear: 2 | on |
| Levels | 1-5 in the hour | gate level 5 | | on |

The Warden's drops, all tier II runs: Legendary drowned_coat x40, Common silver_ring x3, Uncommon travelers_cloak x3, Rare worn_oathblade x3, Uncommon copper_ring x2, Uncommon silver_ring x2, Rare judgement_disc_item x2, Common padded_jerkin x2, Rare copper_ring x2, Common copper_ring x2, Common travelers_cloak x2, Epic watch_buckler x1, Rare silver_ring x1, Uncommon padded_jerkin x1, Rare iron_helm x1, Rare leather_cap x1, Uncommon worn_oathblade x1, Rare padded_jerkin x1, Uncommon chain_shirt x1, Common chain_shirt x1, Common watch_buckler x1, Rare travelers_cloak x1, Common worn_oathblade x1, Uncommon bone_amulet x1, Common hunting_bow x1, Common iron_helm x1, Uncommon iron_helm x1, Uncommon leather_cap x1.

## The campaign gates (7.1, tier II)

| Gate | Measured | Verdict |
|---|---|---|
| The human rises 1-3 an hour | 3.2/hr (median; runs 0,1,0,0,0,1,1,1) | fail |
| The deft at most once an hour | 0.0/hr (worst run 7.2) | pass on the median |
| The standing bot falls to every champion pack | falls 1,0,0,0,0,1,0,0; fell at the Post 0/8, the Barrow 0/8, by day 2/8 | fail (5 champions: a fall each needs 5+) |
| Levels within ±20% (level 5 by the hour's end) | gate level 5 | pass |
| Drops within ±20% (~25 shown an hour) | 68/hr | fail |
| (kills within ±20%, ~500 an hour) | 1323/hr | fail |

**Read the rates with the zone's length:** the whole Low Ford plays in about 8.8 minutes (with films), so every per-hour rate is that run scaled by about 6.9x. One rise in a run reads as 6.9 an hour, so the rise gates cannot pass or fail fairly until the first hour is an hour of ground (see The ground). Per run, the totals (kills, packs, champions, gear, level 5 at the gate) are the numbers to set against the table's first hour: today's zone gives the first hour's levels and champions in an eighth of its time, and about a third of its kills, packs and gear.

Gold: the bots take only what they walk over (the coins are not pulled to her by day); the column gives what she took and what fell.

## The ground

- The route (the goals' walk: the camp, the night's 10 beats, the ford; the day's start, its 8 beats, the gate): **148 m by night + 213 m by day = 361 m**. (The meta's ROAD path, the camp to the ford: 262 m.)
- Walked by the human bot (tier II median), fights' footwork included: 1246 m by night, 686 m by day, 1932 m in all (5.4x the route).
- Packs placed: 10 by night, 6 by day, 16 in all: **4.4 packs per 100 m of route** (6.7 by night, 2.8 by day).
- The first hour's ~40 packs at today's density: **902 m** of route (+541 m, +24 packs more than today).
- The zone at about 45 minutes: today it plays in 8.8 min with films (41 m of route a minute, everything in it). At today's pace and density, 45 minutes is **1854 m** of route (5.1x today, +1493 m more), holding **82 packs** (+66 more).
- So ~40 packs fill about 22 minutes at today's pace; the extra minutes to 45 are walking, films, towns' worth of story, or denser fights (bigger packs, more per beat).

## Seconds per beat (median; woke to down) and her level at its fall (median)

| Beat | II human | II careless | II deft | II plain | II standing | I human | I deft |
|---|---|---|---|---|---|---|---|
| n_lone | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 |
| n_three | 1 s, L1 | 1 s, L1 | 1 s, L1 | 1 s, L1 | 0 s, L1 | 1 s, L1 | 1 s, L1 |
| n_first | 3 s, L1 | 3 s, L1 | 3 s, L1 | 3 s, L1 | 3 s, L1 | 2 s, L1 | 2 s, L1 |
| n_cart | 13 s, L2 | 13 s, L2 | 12 s, L2 | 13 s, L2 | 11 s, L2 | 13 s, L2 | 10 s, L2 |
| n_road1 | 5 s, L2 | 5 s, L2 | 4 s, L2 | 5 s, L2 | 4 s, L2 | 3 s, L2 | 3 s, L2 |
| n_road2 | 5 s, L2 | 5 s, L2 | 5 s, L2 | 5 s, L2 | 4 s, L2 | 3 s, L2 | 3 s, L2 |
| n_post | 4 s, L2 | 4 s, L2 | 4 s, L2 | 4 s, L2 | 3 s, L2 | 3 s, L2 | 4 s, L2 |
| n_road3 | 4 s, L3 | 5 s, L3 | 4 s, L3 | 3 s, L3 | 0 s, L3 | 3 s, L3 | 4 s, L3 |
| n_road4 | 4 s, L3 | 4 s, L3 | 5 s, L3 | 5 s, L3 | 3 s, L3 | 3 s, L3 | 3 s, L3 |
| n_ford | 0 s, L3 | 0 s, L3 | 0 s, L3 | 0 s, L3 | 4 s, L3 | 2 s, L3 | 0 s, L3 |
| boars | 14 s, L4 | 16 s, L4 | 15 s, L4 | 16 s, L4 | 13 s, L4 | 14 s, L4 | 14 s, L4 |
| kerchiefs | 35 s, L4 | 32 s, L4 | 53 s, L4 | 33 s, L4 | 30 s, L4 | 24 s, L4 | 41 s, L4 |
| road_ambush | 5 s, L4 | 6 s, L4 | 6 s, L4 | 5 s, L4 | 5 s, L4 | 5 s, L4 | 5 s, L4 |
| wallow | 22 s, L4 | 22 s, L4 | 21 s, L4 | 21 s, L4 | 19 s, L4 | 20 s, L4 | 21 s, L4 |
| track_ambush | 8 s, L5 | 8 s, L4 | 9 s, L4 | 7 s, L5 | 7 s, L4 | 7 s, L4 | 7 s, L4 |
| wolves | 0 s, L5 | 0 s, L5 | 0 s, L5 | 0 s, L5 | 0 s, L5 | 0 s, L5 | 0 s, L5 |
| stage Wake | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s |
| stage Rising | 3 s | 3 s | 3 s | 3 s | 2 s | 3 s | 3 s |
| stage Road | 2 s | 2 s | 2 s | 2 s | 2 s | 2 s | 2 s |
| stage Ambush | 21 s | 21 s | 20 s | 21 s | 18 s | 20 s | 17 s |
| stage Road2 | 9 s | 9 s | 5 s | 9 s | 11 s | 8 s | 7 s |
| stage Post | 40 s | 42 s | 44 s | 42 s | 32 s | 37 s | 35 s |
| stage Barrow | 45 s | 44 s | 45 s | 46 s | 38 s | 44 s | 43 s |
| stage ToFord | 9 s | 9 s | 9 s | 11 s | 12 s | 11 s | 10 s |
| stage Intro | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s |
| stage Boss | 161 s | 157 s | 146 s | 142 s | 84 s | 152 s | 153 s |
| stage Victory | 19 s | 19 s | 19 s | 19 s | 19 s | 19 s | 19 s |
| stage Dawn | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s |
| stage Exit | 131 s | 127 s | 160 s | 129 s | 120 s | 114 s | 127 s |

## Quiet between beats (median seconds from the previous beat's down to this beat's wake; negative = woke before the last fell)

| Beat (after the one before it in the data) | II human | II careless | II deft | II plain | II standing | I human | I deft |
|---|---|---|---|---|---|---|---|
| n_three (after n_lone) | 4.0 s (8) | 4.0 s (8) | 4.0 s (8) | 4.0 s (8) | 4.2 s (3) | 4.0 s (8) | 4.0 s (8) |
| n_first (after n_three) | 6.1 s (8) | 6.1 s (8) | 6.1 s (8) | 6.1 s (8) | 6.1 s (8) | 6.1 s (8) | 6.1 s (8) |
| n_cart (after n_first) | 0.0 s (8) | 0.0 s (8) | 0.0 s (8) | 0.0 s (8) | 0.0 s (8) | 0.0 s (8) | 0.0 s (8) |
| n_road1 (after n_cart) | 4.0 s (8) | 4.0 s (8) | 4.0 s (8) | 4.0 s (8) | 4.2 s (8) | 4.0 s (8) | 4.0 s (8) |
| n_road2 (after n_road1) | 4.0 s (8) | 4.0 s (8) | 4.0 s (8) | 4.0 s (8) | 4.1 s (8) | 4.0 s (8) | 4.1 s (8) |
| n_post (after n_road2) | 4.7 s (8) | 4.7 s (8) | 5.0 s (8) | 4.7 s (8) | 4.5 s (8) | 4.3 s (8) | 4.3 s (8) |
| n_road3 (after n_post) | 20.2 s (8) | 21.6 s (8) | 25.5 s (8) | 19.4 s (7) | 17.2 s (4) | 20.2 s (8) | 17.1 s (8) |
| n_road4 (after n_road3) | 4.1 s (8) | 4.0 s (8) | 4.1 s (8) | 4.1 s (8) | 4.1 s (8) | 4.1 s (8) | 4.0 s (8) |
| n_ford (after n_road4) | 37.7 s (6) | 38.1 s (8) | 37.6 s (5) | 37.9 s (8) | 40.2 s (5) | 38.7 s (8) | 37.4 s (6) |
| boars (after n_ford) | 203.7 s (8) | 193.7 s (6) | 179.9 s (7) | 183.6 s (8) | 109.5 s (5) | 190.4 s (8) | 188.5 s (7) |
| kerchiefs (after boars) | 6.9 s (8) | 6.8 s (7) | 5.9 s (7) | 6.5 s (8) | 6.4 s (8) | 5.7 s (8) | 6.7 s (8) |
| road_ambush (after kerchiefs) | 4.0 s (8) | 3.0 s (7) | 2.6 s (7) | 2.5 s (8) | 6.5 s (6) | 3.7 s (8) | 4.5 s (8) |
| wallow (after road_ambush) | 12.6 s (8) | 11.7 s (7) | 11.8 s (7) | 12.3 s (8) | 12.1 s (6) | 13.7 s (8) | 14.1 s (8) |
| track_ambush (after wallow) | 3.7 s (8) | 3.1 s (7) | 4.2 s (7) | 3.3 s (8) | 2.9 s (8) | 3.9 s (8) | 3.2 s (8) |
| wolves (after track_ambush) | 7.4 s (8) | 5.8 s (7) | 7.0 s (7) | 6.6 s (8) | 4.8 s (8) | 5.9 s (8) | 5.8 s (8) |

Pack wakes while a champion (not its own pack's, nor the Knight at its own escort) lived within 25 m of her and was **awake** (the count that matters): II human: 0 in 8 runs; II careless: 0 in 8 runs; II deft: 0 in 8 runs; II plain: 0 in 8 runs; II standing: 0 in 8 runs; I human: 0 in 8 runs; I deft: 0 in 8 runs.

The same counting a champion that is still resting (the Knight asleep at the post 12 m from n_road2, for one): II human: 19; II careless: 20; II deft: 21; II plain: 21; II standing: 16; I human: 17; I deft: 20.

## Falls, rises and runs that did not get through

- II human: falls by stage: Boss 2, Exit 2; risen at: lowford.door 2, lowford.bank 2.
- II careless: falls by stage: Boss 2, Exit 1; risen at: lowford.door 2, lowford.bank 1.
  - s1: stuck: Exit beat boars at (-0,-32) goal (2,-80) (after 11.2 min)
- II deft: falls by stage: Boss 2; risen at: lowford.door 2.
  - s2: stuck: Exit beat boars at (8,-50) goal (2,-80) (after 10.2 min)
- II plain: falls by stage: Boss 2; risen at: lowford.door 2.
- II standing: falls by stage: Exit 2; risen at: act1.post1 2.
- I human: falls by stage: none; risen at: none.
- I deft: falls by stage: none; risen at: none.
