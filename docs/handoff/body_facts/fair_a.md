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

## Attempt 5 (numeric solver, 10 Nov): `shrink`, the cap ring on iron_vow@72:l; NOT LIVE (2 of 4 acceptance lines missed)
- New keyword `shrink` (default None, P4 reproduces bit for bit: iron_vow 277->131, flip 1): with rot "fill", stretch false, edges "blend", the crumple's rest edges turned are scaled by `shrink`, so the core is solved in TENSION (a taut membrane on its ring does not buckle; full-length rest edges pushed into the compressed hollow fold).
- P5 = P4 + {"rings": 4, "shrink": 0.5}. Probe pb.py, same columns as the job-1 table:
| pose | patch | >45 (rest, cap) | flip | move p95/max | off smooth p95/max | met |
|---|---|---|---|---|---|---|
| abd120:l | 4342 | 387->44 (81, 89) | 45->0 | 7.6/15.0 | 2.2/5.1 (was 4.3) | yes, off worse |
| abd150:l | 1373 | 84->41 (70, 77) | 15->0 | 4.9/13.0 | 1.7/3.6 | yes |
| abd170:l | 1674 | 112->42 (73, 80) | 17->0 | 6.6/22.5 | 1.7/3.7 | yes |
| flex170:l | 1582 | 93->42 (73, 80) | 16->0 | 6.2/21.1 | 1.7/3.7 | yes |
| iron_vow@72:l | 2046 | 277->81 (76, 84) | 72->0 | 9.4/16.9 | 1.9/3.3 | yes (was NO) |
| leap@6:r | 2427 | 254->89 (102, 112) | 41->0 | 5.7/15.4 | 1.3/5.2 | yes |
| leap@9:r | 4011 | 324->47 (107, 118) | 31->0 | 10.4/26.8 | 2.7/7.3 | yes |
| leap@12:r | 4040 | 333->47 (107, 118) | 53->0 | 9.4/25.2 | 2.5/7.4 (was 6.8) | yes, off worse |
| leap@19:r | 2414 | 108->10 (12, 13) | 33->0 | 10.7/33.3 | 1.5/4.7 (was 3.3) | yes (was NO), off worse |
- Notch (2) box on the composed B surface (notch probe, fair-on): P4 >45 51, >120 6 (max 177); P5 >45 42, >120 ONE (5889-8236 at 128; 5664-5665 119). Under it A's core keeps two folds (A 38088-1806 -85 -> -115 posed -> faired; A 40339-40368 9 -> 148): the filled rotation field jumps 50-122 deg across one edge there (the polar of a near-singular harmonic-filled gradient).
- Lost (code removed): `grow` 2 / `rings` 4 alone (iron 117-121, B box >120 2-7); a measured per-vertex scale sqrt|det F| (~1, no help; note: `_grad` is area-weighted, unnormalised, so `stretch` true scaled edges by area: why it "flattened"); shrink 0.3/0.4/0.7 (flips or 97); flip barrier reweight x4/x10 (never kept); Jacobi passes on R after the polar (4-20: B box 124-131); rotation-vector fill about the ring mean (worse, iron 112); fold_deg 30-35, beyond 10, c_core 0/2, c_soft 1/3, soft 3, alpha_core 0, alpha_mid 0.1, rot_passes 30.
- Left: (a) the B box line needs the core's rotation jump cured (a fill that stays off the singular set, e.g. a rotation fill with the jump edges' weight cut, or seeds there pulled to posed); (c) smooth-skin off max worse on abd120 / leap@12 / leap@19 (the patch grows with rings 4: try shrink per crumple share only, or rings 4 with alpha_mid 0.3).

