# The Low Ford: zone sim (M5-F)

**Today's self-firing bots; the pressing bots are M3's.** The real Prologue zone through HeadlessHost, from the Wake to the gate: the night's placed beats, the Barrow Knight, the Grave-Caller, the Ford-Warden (the films fall back to their captions headless), the dawn and the day stretch. Falls go through the zone's own OnDeath (the rise at her last lamp-post). A warden (calling) on her first weapon, no gear worn beyond the Watch Chest's jerkin (left in the pack: the bots do not dress).

Command: `dotnet run -c Release --project godot/balance -- zone --zone lowford --bots human --seeds 2 --tier 2 --par 4 --out tools/scratch/m9_zone_t2.md`

Films: C01 11.8 s, C02 19.9 s, C03 23.1 s, C04A 13.5 s (godot/data/cinematics/*.json, the shots' "dur" summed; C04 B plays in the Waystation, not here); **68.3 s** added to each run for the with-films hour. Play-only time is the sim's seconds less the headless fallbacks that stand in for C02 and C03 (the Intro and Victory stages).

Kills are hers (fodder / elite / champion / boss). Packs: night and day beats put down (pack, ambush, ring). Gear: ground drops (all of it rolled: carriers, champions, the strongbox, the Warden), by tier; shown = not Hidden by the Default preset (LootFilter.Judge with the toggles on; first sightings not counted). Upgrade: a drop better than the best of its slot so far (Drops.Power over the worn piece by the upgrade margin), not worn. Fighting: a roused foe within 24 m.

## Per bot (medians; worst case in brackets)

| Tier | Bot | Runs | Through | Minutes play (worst) | Minutes with films | Kills f/e/c/b | Packs | Champions | Falls (worst) | Rises | Gear C/U/R/E/Set+L | Shown | Upgrades | Gold (taken / fell) | Lv Warden / gate (lowest) | Meters | Fighting % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| II | human | 2 | 2 | 5.2 (5.2) | 6.3 | 137/5/5/1 | 16 | 5 | 1 (1) | 1 | 3/4/3/0/1 | 10 | 6 | 15 / 149 | 3 / 5 (5) | 954 | 40 |

## The presses (M3; medians, presses and damage shares averaged over the runs)

| group | runs | mark gap in fights from 0:45 (s, med / worst) | Resolve spent /min | Resolve at max % | presses /min | damage shares % | Flare casts / first (s) / share % / boss share % | falls (where) |
|---|---|---|---|---|---|---|---|---|
| T2 human | 2 | 28 / 28 | 448 | 7 | groundbreaker 7.8, heroic_leap 0.2 | groundbreaker 33, sunder 30, oathblade 20, flare 12, heroic_leap 4, dash 0 | 5 / 124 / 13 / 11 | Exit@(-32,-88) by boar_slurry x1; Exit@(39,-90) by kerchief_captain x1 |

## Per hour (medians of each run's rate; play-only / with films)

| Tier | Bot | Kills/hr | Packs/hr | Champions/hr | Gear shown/hr | Minutes per upgrade | Rises/hr |
|---|---|---|---|---|---|---|---|
| II | human | 1714 / 1405 | 185 / 152 | 58 / 47 | 110 / 90 | 0.9 / 1.1 | 12 / 9 |

## Against ARPG.md 7.1's first hour (tier II, the human bot, per hour with films)

| | Target | Measured (per hour) | In this zone (one run) | Verdict |
|---|---|---|---|---|
| Kills | ~500 | 1405 | 148 | over |
| Packs (each with a captain) | ~40 | 152 | 16 | over |
| Champions | 4-6 | 47.5 | 5 | over |
| Gear shown (Default filter) | ~25 | 90 | 10 | over |
| An upgrade worth wearing | every ~8 min | every 1.1 min | 6 | more often |
| The Legendary | 1, certain, from the Ford-Warden | 2/2 runs | Warden's ground gear: 1 | on |
| Levels | 1-5 in the hour | gate level 5 | | on |

The Warden's drops, all tier II runs: Legendary fordwardens_evening_chain x2.

## The campaign gates (7.1, tier II)

| Gate | Measured | Verdict |
|---|---|---|
| The human rises 1-3 an hour | 9.5/hr (median; runs 1,1) | fail |
| Levels within ±20% (level 5 by the hour's end) | gate level 5 | pass |
| Drops within ±20% (~25 shown an hour) | 90/hr | fail |
| (kills within ±20%, ~500 an hour) | 1405/hr | fail |

**Read the rates with the zone's length:** the whole Low Ford plays in about 6.3 minutes (with films), so every per-hour rate is that run scaled by about 9.5x. One rise in a run reads as 9.5 an hour, so the rise gates cannot pass or fail fairly until the first hour is an hour of ground (see The ground). Per run, the totals (kills, packs, champions, gear, level 5 at the gate) are the numbers to set against the table's first hour: today's zone gives the first hour's levels and champions in an eighth of its time, and about a third of its kills, packs and gear.

Gold: the bots take only what they walk over (the coins are not pulled to her by day); the column gives what she took and what fell.

## The ground

- The route (the goals' walk: the camp, the night's 10 beats, the ford; the day's start, its 8 beats, the gate): **148 m by night + 208 m by day = 356 m**. (The meta's ROAD path, the camp to the ford: 262 m.)
- Walked by the human bot (tier II median), fights' footwork included: 523 m by night, 431 m by day, 954 m in all (2.7x the route).
- Packs placed: 10 by night, 6 by day, 16 in all: **4.5 packs per 100 m of route** (6.7 by night, 2.9 by day).
- The first hour's ~40 packs at today's density: **889 m** of route (+534 m, +24 packs more than today).
- The zone at about 45 minutes: today it plays in 6.3 min with films (56 m of route a minute, everything in it). At today's pace and density, 45 minutes is **2533 m** of route (7.1x today, +2177 m more), holding **114 packs** (+98 more).
- So ~40 packs fill about 16 minutes at today's pace; the extra minutes to 45 are walking, films, towns' worth of story, or denser fights (bigger packs, more per beat).

## Seconds per beat (median; woke to down) and her level at its fall (median)

| Beat | II human |
|---|---|
| n_lone | 0 s, L1 |
| n_three | 0 s, L1 |
| n_first | 2 s, L1 |
| n_cart | 10 s, L2 |
| n_road1 | 1 s, L2 |
| n_road2 | 3 s, L2 |
| n_post | 4 s, L2 |
| n_road3 | 2 s, L3 |
| n_road4 | 2 s, L3 |
| n_ford | 3 s, L3 |
| boars | 11 s, L4 |
| kerchiefs | 26 s, L4 |
| road_ambush | 8 s, L4 |
| wallow | 20 s, L4 |
| track_ambush | 7 s, L4 |
| wolves | 0 s, L4 |
| stage Wake | 3 s |
| stage Rising | 4 s |
| stage Road | 2 s |
| stage Ambush | 15 s |
| stage Road2 | 7 s |
| stage Post | 42 s |
| stage Barrow | 42 s |
| stage ToFord | 15 s |
| stage Intro | 6 s |
| stage Boss | 61 s |
| stage Victory | 39 s |
| stage Dawn | 10 s |
| stage Exit | 110 s |

## Quiet between beats (median seconds from the previous beat's down to this beat's wake; negative = woke before the last fell)

| Beat (after the one before it in the data) | II human |
|---|---|
| n_three (after n_lone) | 5.6 s (2) |
| n_first (after n_three) | 7.3 s (2) |
| n_cart (after n_first) | -2.4 s (2) |
| n_road1 (after n_cart) | 4.7 s (2) |
| n_road2 (after n_road1) | 4.7 s (2) |
| n_post (after n_road2) | 4.2 s (2) |
| n_road3 (after n_post) | 25.2 s (2) |
| n_road4 (after n_road3) | 4.7 s (2) |
| n_ford (after n_road4) | 43.1 s (2) |
| boars (after n_ford) | 114.8 s (2) |
| kerchiefs (after boars) | 6.7 s (2) |
| road_ambush (after kerchiefs) | 5.0 s (2) |
| wallow (after road_ambush) | 12.3 s (2) |
| track_ambush (after wallow) | 2.4 s (2) |
| wolves (after track_ambush) | 6.2 s (2) |

Pack wakes while a champion (not its own pack's, nor the Knight at its own escort) lived within 25 m of her and was **awake** (the count that matters): II human: 0 in 2 runs.

The same counting a champion that is still resting (the Knight asleep at the post 12 m from n_road2, for one): II human: 5.

## Falls, rises and runs that did not get through

- II human: falls by stage: Exit 2; risen at: act1.post1 1, lowford.bank 1.
