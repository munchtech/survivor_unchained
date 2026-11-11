# The Low Ford: zone sim (M5-F)

**Today's self-firing bots; the pressing bots are M3's.** The real Prologue zone through HeadlessHost, from the Wake to the gate: the night's placed beats, the Barrow Knight, the Grave-Caller, the Ford-Warden (the films fall back to their captions headless), the dawn and the day stretch. Falls go through the zone's own OnDeath (the rise at her last lamp-post). A warden (calling) on her first weapon, no gear worn beyond the Watch Chest's jerkin (left in the pack: the bots do not dress).

**The stand clock is retired (10 Nov, the owner's ruling).** "Some builds like archers very much move into an area and then stand still while they shoot. So that rule isn't really a thing anymore." `world_tiers.json` `standOn: false`: the story and map fights no longer charge a stander. The rows stay as data (`WorldTiers.Tier.StandRow`), and the arena keeps its own director's stand. This sim is the first one run with it off.

Before and after, II standing, 8 seeds:
- Falls: median 3 (worst 8) before, 3 (worst 4) after.
- By stage: Post 5, Exit 19, Boss 2 before; Exit 18, Boss 2 after.

So the clock's falls were the Watch-post ones. What is left is the day: the bot stands in the pillagers' and wolves' ring at the Exit, which is a get-out beat, not the clock. The worst-run cap halved, and every other bot is unchanged within noise.

Command: `dotnet run -c Release --project godot/balance -- zone --zone lowford --bots human,careless,deft,plain,standing --seeds 8 --tier 2 --also 1:human+deft --out docs/balance/zone_lowford.md`

Films: C01 11.8 s, C02 19.9 s, C03 23.1 s, C04A 13.5 s (godot/data/cinematics/*.json, the shots' "dur" summed; C04 B plays in the Waystation, not here); **68.3 s** added to each run for the with-films hour. Play-only time is the sim's seconds less the headless fallbacks that stand in for C02 and C03 (the Intro and Victory stages).

Kills are hers (fodder / elite / champion / boss). Packs: night and day beats put down (pack, ambush, ring). Gear: ground drops (all of it rolled: carriers, champions, the strongbox, the Warden), by tier; shown = not Hidden by the Default preset (LootFilter.Judge with the toggles on; first sightings not counted). Upgrade: a drop better than the best of its slot so far (Drops.Power over the worn piece by the upgrade margin), not worn. Fighting: a roused foe within 24 m.

## Per bot (medians; worst case in brackets)

| Tier | Bot | Runs | Through | Minutes play (worst) | Minutes with films | Kills f/e/c/b | Packs | Champions | Falls (worst) | Rises | Gear C/U/R/E/Set+L | Shown | Upgrades | Gold (taken / fell) | Lv Warden / gate (lowest) | Meters | Fighting % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| II | human | 8 | 8 | 5.1 (6.2) | 6.3 | 139/5/5/1 | 16 | 5 | 0 (0) | 0 | 3/3/3/1/1 | 10 | 6 | 15 / 192 | 3 / 5 (4) | 1013 | 41 |
| II | careless | 8 | 8 | 5.2 (5.8) | 6.3 | 135/5/5/1 | 16 | 5 | 0 (1) | 0 | 2/3/4/1/1 | 10 | 5 | 15 / 185 | 3 / 5 (4) | 1006 | 40 |
| II | deft | 8 | 8 | 5.7 (6.0) | 6.9 | 142/5/5/1 | 16 | 5 | 0 (0) | 0 | 3/3/2/1/1 | 10 | 6 | 15 / 188 | 3 / 5 (4) | 1079 | 41 |
| II | plain | 8 | 8 | 5.6 (5.9) | 6.7 | 139/5/4/1 | 16 | 4 | 0 (0) | 0 | 2/2/4/1/1 | 9 | 5 | 15 / 184 | 3 / 5 (4) | 1150 | 43 |
| II | standing | 8 | 8 | 6.2 (8.2) | 7.3 | 150/5/4/1 | 16 | 4 | 3 (4) | 3 | 2/3/3/1/1 | 9 | 5 | 15 / 169 | 3 / 5 (4) | 717 | 43 |
| I | human | 8 | 8 | 5.3 (5.7) | 6.4 | 139/5/5/1 | 16 | 5 | 0 (0) | 0 | 3/3/3/1/1 | 10 | 5 | 15 / 185 | 3 / 5 (4) | 1040 | 38 |
| I | deft | 8 | 8 | 5.2 (5.7) | 6.3 | 147/5/5/1 | 16 | 5 | 0 (0) | 0 | 4/3/4/0/1 | 10 | 6 | 15 / 192 | 3 / 5 (4) | 1047 | 39 |

## The presses (M3; medians, presses and damage shares averaged over the runs)

| group | runs | mark gap in fights from 0:45 (s, med / worst) | Resolve spent /min | Resolve at max % | presses /min | damage shares % | Flare casts / first (s) / share % / boss share % | falls (where) |
|---|---|---|---|---|---|---|---|---|
| T2 human | 8 | 32 / 59 | 426 | 4 | groundbreaker 8.0, heroic_leap 0.3 | groundbreaker 36, sunder 31, oathblade 22, heroic_leap 6, flare 4, dash 0 | 2 / 135 / 4 / 16 |  |
| T2 careless | 8 | 33 / 38 | 417 | 6 | groundbreaker 8.2, heroic_leap 0.2 | groundbreaker 39, sunder 32, oathblade 22, heroic_leap 4, flare 2, dash 0 | 1 / 169 / 3 / 12 | Exit@(-36,-98) by boar x1 |
| T2 deft | 8 | 33 / 39 | 416 | 0 | groundbreaker 9.6, heroic_leap 0.3 | groundbreaker 41, sunder 31, oathblade 20, heroic_leap 5, flare 3 | 2 / 142 / 3 / 13 |  |
| T2 plain | 8 | 31 / 41 | 295 | 29 |  | sunder 44, oathblade 30, groundbreaker 22, flare 4, dash 0 | 2 / 138 / 4 / 22 |  |
| T2 standing | 8 | 39 / 124 | 310 | 32 |  | sunder 46, oathblade 28, groundbreaker 21, flare 5 | 2 / 130 / 5 / 18 | Exit@(2,-102) by wolf x3; Exit@(38,-88) by kerchief_captain x1; Exit@(4,-100) by wolf x1; Exit@(27,-84) by footpad x1 |
| T1 human | 8 | 31 / 39 | 382 | 4 | groundbreaker 7.4, heroic_leap 0.3 | sunder 35, groundbreaker 32, oathblade 24, heroic_leap 6, flare 3, dash 0 | 2 / 139 / 3 / 15 |  |
| T1 deft | 8 | 30 / 40 | 367 | 0 | groundbreaker 8.9, heroic_leap 0.3 | groundbreaker 36, sunder 34, oathblade 20, heroic_leap 6, flare 3, dash 0 | 2 / 134 / 3 / 16 |  |

## Per hour (medians of each run's rate; play-only / with films)

| Tier | Bot | Kills/hr | Packs/hr | Champions/hr | Gear shown/hr | Minutes per upgrade | Rises/hr |
|---|---|---|---|---|---|---|---|
| II | human | 1703 / 1388 | 185 / 151 | 59 / 48 | 113 / 92 | 1.0 / 1.2 | 0 / 0 |
| II | careless | 1749 / 1423 | 182 / 150 | 57 / 47 | 111 / 92 | 1.0 / 1.2 | 0 / 0 |
| II | deft | 1631 / 1348 | 168 / 140 | 52 / 43 | 101 / 85 | 0.9 / 1.1 | 0 / 0 |
| II | plain | 1604 / 1331 | 170 / 142 | 45 / 37 | 96 / 80 | 1.1 / 1.4 | 0 / 0 |
| II | standing | 1555 / 1323 | 154 / 130 | 41 / 35 | 86 / 72 | 1.3 / 1.6 | 22 / 19 |
| I | human | 1719 / 1407 | 183 / 150 | 56 / 46 | 108 / 89 | 1.1 / 1.3 | 0 / 0 |
| I | deft | 1798 / 1473 | 185 / 152 | 57 / 47 | 115 / 94 | 0.9 / 1.1 | 0 / 0 |

## Against ARPG.md 7.1's first hour (tier II, the human bot, per hour with films)

| | Target | Measured (per hour) | In this zone (one run) | Verdict |
|---|---|---|---|---|
| Kills | ~500 | 1388 | 150 | over |
| Packs (each with a captain) | ~40 | 151 | 16 | over |
| Champions | 4-6 | 47.9 | 5 | over |
| Gear shown (Default filter) | ~25 | 92 | 10 | over |
| An upgrade worth wearing | every ~8 min | every 1.2 min | 6 | more often |
| The Legendary | 1, certain, from the Ford-Warden | 8/8 runs | Warden's ground gear: 1 | on |
| Levels | 1-5 in the hour | gate level 5 | | on |

The Warden's drops, all tier II runs: Legendary drowned_coat x41.

## The campaign gates (7.1, tier II)

| Gate | Measured | Verdict |
|---|---|---|
| The human rises 1-3 an hour | 0.0/hr (median; runs 0,0,0,0,0,0,0,0) | fail |
| The deft at most once an hour | 0.0/hr (worst run 0.0) | pass |
| The standing bot falls to every champion pack | falls 2,3,2,4,4,0,3,2; fell at the Post 0/8, the Barrow 0/8, by day 7/8 | fail (5 champions: a fall each needs 5+) |
| Levels within ±20% (level 5 by the hour's end) | gate level 5 | pass |
| Drops within ±20% (~25 shown an hour) | 92/hr | fail |
| (kills within ±20%, ~500 an hour) | 1388/hr | fail |

**Read the rates with the zone's length:** the whole Low Ford plays in about 6.3 minutes (with films), so every per-hour rate is that run scaled by about 9.6x. One rise in a run reads as 9.6 an hour, so the rise gates cannot pass or fail fairly until the first hour is an hour of ground (see The ground). Per run, the totals (kills, packs, champions, gear, level 5 at the gate) are the numbers to set against the table's first hour: today's zone gives the first hour's levels and champions in an eighth of its time, and about a third of its kills, packs and gear.

Gold: the bots take only what they walk over (the coins are not pulled to her by day); the column gives what she took and what fell.

## The ground

- The route (the goals' walk: the camp, the night's 10 beats, the ford; the day's start, its 8 beats, the gate): **148 m by night + 208 m by day = 356 m**. (The meta's ROAD path, the camp to the ford: 262 m.)
- Walked by the human bot (tier II median), fights' footwork included: 535 m by night, 488 m by day, 1023 m in all (2.9x the route).
- Packs placed: 10 by night, 6 by day, 16 in all: **4.5 packs per 100 m of route** (6.7 by night, 2.9 by day).
- The first hour's ~40 packs at today's density: **889 m** of route (+534 m, +24 packs more than today).
- The zone at about 45 minutes: today it plays in 6.3 min with films (57 m of route a minute, everything in it). At today's pace and density, 45 minutes is **2558 m** of route (7.2x today, +2203 m more), holding **115 packs** (+99 more).
- So ~40 packs fill about 16 minutes at today's pace; the extra minutes to 45 are walking, films, towns' worth of story, or denser fights (bigger packs, more per beat).

## Seconds per beat (median; woke to down) and her level at its fall (median)

| Beat | II human | II careless | II deft | II plain | II standing | I human | I deft |
|---|---|---|---|---|---|---|---|
| n_lone | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 |
| n_three | 0 s, L1 | 1 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 | 0 s, L1 |
| n_first | 3 s, L1 | 3 s, L1 | 2 s, L1 | 4 s, L1 | 3 s, L1 | 3 s, L1 | 2 s, L1 |
| n_cart | 8 s, L2 | 9 s, L2 | 10 s, L2 | 9 s, L2 | 10 s, L2 | 9 s, L2 | 7 s, L2 |
| n_road1 | 2 s, L2 | 2 s, L2 | 2 s, L2 | 3 s, L2 | 2 s, L2 | 1 s, L2 | 2 s, L2 |
| n_road2 | 2 s, L2 | 2 s, L2 | 1 s, L2 | 3 s, L2 | 2 s, L2 | 1 s, L2 | 1 s, L2 |
| n_post | 2 s, L2 | 2 s, L2 | 3 s, L2 | 2 s, L2 | 3 s, L2 | 3 s, L2 | 2 s, L2 |
| n_road3 | 3 s, L3 | 3 s, L3 | 3 s, L3 | 3 s, L3 | 1 s, L2 | 4 s, L3 | 1 s, L3 |
| n_road4 | 3 s, L3 | 2 s, L3 | 1 s, L3 | 3 s, L3 | 3 s, L3 | 1 s, L3 | 1 s, L3 |
| n_ford | 3 s, L3 | 3 s, L3 | 3 s, L3 | 3 s, L3 | 3 s, L3 | 2 s, L3 | 3 s, L3 |
| boars | 14 s, L4 | 12 s, L4 | 13 s, L4 | 18 s, L4 | 16 s, L4 | 13 s, L4 | 11 s, L4 |
| kerchiefs | 21 s, L4 | 21 s, L4 | 27 s, L4 | 26 s, L4 | 22 s, L4 | 20 s, L4 | 25 s, L4 |
| road_ambush | 7 s, L4 | 5 s, L4 | 9 s, L4 | 7 s, L4 | 8 s, L4 | 4 s, L4 | 6 s, L4 |
| wallow | 18 s, L4 | 16 s, L4 | 16 s, L4 | 21 s, L4 | 24 s, L4 | 18 s, L4 | 15 s, L4 |
| track_ambush | 6 s, L4 | 7 s, L4 | 8 s, L4 | 9 s, L4 | 9 s, L4 | 6 s, L4 | 7 s, L4 |
| wolves | 5 s, L4 | 5 s, L4 | 5 s, L4 | 5 s, L4 | 5 s, L4 | 5 s, L4 | 4 s, L4 |
| stage Wake | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s |
| stage Rising | 3 s | 3 s | 3 s | 3 s | 2 s | 3 s | 3 s |
| stage Road | 2 s | 2 s | 2 s | 2 s | 2 s | 2 s | 2 s |
| stage Ambush | 14 s | 14 s | 14 s | 17 s | 16 s | 14 s | 13 s |
| stage Road2 | 10 s | 7 s | 9 s | 8 s | 8 s | 7 s | 6 s |
| stage Post | 41 s | 41 s | 45 s | 41 s | 35 s | 41 s | 41 s |
| stage Barrow | 42 s | 41 s | 40 s | 41 s | 39 s | 39 s | 39 s |
| stage ToFord | 14 s | 14 s | 13 s | 14 s | 14 s | 14 s | 16 s |
| stage Intro | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s |
| stage Boss | 62 s | 62 s | 61 s | 63 s | 73 s | 61 s | 61 s |
| stage Victory | 39 s | 39 s | 39 s | 39 s | 39 s | 39 s | 39 s |
| stage Dawn | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s |
| stage Exit | 110 s | 111 s | 124 s | 129 s | 149 s | 112 s | 116 s |

## Quiet between beats (median seconds from the previous beat's down to this beat's wake; negative = woke before the last fell)

| Beat (after the one before it in the data) | II human | II careless | II deft | II plain | II standing | I human | I deft |
|---|---|---|---|---|---|---|---|
| n_three (after n_lone) | 5.0 s (6) | 5.0 s (7) | 5.0 s (6) | 5.0 s (6) | 4.1 s (8) | 5.0 s (5) | 5.0 s (5) |
| n_first (after n_three) | 7.0 s (8) | 7.1 s (8) | 7.2 s (8) | 7.2 s (8) | 6.1 s (8) | 6.6 s (8) | 6.6 s (8) |
| n_cart (after n_first) | -2.0 s (8) | -3.1 s (8) | -1.8 s (8) | -3.8 s (8) | 0.0 s (8) | -0.8 s (8) | -0.5 s (8) |
| n_road1 (after n_cart) | 5.0 s (7) | 4.3 s (8) | 4.1 s (8) | 4.3 s (7) | 4.1 s (8) | 5.0 s (8) | 4.1 s (8) |
| n_road2 (after n_road1) | 4.5 s (8) | 4.5 s (8) | 4.1 s (8) | 4.3 s (8) | 4.1 s (7) | 5.2 s (7) | 4.3 s (8) |
| n_post (after n_road2) | 4.6 s (7) | 4.7 s (7) | 4.1 s (8) | 4.2 s (8) | 4.6 s (8) | 4.6 s (8) | 4.1 s (6) |
| n_road3 (after n_post) | 28.5 s (8) | 28.8 s (8) | 28.7 s (8) | 24.6 s (8) | 20.8 s (8) | 27.0 s (8) | 28.5 s (7) |
| n_road4 (after n_road3) | 4.3 s (8) | 4.5 s (8) | 4.7 s (8) | 5.0 s (8) | 4.1 s (8) | 4.3 s (8) | 4.3 s (8) |
| n_ford (after n_road4) | 40.9 s (7) | 41.3 s (7) | 40.4 s (6) | 40.3 s (7) | 41.6 s (7) | 40.5 s (7) | 41.7 s (8) |
| boars (after n_ford) | 118.9 s (7) | 121.7 s (7) | 124.3 s (6) | 119.6 s (7) | 128.5 s (7) | 123.4 s (7) | 121.9 s (8) |
| kerchiefs (after boars) | 6.6 s (8) | 6.9 s (8) | 6.7 s (8) | 6.8 s (8) | 6.7 s (8) | 7.1 s (8) | 6.4 s (8) |
| road_ambush (after kerchiefs) | 5.8 s (8) | 4.4 s (8) | 4.6 s (8) | 4.6 s (8) | 5.5 s (5) | 4.4 s (8) | 6.1 s (8) |
| wallow (after road_ambush) | 12.3 s (8) | 11.7 s (8) | 12.1 s (8) | 11.0 s (8) | 11.0 s (5) | 13.0 s (8) | 11.7 s (8) |
| track_ambush (after wallow) | 2.8 s (8) | 3.1 s (8) | 3.0 s (8) | 2.9 s (8) | 2.8 s (8) | 2.6 s (8) | 3.3 s (8) |
| wolves (after track_ambush) | 6.2 s (8) | 6.6 s (8) | 7.7 s (8) | 6.5 s (8) | 6.0 s (8) | 6.2 s (8) | 6.7 s (8) |

Pack wakes while a champion (not its own pack's, nor the Knight at its own escort) lived within 25 m of her and was **awake** (the count that matters): II human: 0 in 8 runs; II careless: 0 in 8 runs; II deft: 0 in 8 runs; II plain: 0 in 8 runs; II standing: 0 in 8 runs; I human: 0 in 8 runs; I deft: 0 in 8 runs.

The same counting a champion that is still resting (the Knight asleep at the post 12 m from n_road2, for one): II human: 16; II careless: 16; II deft: 16; II plain: 17; II standing: 15; I human: 14; I deft: 14.

## Falls, rises and runs that did not get through

- II human: falls by stage: none; risen at: none.
- II careless: falls by stage: Exit 1; risen at: act1.post1 1.
- II deft: falls by stage: none; risen at: none.
- II plain: falls by stage: none; risen at: none.
- II standing: falls by stage: Exit 18, Boss 2; risen at: lowford.bank 6, act1.post1 12, lowford.door 2.
- I human: falls by stage: none; risen at: none.
- I deft: falls by stage: none; risen at: none.
