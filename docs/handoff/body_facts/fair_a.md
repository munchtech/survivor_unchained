# fair_a: A's posed skin faired at the source (judge fix 1 attempt 3, lead 21's max solvers, 10 Nov): job 1 at 7/9 poses, key absent (inert)

## Method (tools/body/fair_a.py, general: rest V0, T, posed V, params; no ids; seams welded)
- Seeds: inner edge |fold| > fold_deg (45) and > rest + beyond_deg (20), or a triangle flipped against its rest normal turned by the smoothed rotations. `where` limits the first seeds (Her: the A vertices the region's carrier reads). No seed: V returned bit for bit.
- Patch = seeds + `rings`; outer `soft` rings pulled to posed, next ring held hard. Poisson of target edges + pull; volume: mean offset along smooth normals held 0 (Lagrange); optional guarded ARAP `iters` (a step kept only if flips and beyond-rest folds in the patch do not rise).
- Attempt 4 (solver 2) added, all off by default (old params reproduce the old table bit for bit):
  - `close`: before each solve, every bad element (flip or beyond-rest fold, not limited by `where`) on the patch or its ring becomes a seed, to closure. Cause it cures: most flips left were posed A's own flips just outside the patch, which the grown patch touched in its last round (tiny 0.1-0.4 mm2 triangles at patch row 4).
  - `edges: "blend"`: off the crumple the target edges are the POSED edges; inside it, the rest edges turned. Crumple share c = 1 within `c_core` rows of the seeds, smoothstep to 0 over `c_soft`. The volume is the crumple's (area x c). `alpha_mid`: the pull off the crumple. Cause it cures: rest edges everywhere drifted smooth skin off the posed surface (old off-surface on smooth skin up to 10 mm).
  - `rot: "fill"`: the per-vertex deformation gradients harmonic-filled over the crumple core (c = 1), then `rot_passes` Jacobi passes, polar. `stretch` true uses the filled gradient itself on the rest edges: it FLATTENS rest's sharp edges (>45 count fell to 31 against rest's 80) and adds flips: use false.
  - `dilate`: a round's leftovers enter the seeds grown by `grow` rows (re-seeding a core leftover alone repeats the same solve). `best`: the round kept is the one with the fewest (flipped, beyond-rest folds) on the patch and ring.
- Hook: `Her.part`, after A is posed: `if cfg.get("fair_a")` -> `fair_a.her_hook` (config {"regions": ["girdle_{s}"], "params": {...}}; h.fair_on False = off). Cache out/fair_a (git-ignored; the key holds the params).

## Job 1 table, params P4 = {"rings": 3, "soft": 2, "alpha": 0.5, "alpha_core": 0.02, "rot_passes": 10, "grow": 1, "close": true, "rot": "fill", "edges": "blend", "c_core": 1, "c_soft": 2, "alpha_mid": 0.2, "stretch": false, "dilate": true, "best": true, "rounds": 5, "iters": 4}
Probe: survivorsunchained_inputs/scratch_p1_fair_a4/pb.py (env FA = params, DIAG=1 for where). Counts are on the patch, so rest's count grows with the patch (cap = rest x 1.1).
| pose | patch | >45 before->after (rest, cap) | flipped | move p95/max mm | off posed surface, smooth skin p95/max mm | crumple max | met |
|---|---|---|---|---|---|---|---|
| abd120:l | 3370 | 385->69 (80, 88) | 45->0 | 8.2/14.9 | 1.7/4.3 | 8.3 | yes |
| abd150:l | 1897 | 87->74 (73, 80) | 15->0 | 4.3/14.7 | 1.8/4.9 | 5.5 | yes |
| abd170:l | 2413 | 114->69 (75, 82) | 17->0 | 4.5/23.7 | 1.5/4.6 | 4.5 | yes |
| flex170:l | 2790 | 95->69 (75, 82) | 16->0 | 4.5/23.3 | 1.2/4.8 | 5.8 | yes |
| iron_vow@72:l | 2169 | 277->131 (76, 84) | 72->1 | 11.5/20.1 | 4.0/7.9 | 11.9 | NO |
| leap@6:r | 2428 | 254->91 (102, 112) | 41->0 | 5.9/15.3 | 1.5/5.4 | 7.9 | yes |
| leap@9:r | 3533 | 314->89 (91, 100) | 30->0 | 10.6/24.4 | 2.8/7.7 | 10.0 | yes |
| leap@12:r | 3581 | 333->76 (107, 118) | 53->0 | 9.3/21.1 | 2.1/6.8 | 8.2 | yes |
| leap@19:r | 1634 | 108->14 (5, 6) | 33->0 | 10.5/34.9 | 1.5/3.3 | 6.6 | NO |
- "Smooth skin" = patch points more than 2 rows from the first seeds; "off" = distance to posed A's surface (dense samples), not the vertex move. Before P4 (solver 1's params) it was 2.7-10.3 mm.
- Job 2, where the 14-35 mm moves sit: inside the crumple. With DIAG, points moving > 10 mm are 75-98% within 2 rows of a seed (leap@19: 63 of 73), the rest at rows 3-4; their off-surface max is the crumple's (4-12 mm): they slide along the surface as the crumple opens. Bound on smooth skin: <= 5 mm on 6 poses; 6.8-7.9 mm on iron_vow@72, leap@9, leap@12 (rows 3-4 next to the crumple, patch rows 0-2): NOT bounded yet.
- Sweeps that lost (3 poses abd150, iron_vow@72, leap@19): c_core 2 (iron 152, flips 3, moves up); alpha_core 0 (moves p95 18 mm); wclamp [0.2, 5] (flips back on abd*); edges "blend" with rot "smooth" is close to "fill" (iron 110, 1 flip). Rounds without dilate repeat the same solve on core leftovers.