## Attempt 6 (numeric solver, 10 Nov): NOT LIVE; P5 stays. See strip_rest.md "Lay 9".
- Left turned band triangles (hadd40 259, flex120 287, iron_vow@72 109) sit INSIDE the patch: tight 2-3-row creases (feet 1.4-4.3 mm posed, 9-13 at rest, normals opposed) the per-edge test half-sees.
- pb.py poses A by the girdle only; strip_rest rides the whole pose (`pose_ref`), where P5 misses the cap on hadd40 (88/81, flip 6) and iron_vow (252/229, flip 1).
- New, off by default: `fair(V, where, extra)` (caller's seed points; cache key unchanged when None). Lost: `mend` (bi/harmonic leftover re-fill: bridges the crease, +2..20 flips), extra-seed iteration, shrink 0.35, rounds 10, grow 2, iters 12.
- Next: a crease-aware seed (normal turn over 2-3 rows) with a contact-flattened target; judge the nine on `pose_ref`.

## Attempt 7 (lead 23's solver): the cap-band curvature rule; NOT LIVE (first setting fails; sweep not done, budget out)
- New keyword `cap` (default None: P5 bit for bit, the cache tag and key unchanged): `CAP` keys lo/hi (band: the rigid bone chain's A skin share), h_min (1/m), flat, rim, rings, grow, soft, turn, alpha, passes; bone/chain read by the hooks. `Fair.curv(X, rings)` = smoothed cotangent mean curvature (rotation free, so the rigid-carried rest cap's H is H0 = curv(P0)); `Fair.cap_share` fires on band & H0 > h_min & (H < flat x H0, or rim H < -h_min); the fired set grown `grow` rows = share 1, smoothstep 0 over `soft`. There the target edges are rest edges turned by polar((1-turn) R_posed + turn R_rigid), pull `alpha`, the cap's volume held. Wiring: `rigid_of(h, Ga, sides)`; `her_hook(h, rg, Va, Ga)` (Her.part passes A's Ga), `ref_hook(h, Va, Ga)` (strip_rest.pose_a).
- Facts (A, girdle part pose; probes scratch_p1_l23/cap1.py, cap2.py): the notch (2) box on A is carried by clavicle 0-0.62, upperarm_share 0.16-0.63, twist_01 0.04-0.34 (upperarm_l itself 0). There A's smoothed H is NOT below rest (rest p50 5.3/m, A 19.7, P5 27.7); A's normals sit 99 deg (p50) off upperarm_l's rigid-carried rest normals.
- First setting (chain upperarm_l + share + twists, defaults above, turn 1.0): iron_vow@72:l fires 305 pts, patch 2046 -> 5397, >45 81 -> 254 (rest 80), flips 0 -> 58, move max 35 mm, cap H/H0 p50 0.89 -> 0.72: FAIL. abd150:l fires too (292): >45 63 (rest 79), flips 0 -> 1, H/H0 p50 0.62 -> 0.84.
- So the full rigid turn (~100 deg off posed in the blend band) tears the patch. Next: turn 0 to 0.3 (rest curvature in the posed frame), band hi 0.8, flat 0.35, rim off; then the acceptance list in the brief (iron_vow@70..74 etc.).

