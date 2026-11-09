# The Low Ford: zone sim (M5-F)

**Today's self-firing bots; the pressing bots are M3's.** The real Prologue zone through HeadlessHost, from the Wake to the gate: the night's placed beats, the Barrow Knight, the Grave-Caller, the Ford-Warden (the films fall back to their captions headless), the dawn and the day stretch. Falls go through the zone's own OnDeath (the rise at her last lamp-post). A warden (calling) on her first weapon, no gear worn beyond the Watch Chest's jerkin (left in the pack: the bots do not dress).

Command: `dotnet run -c Release --project godot/balance -- zone --zone lowford --bots human,careless,deft,plain,standing --seeds 8 --tier 2 --also 1:human+deft --out C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/zones-m5/docs/balance/zone_base.md`

Films: C01 11.8 s, C02 19.9 s, C03 23.1 s, C04A 13.5 s (godot/data/cinematics/*.json, the shots' "dur" summed; C04 B plays in the Waystation, not here); **68.3 s** added to each run for the with-films hour. Play-only time is the sim's seconds less the headless fallbacks that stand in for C02 and C03 (the Intro and Victory stages).

Kills are hers (fodder / elite / champion / boss). Packs: night and day beats put down (pack, ambush, ring). Gear: ground drops (all of it rolled: carriers, champions, the strongbox, the Warden), by tier; shown = not Hidden by the Default preset (LootFilter.Judge with the toggles on; first sightings not counted). Upgrade: a drop better than the best of its slot so far (Drops.Power over the worn piece by the upgrade margin), not worn. Fighting: a roused foe within 24 m.

## Per bot (medians; worst case in brackets)

| Tier | Bot | Runs | Through | Minutes play (worst) | Minutes with films | Kills f/e/c/b | Packs | Champions | Falls (worst) | Rises | Gear C/U/R/E/Set+L | Shown | Upgrades | Gold (taken / fell) | Lv Warden / gate (lowest) | Meters | Fighting % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| II | human | 8 | 8 | 6.7 (7.5) | 7.8 | 175/5/5/1 | 16 | 5 | 1 (1) | 1 | 3/3/4/0/1 | 10 | 6 | 15 / 193 | 3 / 5 (5) | 1753 | 41 |
| II | careless | 8 | 8 | 6.8 (7.5) | 7.9 | 176/5/5/1 | 16 | 5 | 1 (2) | 1 | 2/2/4/0/1 | 11 | 7 | 15 / 201 | 3 / 5 (5) | 1775 | 39 |
| II | deft | 8 | 8 | 6.9 (10.0) | 8.0 | 164/5/5/1 | 16 | 5 | 1 (1) | 1 | 2/2/3/0/1 | 8 | 5 | 8 / 178 | 3 / 5 (4) | 1676 | 44 |
| II | plain | 8 | 6 | 6.6 (20.9) | 7.7 | 168/5/5/1 | 16 | 5 | 1 (1) | 1 | 3/1/3/1/1 | 8 | 5 | 0 / 177 | 3 / 5 (4) | 1745 | 48 |
| II | standing | 8 | 8 | 5.0 (5.6) | 6.2 | 147/5/5/1 | 16 | 5 | 1 (1) | 1 | 2/3/3/1/2 | 11 | 6 | 15 / 176 | 3 / 5 (5) | 724 | 49 |
| I | human | 8 | 7 | 6.4 (7.7) | 7.6 | 162/5/5/1 | 16 | 5 | 0 (0) | 0 | 2/2/3/0/1 | 10 | 5 | 15 / 180 | 3 / 5 (2) | 1649 | 38 |
| I | deft | 8 | 8 | 6.2 (6.8) | 7.4 | 166/5/5/1 | 16 | 5 | 0 (0) | 0 | 3/2/4/1/1 | 11 | 6 | 15 / 204 | 3 / 5 (5) | 1647 | 39 |

## Per hour (medians of each run's rate; play-only / with films)

| Tier | Bot | Kills/hr | Packs/hr | Champions/hr | Gear shown/hr | Minutes per upgrade | Rises/hr |
|---|---|---|---|---|---|---|---|
| II | human | 1699 / 1455 | 144 / 123 | 41 / 35 | 80 / 68 | 1.2 / 1.4 | 4 / 3 |
| II | careless | 1623 / 1409 | 141 / 121 | 41 / 35 | 92 / 79 | 1.1 / 1.3 | 4 / 3 |
| II | deft | 1627 / 1397 | 139 / 119 | 34 / 29 | 82 / 69 | 1.3 / 1.5 | 7 / 6 |
| II | plain | 1674 / 1411 | 146 / 125 | 41 / 34 | 68 / 59 | 1.3 / 1.5 | 1 / 1 |
| II | standing | 1860 / 1517 | 185 / 152 | 59 / 48 | 123 / 101 | 0.9 / 1.1 | 5 / 4 |
| I | human | 1589 / 1351 | 148 / 126 | 42 / 36 | 85 / 73 | 1.2 / 1.5 | 0 / 0 |
| I | deft | 1679 / 1422 | 154 / 130 | 46 / 39 | 106 / 90 | 1.1 / 1.3 | 0 / 0 |

## Against ARPG.md 7.1's first hour (tier II, the human bot, per hour with films)

| | Target | Measured (per hour) | In this zone (one run) | Verdict |
|---|---|---|---|---|
| Kills | ~500 | 1455 | 186 | over |
| Packs (each with a captain) | ~40 | 123 | 16 | over |
| Champions | 4-6 | 35.2 | 5 | over |
| Gear shown (Default filter) | ~25 | 68 | 10 | over |
| An upgrade worth wearing | every ~8 min | every 1.4 min | 6 | more often |
| The Legendary | 1, certain, from the Ford-Warden | 8/8 runs | Warden's ground gear: 2 | on |
| Levels | 1-5 in the hour | gate level 5 | | on |

The Warden's drops, all tier II runs: Legendary drowned_coat x40, Rare judgement_disc_item x4, Uncommon bone_amulet x3, Uncommon travelers_cloak x3, Common iron_helm x2, Common judgement_disc_item x2, Common leather_cap x2, Rare padded_jerkin x2, Common silver_ring x2, Uncommon padded_jerkin x2, Epic watch_buckler x2, Rare watch_buckler x1, Epic travelers_cloak x1, Rare rime_rod x1, Epic leather_cap x1, Common chain_shirt x1, Uncommon ember_staff x1, Uncommon worn_oathblade x1, Rare copper_ring x1, Common watch_buckler x1, Epic silver_ring x1, Common gyre_axes x1, Common copper_ring x1, Common bone_amulet x1, Epic judgement_disc_item x1, Rare worn_oathblade x1, Rare chain_shirt x1.

## The campaign gates (7.1, tier II)

| Gate | Measured | Verdict |
|---|---|---|
| The human rises 1-3 an hour | 3.5/hr (median; runs 0,0,1,0,0,1,1,1) | fail |
| The deft at most once an hour | 5.8/hr (worst run 7.6) | fail |
| The standing bot falls to every champion pack | falls 0,1,1,0,0,0,1,1; fell at the Post 0/8, the Barrow 0/8, by day 4/8 | fail (5 champions: a fall each needs 5+) |
| Levels within ±20% (level 5 by the hour's end) | gate level 5 | pass |
| Drops within ±20% (~25 shown an hour) | 68/hr | fail |
| (kills within ±20%, ~500 an hour) | 1455/hr | fail |

**Read the rates with the zone's length:** the whole Low Ford plays in about 7.8 minutes (with films), so every per-hour rate is that run scaled by about 7.7x. One rise in a run reads as 7.7 an hour, so the rise gates cannot pass or fail fairly until the first hour is an hour of ground (see The ground). Per run, the totals (kills, packs, champions, gear, level 5 at the gate) are the numbers to set against the table's first hour: today's zone gives the first hour's levels and champions in an eighth of its time, and about a third of its kills, packs and gear.

Gold: the bots take only what they walk over (the coins are not pulled to her by day); the column gives what she took and what fell.

## The ground

- The route (the goals' walk: the camp, the night's 10 beats, the ford; the day's start, its 8 beats, the gate): **147 m by night + 213 m by day = 360 m**. (The meta's ROAD path, the camp to the ford: 262 m.)
- Walked by the human bot (tier II median), fights' footwork included: 1080 m by night, 687 m by day, 1767 m in all (4.9x the route).
- Packs placed: 10 by night, 6 by day, 16 in all: **4.4 packs per 100 m of route** (6.8 by night, 2.8 by day).
- The first hour's ~40 packs at today's density: **899 m** of route (+540 m, +24 packs more than today).
- The zone at about 45 minutes: today it plays in 7.8 min with films (46 m of route a minute, everything in it). At today's pace and density, 45 minutes is **2070 m** of route (5.8x today, +1710 m more), holding **92 packs** (+76 more).
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
| boars | 16 s, L4 | 14 s, L4 | 16 s, L4 | 16 s, L4 | 15 s, L4 | 17 s, L4 | 15 s, L4 |
| kerchiefs | 39 s, L4 | 36 s, L4 | 32 s, L4 | 43 s, L4 | 28 s, L4 | 28 s, L4 | 28 s, L4 |
| road_ambush | 5 s, L4 | 6 s, L4 | 6 s, L4 | 6 s, L4 | 6 s, L4 | 5 s, L4 | 5 s, L4 |
| wallow | 22 s, L4 | 20 s, L4 | 22 s, L4 | 22 s, L4 | 20 s, L4 | 21 s, L4 | 21 s, L4 |
| track_ambush | 8 s, L4 | 7 s, L5 | 8 s, L4 | 7 s, L4 | 8 s, L4 | 6 s, L4 | 7 s, L4 |
| wolves | 0 s, L5 | 0 s, L5 | 0 s, L5 | 0 s, L5 | 0 s, L4 | 0 s, L5 | 0 s, L5 |
| stage Wake | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s | 3 s |
| stage Rising | 0 s | 0 s | 0 s | 0 s | 0 s | 0 s | 0 s |
| stage Road | 2 s | 2 s | 2 s | 2 s | 6 s | 2 s | 2 s |
| stage Ambush | 25 s | 25 s | 25 s | 24 s | 12 s | 15 s | 16 s |
| stage Road2 | 3 s | 3 s | 2 s | 3 s | 4 s | 2 s | 3 s |
| stage Post | 30 s | 30 s | 27 s | 30 s | 32 s | 37 s | 26 s |
| stage Barrow | 38 s | 39 s | 38 s | 40 s | 38 s | 39 s | 37 s |
| stage ToFord | 12 s | 9 s | 11 s | 10 s | 12 s | 9 s | 10 s |
| stage Intro | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s | 6 s |
| stage Boss | 155 s | 163 s | 140 s | 131 s | 67 s | 151 s | 152 s |
| stage Victory | 13 s | 13 s | 13 s | 13 s | 13 s | 13 s | 13 s |
| stage Dawn | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s | 10 s |
| stage Exit | 134 s | 132 s | 131 s | 149 s | 115 s | 116 s | 118 s |

## Quiet between beats (median seconds from the previous beat's down to this beat's wake; negative = woke before the last fell)

| Beat (after the one before it in the data) | II human | II careless | II deft | II plain | II standing | I human | I deft |
|---|---|---|---|---|---|---|---|
| n_three (after n_lone) | 1.1 s (8) | 1.1 s (8) | 1.1 s (8) | 1.1 s (8) | 1.2 s (8) | 1.1 s (8) | 1.1 s (8) |
| n_first (after n_three) | 0.8 s (8) | 0.8 s (8) | 0.8 s (8) | 0.8 s (8) | 1.3 s (8) | 0.9 s (8) | 0.9 s (8) |
| n_cart (after n_first) | 0.8 s (8) | 0.8 s (8) | 0.8 s (8) | 0.8 s (8) | 1.3 s (8) | 1.1 s (8) | 0.8 s (8) |
| n_road1 (after n_cart) | -19.2 s (8) | -19.2 s (8) | -12.1 s (8) | -18.4 s (8) | -10.5 s (8) | -10.2 s (8) | -6.8 s (8) |
| n_road2 (after n_road1) | -3.0 s (8) | -3.0 s (8) | -6.3 s (8) | -3.0 s (8) | -1.2 s (8) | 1.7 s (8) | 3.7 s (8) |
| n_post (after n_road2) | 1.5 s (8) | 1.5 s (8) | 0.8 s (8) | 1.5 s (8) | 2.0 s (8) | -0.5 s (8) | -0.2 s (8) |
| n_road3 (after n_post) | 21.0 s (8) | 21.7 s (8) | 16.3 s (8) | 19.7 s (8) | 18.6 s (8) | 21.8 s (7) | 17.2 s (8) |
| n_road4 (after n_road3) | 0.3 s (8) | 0.3 s (8) | 0.8 s (8) | 1.2 s (8) | 2.8 s (8) | 0.9 s (7) | 0.8 s (8) |
| n_ford (after n_road4) | 32.2 s (8) | 32.4 s (8) | 34.7 s (8) | 34.5 s (8) | 39.2 s (6) | 35.1 s (7) | 31.5 s (8) |
| boars (after n_ford) | 190.6 s (8) | 199.6 s (8) | 179.7 s (8) | 144.2 s (7) | 96.1 s (6) | 184.0 s (7) | 186.2 s (8) |
| kerchiefs (after boars) | 7.0 s (8) | 6.4 s (8) | 7.3 s (8) | 6.5 s (7) | 6.7 s (8) | 6.3 s (7) | 6.2 s (8) |
| road_ambush (after kerchiefs) | 3.6 s (8) | 4.4 s (8) | 4.4 s (8) | 4.7 s (6) | 4.5 s (8) | 3.8 s (7) | 4.1 s (8) |
| wallow (after road_ambush) | 13.2 s (8) | 14.2 s (8) | 10.5 s (7) | 13.0 s (6) | 13.3 s (8) | 13.0 s (7) | 12.6 s (8) |
| track_ambush (after wallow) | 3.5 s (8) | 4.5 s (8) | 3.5 s (7) | 3.6 s (6) | 3.1 s (8) | 3.7 s (7) | 3.2 s (8) |
| wolves (after track_ambush) | 5.7 s (8) | 5.7 s (8) | 5.6 s (7) | 5.5 s (6) | 5.4 s (8) | 6.5 s (7) | 5.3 s (8) |

Pack wakes while a champion (not its own) lived within 25 m of her: II human: 24 in 8 runs (n_road2 x8, n_post x8, n_road4 x3, n_ford x3, n_road3 x1, n_cart x1); II careless: 25 in 8 runs (n_road2 x8, n_post x8, n_road4 x4, n_ford x3, n_road3 x1, n_cart x1); II deft: 26 in 8 runs (n_road2 x8, n_post x8, n_road3 x3, n_road4 x4, n_ford x2, n_road1 x1); II plain: 25 in 8 runs (n_road2 x8, n_post x8, n_road4 x5, n_ford x2, n_road3 x1, n_cart x1); II standing: 20 in 8 runs (n_road2 x8, n_post x8, n_road4 x4); I human: 23 in 8 runs (n_road2 x8, n_post x8, n_road3 x2, n_road4 x3, n_cart x1, n_ford x1); I deft: 23 in 8 runs (n_road2 x7, n_post x8, n_ford x3, n_cart x1, n_road1 x1, n_road4 x3).

## Falls, rises and runs that did not get through

- II human: falls by stage: Exit 3, Boss 1; risen at: act1.post1 1, lowford.bank 2, lowford.door 1.
- II careless: falls by stage: Exit 3, Boss 2; risen at: act1.post1 1, lowford.bank 2, lowford.door 2.
- II deft: falls by stage: Boss 5; risen at: lowford.door 5.
- II plain: falls by stage: Exit 1, Boss 3; risen at: lowford.bank 1, lowford.door 3.
  - s5: stuck: Exit beat road_ambush at (48,-84) goal (22,-87) (after 21.2 min)
  - s7: stuck: Exit beat boars at (1,-34) goal (1,-79) (after 9.9 min)
- II standing: falls by stage: Exit 4; risen at: act1.post1 4.
- I human: falls by stage: none; risen at: none.
  - s7: stuck: Post beat n_road3 at (16,38) goal (10,32) (after 5.8 min)
- I deft: falls by stage: none; risen at: none.
