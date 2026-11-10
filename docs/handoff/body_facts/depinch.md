# De-pinch A before carrying it (judge fix 1, Gate T round 2; lead 21's solver, 10 Nov): BUILT, NOT MET, left OFF

## What A's "pinch" is, in numbers
Fold = fold_probe.dihedral on the model's triangles (valley +, the chest_fold.md convention; the bar is a fold of 15 deg or less = interior 165 or more). Composed target, rule off:
| pose (elev) | (5832,5833) | (5773,5833) | (2882,2932) | list edges abs(fold) > 45 / > 90 |
|---|---|---|---|---|
| abd120:l (120) | -29 | -17 | 13 | 125 / 40 |
| abd150:l (150) | 141 | 67 | 128 | 99 / 32 |
| abd170:l (170) | 155 | 74 | 147 | 100 / 36 |
| flex170:l (170) | -74 | 150 | 141 | 87 / 33 |
| iron_vow@72:l (109) | -83 | -92 | -21 | 307 / 99 |
It is not one pinched edge: the front armpit (md ids about 5770-5900 and 8220-8360) is a CRUMPLE of A's carry, valleys of 140-179 next to ridges of -100 to -170, in the fill (map off reads the same). B's published part pose is crumpled there too on iron_vow@72 (published folds up to -176). abd120's named edges are not pinched; its sharpest fill edges are (5429,5501) 168 and (5501,5564) 150. The 179-deg edge (5558,5617) at abd120 / abd150 is the armpit MAP's band (fill -18 / -5): not touched (strip_rest's).

## Built (tools/body/carried_target.py, inert while the key is absent)
`Her.depinched(rg, G, cf, Vr, Pg, info=None)`, run in `Her.part` after `relaxed`, before `mapped` (Pg now computed first, same value). Config `support["depinch"]` of an explicit region (wired in `Her.grow`: `rg.depinch = (lo, hi, rule)`, `rg.tris` = the region's own triangles): seeds = edges with fold over `fold_deg` and over B's fold by `fold_deg` (`ref` "rest" (default) or published part pose; `both`: abs, ridges too), never on the map's band when the map is on; pocket = `rows` around, minus the band; `fill` "frames" (Pocket, B's rest differentials turned by A's smoothed rotations, as `relaxed`) or "membrane" (delta 0, least-area); volume given back as a bump b (L_pp b = 1, 0 on the ring) along the fill's normals so the pocket's area-weighted mean normal offset is cf's, scaled by `volume`; `passes` rounds; smoothstep of elevation over `deg`, at or under lo bit for bit. It sits in HER as `"depinch_wip"` (NOT read): today's target is unchanged, `carried_target.py test` 83 PASS (as lead 20).

## Sweep (composed, rule on; named edges before -> after; list abs fold > 45 / > 90 before -> after; max move)
| variant | abd150 | abd170 | iron_vow@72:l | verdict |
|---|---|---|---|---|
| frames, rows 1, volume 1 | 13 / -2 / -14; new sharp 28 | 32 / 4 / -12 | -30 / -50, 353 -> 424 edges > 20, 30 mm | new creases |
| frames, both, rows 3, passes 2 | 14 / -1 / -6; > 45 99 -> 62 | 18 / 1 / -8 | -90 / -155; > 90 99 -> 159; 82 mm | worse on iron_vow |
| membrane, rows 2, passes 3, volume 0 | 11 / 3 / -1; 99 -> 31, 32 -> 15 | 12 / 2 / -2; 100 -> 56, 36 -> 21 | 12 / 40; 307 -> 222, 99 -> 65; 62 mm | folds best; VOLUME LOST |
| membrane, rows 2, passes 3, volume 1 | 16 / 0 / 2; 99 -> 63, 32 -> 39 | 16 / 1 / -3 | -134 / -180; bump 23-26 mm | the bump re-crumples |
abd120 (membrane vol 0): -29 / -17 / 13 -> 11 / 3 / 13, > 45 125 -> 34. flex170: -74 / 150 / 141 -> 28 / -3 / -1.
Shift for the best fold variant (membrane vol 0; `carried_target.py target --poses x:abd120:l,x:abd150:l,x:abd170:l,x:flex170:l,p4:iron_vow@72:l,x:add0:l`, then `region_shape.py shift --provider carried --target target_a_dev.npz --poses <same>`): fold_front worst in95 **21.9** (round 1 16.0), deltoid_cap **35.0** (15.5), median in95 deltoid **12.9** (bar 3.0). FAILS (d). target_a_dev.npz holds that run (dev only; target_a.npz untouched).

## Acceptance
(a) membrane vol 0 meets 15 deg on abd120/150/170 named edges, not flex170 (5832,5833) 28 or iron_vow (5773,5833) 40. (b) not run (edges). (c) 83 PASS with the rule OFF; T24 not written (no default to test). (d) FAILS (above). (e) iron_vow@72:l cap face NOT cured: its sharpest fill edges (5829,5889) 178, (5829,5830) 172, (5769,5829) 166 sit in a 300-edge crumple; no variant smooths it without a 30-80 mm move.

## Why it resists, and the next step (a solver)
A pocket fill keeps the rest layout's triangulation over a tangled boundary: the harmonic solve flips triangles at the ring (worse edges with 0-1 pocket ends: 17 + 26 of 66 at abd150), and a volume bump on a narrow pocket makes a new valley. The cure needs an untangle with a volume constraint, e.g. strip_rest's `untangle` / `lay2` (a re-laid band over A's surface, as the armpit map does), or an ARAP fill of the OFFSET from a smooth reference with turned-triangle and swept-volume terms. Measuring the pinch by named edges alone is gaming: use the list's abs-fold > 45 / > 90 counts, turned triangles and the shift bands. Probe: scratch `pinch.py` (below), env `DP='{json rule}'`.
Probe copy: C:/Users/munch/Desktop/survivorsunchained_inputs/scratch_p1_depinch/pinch.py.
JOB 2 (cast_bolt@3:r tick) not started (context).
