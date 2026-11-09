# The Low Ford: zone sim (M5-F)

**Today's self-firing bots; the pressing bots are M3's.** The real Prologue zone through HeadlessHost, from the Wake to the gate: the night's placed beats, the Barrow Knight, the Grave-Caller, the Ford-Warden (the films fall back to their captions headless), the dawn and the day stretch. Falls go through the zone's own OnDeath (the rise at her last lamp-post). A warden (calling) on her first weapon, no gear worn beyond the Watch Chest's jerkin (left in the pack: the bots do not dress).

Command: `dotnet run -c Release --project godot/balance -- zone --zone lowford --bots human,careless,deft,plain,standing --seeds 8 --tier 2 --also 1:human+deft --out docs/balance/zone_lowford.md`

Films: C01 11.8 s, C02 19.9 s, C03 23.1 s, C04A 13.5 s (godot/data/cinematics/*.json, the shots' "dur" summed; C04 B plays in the Waystation, not here); **68.3 s** added to each run for the with-films hour. Play-only time is the sim's seconds less the headless fallbacks that stand in for C02 and C03 (the Intro and Victory stages).

Kills are hers (fodder / elite / champion / boss). Packs: night and day beats put down (pack, ambush, ring). Gear: ground drops (all of it rolled: carriers, champions, the strongbox, the Warden), by tier; shown = not Hidden by the Default preset (LootFilter.Judge with the toggles on; first sightings not counted). Upgrade: a drop better than the best of its slot so far (Drops.Power over the worn piece by the upgrade margin), not worn. Fighting: a roused foe within 24 m.

## Per bot (medians; worst case in brackets)

| Tier | Bot | Runs | Through | Minutes play (worst) | Minutes with films | Kills f/e/c/b | Packs | Champions | Falls (worst) | Rises | Gear C/U/R/E/Set+L | Shown | Upgrades | Gold (taken / fell) | Lv Warden / gate (lowest) | Meters | Fighting % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| II | human | 8 | 8 | 6.7 (7.1) | 7.9 | 176/5/5/1 | 16 | 5 | 1 (1) | 1 | 2/3/3/0/0 | 7 | 6 | 15 / 196 | 3 / 5 (5) | 1712 | 41 |
| II | careless | 8 | 8 | 6.8 (7.4) | 7.9 | 176/5/5/1 | 16 | 5 | 1 (2) | 1 | 2/3/3/0/0 | 8 | 6 | 15 / 192 | 3 / 5 (5) | 1814 | 40 |
| II | deft | 8 | 8 | 6.4 (7.6) | 7.5 | 161/5/5/1 | 16 | 5 | 1 (1) | 1 | 2/2/4/0/0 | 8 | 5 | 8 / 187 | 3 / 5 (5) | 1702 | 44 |
| II | plain | 8 | 7 | 6.6 (16.6) | 7.7 | 176/5/5/1 | 16 | 5 | 1 (1) | 1 | 3/2/4/1/0 | 8 | 5 | 0 / 185 | 3 / 5 (4) | 1708 | 44 |
| II | standing | 8 | 8 | 5.1 (5.5) | 6.3 | 145/5/5/1 | 16 | 5 | 0 (1) | 0 | 2/1/2/1/1 | 7 | 4 | 15 / 162 | 3 / 5 (5) | 715 | 47 |
| I | human | 8 | 7 | 6.4 (9.1) | 7.5 | 162/5/5/1 | 16 | 5 | 0 (0) | 0 | 2/2/3/0/0 | 7 | 4 | 15 / 188 | 3 / 5 (2) | 1678 | 38 |
| I | deft | 8 | 8 | 6.3 (6.6) | 7.5 | 167/5/5/1 | 16 | 5 | 0 (0) | 0 | 2/2/4/1/0 | 8 | 5 | 15 / 199 | 3 / 5 (5) | 1660 | 40 |

## Per hour (medians of each run's rate; play-only / with films)

| Tier | Bot | Kills/hr | Packs/hr | Champions/hr | Gear shown/hr | Minutes per upgrade | Rises/hr |
|---|---|---|---|---|---|---|---|
| II | human | 1722 / 1473 | 143 / 122 | 40 / 34 | 63 / 54 | 1.3 / 1.5 | 4 / 4 |
| II | careless | 1650 / 1422 | 142 / 122 | 42 / 36 | 73 / 61 | 1.2 / 1.4 | 4 / 4 |
| II | deft | 1662 / 1422 | 151 / 128 | 42 / 36 | 77 / 64 | 1.5 / 1.7 | 4 / 3 |
| II | plain | 1725 / 1463 | 146 / 124 | 45 / 39 | 54 / 46 | 1.3 / 1.6 | 4 / 4 |
| II | standing | 1832 / 1501 | 178 / 147 | 56 / 46 | 82 / 67 | 1.5 / 1.8 | 0 / 0 |
| I | human | 1583 / 1351 | 148 / 126 | 42 / 36 | 65 / 55 | 1.6 / 1.9 | 0 / 0 |
| I | deft | 1678 / 1411 | 152 / 129 | 46 / 39 | 71 / 60 | 1.2 / 1.5 | 0 / 0 |

## Against ARPG.md 7.1's first hour (tier II, the human bot, per hour with films)

| | Target | Measured (per hour) | In this zone (one run) | Verdict |
|---|---|---|---|---|
| Kills | ~500 | 1473 | 187 | over |
| Packs (each with a captain) | ~40 | 122 | 16 | over |
| Champions | 4-6 | 33.9 | 5 | over |
| Gear shown (Default filter) | ~25 | 54 | 7 | over |
| An upgrade worth wearing | every ~8 min | every 1.5 min | 6 | more often |
| The Legendary | 1, certain, from the Ford-Warden | 0/8 runs | Warden's ground gear: 0 | missing |
| Levels | 1-5 in the hour | gate level 5 | | on |

The Warden's drops, all tier II runs: none on the ground.

## The campaign gates (7.1, tier II)

| Gate | Measured | Verdict |
|---|---|---|
| The human rises 1-3 an hour | 3.6/hr (median; runs 1,0,0,1,0,1,0,1) | fail |
| The deft at most once an hour | 3.5/hr (worst run 8.0) | fail |
| The standing bot falls to every champion pack | falls 0,1,1,0,0,0,1,0; fell at the Post 0/8, the Barrow 0/8, by day 3/8 | fail (5 champions: a fall each needs 5+) |
| Levels within ±20% (level 5 by the hour's end) | gate level 5 | pass |
| Drops within ±20% (~25 shown an hour) | 54/hr | fail |
| (kills within ±20%, ~500 an hour) | 1473/hr | fail |

**Read the rates with the zone's length:** the whole Low Ford plays in about 7.9 minutes (with films), so every per-hour rate is that run scaled by about 7.6x. One rise in a run reads as 7.6 an hour, so the rise gates cannot pass or fail fairly until the first hour is an hour of ground (see The ground). Per run, the totals (kills, packs, champions, gear, level 5 at the gate) are the numbers to set against the table's first hour: today's zone gives the first hour's levels and champions in an eighth of its time, and about a third of its kills, packs and gear.

Gold: the bots take only what they walk over (the coins are not pulled to her by day); the column gives what she took and what fell.

## The ground

- The route (the goals' walk: the camp, the night's 10 beats, the ford; the day's start, its 8 beats, the gate): **147 m by night + 213 m by day = 360 m**. (The meta's ROAD path, the camp to the ford: 262 m.)
- Walked by the human bot (tier II median), fights' footwork included: 1080 m by night, 656 m by day, 1736 m in all (4.8x the route).
- Packs placed: 10 by night, 6 by day, 16 in all: **4.4 packs per 100 m of route** (6.8 by night, 2.8 by day).
- The first hour's ~40 packs at today's density: **899 m** of route (+540 m, +24 packs more than today).
- The zone at about 45 minutes: today it plays in 7.9 min with films (46 m of route a minute, everything in it). At today's pace and density, 45 minutes is **2057 m** of route (5.7x today, +1697 m more), holding **91 packs** (+75 more).
- So ~40 packs fill about 20 minutes at today's pace; the extra minutes to 45 are walking, films, towns' worth of story, or denser fights (bigger packs, more per beat).

## Seconds per beat (median; woke to down) and her level at its fall (median)

| Beat | II human | II careless | II deft | II plain | II standing | I human | I deft |
|---|---|---|---|---|---|---|---|
| n_lone | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 |
| n_three | 2 s, L1 | 2 s, L1 | 2 s, L1 | 2 s, L1 | 1 s, L1 | 1 s, L1 | 1 s, L1 |
| n_first | 7 s, L1 | 7 s, L1 | 7 s, L1 | 7 s, L1 | 4 s, L1 | 5 s, L1 | 5 s, L1 |
| n_cart | 14 s, L2 | 14 s, L2 | 16 s, L2 | 14 s, L2 | 12 s, L2 | 12 s, L2 | 11 s, L2 |
| n_road1 | 10 s, L2 | 10 s, L2 | 10 s, L2 | 11 s, L2 | 11 s, L2 | 7 s, L2 | 5 s, L2 |
| n_road2 | 9 s, L2 | 9 s, L2 | 10 s, L2 | 9 s, L2 | 5 s, L2 | 5 s, L2 | 4 s, L2 |
| n_post | 4 s, L2 | 4 s, L2 | 6 s, L2 | 4 s, L2 | 4 s, L2 | 4 s, L2 | 4 s, L2 |
| n_road3 | 5 s, L3 | 5 s, L3 | 5 s, L3 | 6 s, L3 | 3 s, L3 | 5 s, L3 | 4 s, L3 |
| n_road4 | 5 s, L3 | 7 s, L3 | 6 s, L3 | 5 s, L3 | 5 s, L3 | 5 s, L3 | 4 s, L3 |
| n_ford | 5 s, L3 | 4 s, L3 | 4 s, L3 | 5 s, L3 | 3 s, L3 | 3 s, L3 | 4 s, L3 |
| boars | 15 s, L4 | 17 s, L4 | 14 s, L4 | 15 s, L4 | 15 s, L4 | 16 s, L4 | 14 s, L4 |
| kerchiefs | 35 s, L4 | 32 s, L4 | 40 s, L4 | 33 s, L4 | 28 s, L4 | 29 s, L4 | 31 s, L4 |
| road_ambush | 5 s, L4 | 6 s, L4 | 5 s, L4 | 6 s, L4 | 4 s, L4 | 6 s, L4 | 6 s, L4 |
| wallow | 21 s, L4 | 20 s, L4 | 21 s, L4 | 22 s, L4 | 22 s, L4 | 22 s, L4 | 21 s, L4 |
| track_ambush | 6 s, L5 | 9 s, L5 | 8 s, L4 | 6 s, L5 | 7 s, L4 | 7 s, L4 | 7 s, L4 |
| wolves | 0 s, L5 | 0 s, L5 | 0 s, L5 | 0 s, L5 | 0 s, L4 | 0 s, L5 | 0 s, L5 |
| stage Wake | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s |
| stage Rising | 0 s | 0 s | 0 s | 0 s | 0 s | 0 s | 0 s |
| stage Road | 2 s | 2 s | 2 s | 2 s | 6 s | 2 s | 2 s |
| stage Ambush | 25 s | 25 s | 25 s | 24 s | 12 s | 15 s | 16 s |
| stage Road2 | 3 s | 3 s | 2 s | 3 s | 4 s | 2 s | 3 s |
| stage Post | 30 s | 30 s | 27 s | 30 s | 32 s | 37 s | 26 s |
| stage Barrow | 38 s | 39 s | 37 s | 40 s | 38 s | 39 s | 37 s |
| stage ToFord | 12 s | 9 s | 12 s | 10 s | 12 s | 9 s | 10 s |
| stage Intro | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s |
| stage Boss | 155 s | 163 s | 121 s | 131 s | 67 s | 151 s | 152 s |
| stage Victory | 13 s | 13 s | 13 s | 13 s | 13 s | 13 s | 13 s |
| stage Dawn | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s |
| stage Exit | 127 s | 130 s | 129 s | 124 s | 119 s | 117 s | 123 s |

## Falls, rises and runs that did not get through

- II human: falls by stage: Exit 3, Boss 1; risen at: act1.post1 1, lowford.bank 2, lowford.door 1.
- II careless: falls by stage: Exit 4, Boss 2; risen at: lowford.bank 2, act1.post1 2, lowford.door 2.
- II deft: falls by stage: Boss 4; risen at: lowford.door 4.
- II plain: falls by stage: Exit 2, Boss 3; risen at: act1.post1 1, lowford.bank 1, lowford.door 3.
  - s3: stuck: Exit beat road_ambush at (49,-86) goal (50,-86) (after 13.4 min)
- II standing: falls by stage: Exit 3; risen at: act1.post1 3.
- I human: falls by stage: none; risen at: none.
  - s7: stuck: Post beat n_road3 at (16,38) goal (10,32) (after 5.8 min)
- I deft: falls by stage: none; risen at: none.