## Attempt 8 (lead 24's solver, 10 Nov): the curvature CEILING; NOT LIVE (P5 stays bit for bit, t22_row_tol kept)
- Code (off by default, commit a3b6309c4; key absent: tag b5c042ac971ca915 unchanged): CAP keys `ceil`/`add` (fire where the fair WITHOUT the cap, H_P5, exceeds ceil x max(H0, H_A) + add and h_min; flat/rim unused), `mode` "lap" (Fair._cap_lap: the cap kc > 0 re-solved on P5's surface by cotangent Laplacian coordinates, `reps` passes, pull `alpha` to P5, all else held), `target` "clip" (P5's own Laplacian, its normal part cut by `clip` x the excess over the ceiling: the ceiling itself) / "rest" (rest Laplacian turned by P5's rotations) / "posed" (A's own; also for mode edges), `spare` (crumple from the non-cap seeds only). Chain: clavicle_{s}, upperarm_share_{s}, upperarm_twist_01_{s}, hi 0.8. Probes: survivorsunchained_inputs/scratch_p1_l24/cap3.py (CAPS = JSON list), diag3.py, t22.py, accept.log.
- Pose names: iron_vow@70/73/74:l are not in poses.npz; @71:l and @72:l used.
- Mechanism found: the over-curved points (H_P5 > 1.2 max(H0, H_A), 200 on iron_vow@72:l) sit 0-4 rows from A's own bad seeds, i.e. inside P5's crumple solve (the taut core meeting the held ring). The extra >45 edges any cap setting makes are in the cap core (kc = 1; P5 48 there, rest 6).
- Edges mode with the ceiling (turn 0 / 0.3, rest or posed targets, spare): iron_vow@72:l >45 101-288, flips 2-77: lost. Lap "rest": >45 100-112, flips 0-6: lost. Lap "posed": >45 151-193: lost.
- Best two (lap, clip, ceil 1.0, hi 0.8). C1 = alpha 0.03, grow 2, soft 4, clip 1, reps 4; C2 = alpha 0.003, grow 3, soft 6, clip 1, reps 10. Columns P5 -> C1 / C2: >45 on the union patch, flips, move max mm, cap H/H0 p50 on the fixed over-curved set (A's own in brackets):
| pose | >45 | flips | move max | H/H0 p50 (A) |
|---|---|---|---|---|
| iron_vow@72:l | 85 -> 86 / 90 | 0 -> 0 / 0 | 16.9 -> 16.9 / 16.9 | 6.21 -> 5.04 / 3.35 (2.35) |
| iron_vow@71:l | 68 -> 69 / 70 | 1 -> 1 / 1 | 11.1 | 1.88 -> 1.71 / 1.37 (1.09) |
| iron_vow@78:l | 71 -> 70 / 72 | 0 | 9.6 | 2.07 -> 1.93 / 1.50 (1.08) |
| iron_vow@83:l | 6-7 -> 6 / 7 | 0 | 2.5 | 1.22 -> 1.17 / 1.10 |
| iron_vow@86:l | 2 -> 2 / 1 | 0 | 1.9 | (no set) |
| x:hadd40:l | 93 -> 90 / 96 | 7 -> 8 / 9 | 11.5 -> 11.6 | 3.98 -> 2.87 / 2.01 (0.61) |
| sword_heavy@10:l | 63 -> 63 / 63 | 0 | 7.7 | 2.45 -> 2.15 / 1.87 |
| cast_bolt@0:l | 2 -> 3 / 3 | 0 | 6.8 -> 6.7 | 5.83 -> 5.19 / 4.60 |
| crossbow_shoot@10:r | 19 -> 19 / 19 | 0 | 6.6 | 1.80 -> 1.75 / 1.62 |
| x:abd120:l | 44 -> 44 / 47 | 0 | 15.0 -> 14.9 | 2.11 -> 1.74 / 1.32 |
| x:abd150:l | 42-44 -> 42 / 44 | 0 | 13.0 | FIRES (266): 5.55 -> 5.04 / 3.75 |
| x:abd170:l | 42-45 -> 44 / 50 | 0 | 22.5 | 3.51 -> 3.03 / 2.41 |
| x:flex170:l | 42 -> 43 / 43 | 0 | 21.1 | 3.29 -> 2.78 / 2.08 |
| leap@6:r | 89 -> 90 / 91 | 0 | 15.4 | 2.62 -> 2.49 / 1.90 |
| leap@9:r | 47 -> 49 / 52 | 0 | 26.8 | 1.80 -> 1.65 / 1.46 |
| leap@12:r | 47 -> 48 / 49 | 0 | 25.2 | 2.26 -> 1.91 / 1.58 |
| leap@19:r | 12 -> 12 / 13 | 0 | 33.3 | 4.37 -> 3.53 / 2.84 |
- Harder pushes on iron_vow@72:l (reps 20, alpha 0.001-0.003, clip 1-1.5): H 27.5 -> 16.2 per m (A 14.2) but >45 99-110; rings 0 clip: flips 1, max 172. A monotone trade: each 1/m of H taken off the cap adds folds in its core.
- T22 (strip_rest.cmd_turned, iron_vow@72:l): band edge P5 1.97, C1 1.97, C2 1.98 (A's own 1.81, fill 2.07), though the cap fires in pose_ref (878 points). The band edge is a STRETCH ratio along the armpit map band (posed map edge / B rest), not a curvature: the cap ceiling cannot carry the t22_row_tol removal. The suite was not run (no setting to make live).
- Misses vs the acceptance: >45 over P5 on most rows (+1..+8), hadd40 flips 7 -> 8 / 9, abd150 fires, T22 1.97 vs the 1.96 needed (unmoved); iron_vow@72 move max 16.9 is P5's own (the cap adds 0).
- Next (if the lid stays open): the lid is P5's crumple core itself, so fix it there (the core's tension `shrink` per crumple share, or a biharmonic core solve so the core meets its ring with slope), and judge the T22 band edge as its own stretch problem in strip_rest's lay, not in fair_a.
