# fair_a: A's posed skin faired at the source (judge fix 1 attempt 3; lead 21's max solver, 10 Nov): BUILT, NOT MET, key absent (inert)

## Method (tools/body/fair_a.py, general: rest V0, T, posed V, params; no ids; seams welded)
- Seeds: inner edge |fold| > fold_deg (45) and > rest + beyond_deg (20), or a triangle flipped against its rest normal turned by the smoothed rotations. `where` limits seeds (Her: A vertices the region's carrier reads). No seed: V returned bit for bit.
- Patch = seeds + `rings`; outer `soft` rings pulled to posed (smoothstep to alpha), next ring held hard. Rotations: "smooth" (posed rotations, rot_passes Jacobi passes inside, ring held) or "harmonic" (filled from the ring). Poisson of rest edges turned by them + alpha_core pull everywhere; volume: mean offset along smooth normals held 0 (Lagrange). Optional ARAP iters with a flip barrier. `rounds`: leftovers re-seed (+grow rings).
- Hook: `Her.part`, after A is posed: `if cfg.get("fair_a")` -> `fair_a.her_hook` (config {"regions": ["girdle_{s}"], "params": {...}}; h.fair_on False = off). Cache out/fair_a (git-ignored).

## (a) on A, params {"rings": 3, "soft": 2, "alpha": 0.5, "alpha_core": 0.02, "rot_passes": 10, "rounds": 2, "grow": 1} (scratch pa.py)
| pose | patch | >45 before->after (rest) | >90 | flipped | offset mean mm | move p95/max mm |
|---|---|---|---|---|---|---|
| abd120:l | 2631 | 362->77 (63) | 102->15 | 45->6 | 0.03 | 9.2/14.0 |
| abd150:l | 1106 | 62->47 (31) | 11->9 | 6->5 | 0.05 | 5.8/23.0 |
| abd170:l | 1433 | 92->47 (34) | 15->9 | 8->5 | 0.06 | 8.1/31.7 |
| flex170:l | 1405 | 73->46 (34) | 11->9 | 7->5 | 0.06 | 6.9/30.2 |
| iron_vow@72:l | 1946 | 257->85 (35) | 71->12 | 66->3 | 0.11 | 12.4/21.3 |
| leap@6:r | 1588 | 181->24 (17) | 42->3 | 37->0 | 0.06 | 8.7/19.3 |
| leap@9:r | 2452 | 259->48 (27) | 65->7 | 27->4 | 0.12 | 13.4/22.3 |
| leap@12:r | 2885 | 325->102 (95) | 93->5 | 53->0 | 0.08 | 12.2/22.0 |
| leap@19:r | 1157 | 107->15 (0) | 44->4 | 33->0 | 0.10 | 11.4/35.2 |
- iron_vow@75:l is not in poses.npz. Outside the patch bit for bit on every pose. "harmonic" (first try): flips 0 but moves p95 17-30 mm, >45 not cured on abd150/flex170: dropped.
- NOT MET: flipped 3-6 left on 6 poses; >45 at rest's level only on abd120, leap@6/@12. Max moves 14-35 mm at a few points (check where before (b)).
- The rule also fires on x:add0:l (arm down): T18 must run rule-off if the key goes on.

## (b)-(d) not run (context cap). (d) with the key absent: see the commit. (e) ~2.5 s a fair, cached compose 0.85 s; cache ~28 KB a pose-region (~8 MB for 141 x 2).
## Next: per-pose flips left sit where? (try rounds 3, rot_passes 20, ARAP iters 4); then (b) shift, (c) meas.py + turned (turned uses pose_ref: hook it too, run live, not --snap), T26.
