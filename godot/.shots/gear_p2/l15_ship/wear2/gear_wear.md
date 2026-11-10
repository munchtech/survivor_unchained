# gear_wear: godot\art\gear\out\body_p1

33 clips, step 2, grid 2.5 mm, 3 tests, 553 s. Garment tuck as HerWear lays it. OUT>2: her skin / the inner piece past the outer face by more than 2 mm (what shows), as area.

| kind | tests | with OUT>2 | OUT>2 mm^2 (all clips) |
|---|---:|---:|---:|
| skin | 3 | 3 | 3238 |

## Worst 20 (clip, test)

| clip | test | kind | OUT>2 mm^2 | worst mm | frame | region |
|---|---|---|---:|---:|---:|---|
| axe_heavy | skin under plate_top_etched | skin | 1712 | 43.24 | 10 | upper arm R (upperarm_twist_03_r) |
| axe_fore | skin under plate_top_etched | skin | 1528 | 34.39 | 4 | upper arm R (upperarm_twist_03_r) |
| axe_fore | skin under plate_top_gilded | skin | 377 | 43.06 | 6 | upper arm R (upperarm_twist_03_r) |
| Jog_Fwd | skin under plate_top_etched | skin | 289 | 44.44 | 12 | torso (spine_04) |
| axe_back | skin under plate_top_etched | skin | 194 | 5.4 | 2 | upper arm R (upperarm_twist_03_r) |
| Jog_Fwd | skin under plate_top_gilded | skin | 162 | 9.08 | 2 | torso (spine_04) |
| crossbow_shoot | skin under plate_top_etched | skin | 148 | 3.13 | 8 | shoulder L (clavicle_l) |
| Jog_Fwd | skin under plate_top_plain | skin | 81 | 5.28 | 4 | torso (spine_04) |
| run_reaver | skin under plate_top_etched | skin | 77 | 21.86 | 8 | shoulder R (clavicle_r) |
| sword_back | skin under plate_top_plain | skin | 76 | 9.41 | 6 | shoulder R (clavicle_r) |
| sword_fore | skin under plate_top_plain | skin | 76 | 8.92 | 0 | shoulder R (clavicle_r) |
| daggers_back | skin under plate_top_plain | skin | 76 | 8.87 | 4 | shoulder R (clavicle_r) |
| cast_flick | skin under plate_top_plain | skin | 76 | 5.48 | 0 | shoulder R (clavicle_r) |
| crossbow_shoot | skin under plate_top_plain | skin | 73 | 2.8 | 8 | shoulder L (clavicle_l) |
| axe_heavy | skin under plate_top_plain | skin | 71 | 2.63 | 10 | shoulder R (clavicle_r) |
| sword_heavy | skin under plate_top_etched | skin | 71 | 2.09 | 4 | shoulder R (clavicle_r) |
| axe_back | skin under plate_top_gilded | skin | 70 | 2.59 | 0 | shoulder R (clavicle_r) |

## Where it shows

close: through over 2 mm in the town / idle / look / talk clips (16); play: over 6 mm in the others (17); ex: without Jog_Fwd. mm^2.

| test | close | play | play ex |
|---|---:|---:|---:|
| skin under plate_top_etched | 0 | 2028 | 1820 |
| skin under plate_top_gilded | 0 | 458 | 377 |
| skin under plate_top_plain | 0 | 76 | 76 |

## What one frame shows

The worst single frame's through area (mm^2) past each depth, its clip and frame: close views at 2 mm, play (ex) at 3 and 6 mm. One play pixel is 169 mm^2.

| test | close 2 mm | play 3 mm | play 6 mm |
|---|---|---|---|
| skin under plate_top_etched | 0 | 1624 (axe_heavy f10) | 1624 (axe_heavy f10) |
| skin under plate_top_gilded | 0 | 310 (axe_fore f8) | 310 (axe_fore f8) |
| skin under plate_top_plain | 0 | 76 (cast_flick f0) | 76 (daggers_back f4) |

## Through or beside

under: her skin UNDER the piece at rest (its footprint), through it; beside: skin from beside the piece over it (rigid parts only). mm^2, under / beside. Frames: the worst single frame (close 2 mm, play ex 6 mm).

| test | close ex | play ex | close frame | play frame |
|---|---|---|---|---|
| skin under plate_top_etched | 0 / 0 | 0 / 1820 | 0 / 0 | 0 / 1624 |
| skin under plate_top_gilded | 0 / 0 | 0 / 377 | 0 / 0 | 0 / 310 |
| skin under plate_top_plain | 0 / 0 | 76 / 0 | 0 / 0 | 76 / 0 |