## Left (in order)
1. iron_vow@72:l and leap@19:r: the leftover >45 edges sit IN the core (rows 0-1 of the seeds), 1 core flip on iron_vow (6-7 mm2): the rest edges turned do not fit the compressed hollow. Next try: a flip barrier inside the Poisson (reweight edges of flipped or beyond-rest triangles x4 and re-solve, kept only if better), or let the core's target edges shorten to the hollow's boundary length (a scalar per-vertex stretch, not the full F, which flattens).
2. The smooth-skin bound on iron_vow / leap@9 / leap@12 (6.8-7.9 mm): raise alpha_mid only on rows past c_core + c_soft, or a hard hold past 2 rows of the crumple.
3. Not done (context cap): strip_rest's pose_ref hook (job 3: add the same her_hook call in Her.pose_ref, seeds limited to both girdle carriers' A vertices; run `strip_rest.py turned` live, not --snap), the key in HER, 4(a)-(c), T26. T18 must run rule-off when the key goes on (x:add0:l fires).

## Live run (lead 21's helper, 10 Nov): HER["fair_a"] = P4 on girdle_{s}, LIVE (WIP, pending the lead's look)
- Wiring: `Her.part` hook (as before); strip_rest `pose_a(h, G)` routes all 5 of its A poses (design, target, map targets, panels, turned) through `fair_a.ref_hook` (same rule, seeds on both girdle carriers' A vertices). Key absent / `--snap`: untouched. `Her.fair_off()` (map_off pattern).
- Dev target: 13 poses -> out/shoulder/target_a_dev.npz (4m36). target_a.npz not written. Sheet: out/shoulder/sheets/gate_l21_fair_half.jpg (gate_carried_half.jpg restored; copy gate_carried_half_before_l21fair.jpg). Not looked at.
- (a) edges on the dev file, 13 poses: both girdles 161 over (pocket 116, A's own 41, published 2, carrier 2); own side 154: OLD 153, NEW 1. Not the round-1 basis (76 / 293 was the full target_a.npz).
- (b) shift, worst in95 / median in95: fold_front 6.0 / 0.7 (r1 16.0), deltoid 5.0 / 1.6 (r1 15.5), breast 5.0 / 2.4 (r1 12.6), trap 31.9 / 2.6 (r1 31.9; iron_vow@72:l, unchanged).
- (c) strip_rest turned live, 19 poses (log out/shoulder/turned_l21_fair_live.log) vs lay 5 raw: turned total 10 vs 13. Better: leap@6:r 3->0, cast_bolt@6:l 3->0, crossbow@2:r 1->0. Worse: leap@9:r 0->1, cast_flick@8:r 1->2, idle@122:l 3->5 (w 0: the fill itself). FOLD max falls on abd120 105.7->81.8, leap@12 121.6->79.5, crossbow@2 148.4->99.4, cast_bolt@6 166.2->134.2, cast_flick 151.6->120.3, crossbow@0 140.3->120.4; rises on leap@9 137.3->158.7, leap@6 143.3->151.9, crossbow@10 94.7->117.6, idle@122 175.0->179.3; iron_vow 178.0->178.7.
- (d) x:add0:l: fires (girdle_l 4 seed edges, patch 103, 1 round): target and composed move 0.63 mm max vs key off.
- Tests: 79 PASS, 4 FAIL. T11 (h0 built without fair_a) and T18 (`fair_off`) now run rule-off as the frozen "of before" copies need; they failed on the rule alone (T18 add0 0.52 mm). T22 FAILS, limits unchanged: abd120:l 2.44 vs own 2.23, iron_vow@72:l 2.41 vs 1.85, leap@7:r turned 1 + 2.83 vs 2.65, leap@9:r turned 1 + 3.29 vs 2.88 (T22 was MET on lay 5 raw; the lay was built on raw A, A's own measure is now the faired one).
- Next (the lead): the look; then either re-lay strip_rest on faired A (`build`, its design now reads faired A) or keep the map's measures on raw A.
