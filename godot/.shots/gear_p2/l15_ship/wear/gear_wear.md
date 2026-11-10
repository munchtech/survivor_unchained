# gear_wear: godot\art\gear\out\body_p1

33 clips, step 2, grid 2.5 mm, 3 tests, 593 s. Garment tuck as HerWear lays it. OUT>2: her skin / the inner piece past the outer face by more than 2 mm (what shows), as area.

| kind | tests | with OUT>2 | OUT>2 mm^2 (all clips) |
|---|---:|---:|---:|
| skin | 3 | 3 | 3188 |

## Worst 20 (clip, test)

| clip | test | kind | OUT>2 mm^2 | worst mm | frame | region |
|---|---|---|---:|---:|---:|---|
| axe_fore | skin under plate_top_plain | skin | 1100 | 44.41 | 6 | upper arm R (upperarm_twist_03_r) |
| axe_fore | skin under plate_top_gilded | skin | 776 | 43.77 | 6 | upper arm R (upperarm_twist_03_r) |
| axe_heavy | skin under plate_top_plain | skin | 656 | 44.67 | 12 | upper arm R (upperarm_twist_03_r) |
| cast_bolt | skin under plate_top_plain | skin | 654 | 14.43 | 18 | torso (spine_04) |
| run_arcanist | skin under plate_top_plain | skin | 632 | 14.46 | 0 | torso (spine_04) |
| run_reaver_town | skin under plate_top_plain | skin | 632 | 14.45 | 0 | torso (spine_04) |
| run_reaver | skin under plate_top_plain | skin | 632 | 14.3 | 2 | torso (spine_04) |
| daggers_heavy | skin under plate_top_plain | skin | 632 | 14.2 | 20 | torso (spine_04) |
| Jog_Fwd | skin under plate_top_plain | skin | 625 | 13.99 | 20 | torso (spine_04) |
| axe_back | skin under plate_top_plain | skin | 620 | 14.26 | 16 | torso (spine_04) |
| cast_flick | skin under plate_top_plain | skin | 620 | 14.25 | 18 | torso (spine_04) |
| daggers_back | skin under plate_top_plain | skin | 620 | 14.19 | 16 | torso (spine_04) |
| run_arcanist_town | skin under plate_top_plain | skin | 550 | 14.41 | 0 | torso (spine_04) |
| run_stalker | skin under plate_top_plain | skin | 550 | 14.41 | 0 | torso (spine_04) |
| run_stalker_town | skin under plate_top_plain | skin | 550 | 14.41 | 0 | torso (spine_04) |
| run_warden | skin under plate_top_plain | skin | 550 | 14.33 | 6 | torso (spine_04) |
| sword_heavy | skin under plate_top_plain | skin | 550 | 14.29 | 22 | torso (spine_04) |
| sword_fore | skin under plate_top_plain | skin | 550 | 14.28 | 18 | torso (spine_04) |
| idle_stalker_town | skin under plate_top_plain | skin | 550 | 14.23 | 96 | torso (spine_04) |
| sword_back | skin under plate_top_plain | skin | 550 | 14.21 | 2 | torso (spine_04) |

## Where it shows

close: through over 2 mm in the town / idle / look / talk clips (16); play: over 6 mm in the others (17); ex: without Jog_Fwd. mm^2.

| test | close | play | play ex |
|---|---:|---:|---:|
| skin under plate_top_plain | 632 | 732 | 651 |
| skin under plate_top_gilded | 104 | 856 | 776 |
| skin under plate_top_etched | 367 | 0 | 0 |

## What one frame shows

The worst single frame's through area (mm^2) past each depth, its clip and frame: close views at 2 mm, play (ex) at 3 and 6 mm. One play pixel is 169 mm^2.

| test | close 2 mm | play 3 mm | play 6 mm |
|---|---|---|---|
| skin under plate_top_gilded | 104 (idle_arcanist_look f0) | 738 (axe_fore f8) | 738 (axe_fore f8) |
| skin under plate_top_plain | 632 (run_reaver_town f0) | 841 (axe_fore f6) | 651 (axe_fore f6) |
| skin under plate_top_etched | 367 (run_arcanist_town f8) | 263 (crossbow_shoot f6) | 0 |

## Through or beside

under: her skin UNDER the piece at rest (its footprint), through it; beside: skin from beside the piece over it (rigid parts only). mm^2, under / beside. Frames: the worst single frame (close 2 mm, play ex 6 mm).

| test | close ex | play ex | close frame | play frame |
|---|---|---|---|---|
| skin under plate_top_plain | 632 / 0 | 101 / 550 | 632 / 0 | 101 / 551 |
| skin under plate_top_gilded | 104 / 0 | 104 / 672 | 104 / 0 | 104 / 634 |
| skin under plate_top_etched | 367 / 0 | 0 / 0 | 367 / 0 | 0 / 0 |
