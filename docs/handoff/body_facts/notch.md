# The lead's three marks on the carried column, located (lead 21's helper, 10 Nov; dev target target_a_dev.npz)

Probes: `survivorsunchained_inputs/scratch_p1_notch/` (probe.py, neck.py, wjump.py; read-only). Live compose == dev Xc
(0.0 mm). Rest mm: +z front, -x her right. Vertex ids (md) are for checks only; the cures are rules.

## (1) heroic_leap@6:r / @9:r, upper-chest notch: B's SOURCE WEIGHTS, checkerboard neck_01 / spine_04
- Where: x -45..-69, y 1508-1531, z 43-75 (under the right clavicle). Edges 23033-23034, 23075-23140, 23204-23205 ...
- Cause: neighbouring vertices alternate neck_01 0.82-0.95 (23034, 23075, 23140, 23204, 23205, 22914) and
  spine_04 0.76-0.82 + trap 0.1-0.18 (23033, 23074, 23139, 23268). 28 front edges per side with a neck-chain weight jump
  > 0.5 (y 1510-1544; the left the same). The neck region's delta alternates with it: 30-34 mm on the
  neck_01 points, 1-3 mm on the spine_04 points (share 1.00, core, not stiff; neck relax on = off, cf = cr).
- Numbers, box of 179 edges, max dihedral / edges over 45: @6 published 153/26, composed 136/22, girdles only 147/27;
  @9 published 148/5, composed 124/17, neck only 137/15 (the neck region adds 12 on @9); @12 pub 77/4 -> 35/0; iron_vow@72:l 68/8 -> 18/0.
- Since when: not fair_a (on = off to the degree), not the map (map_off = on), not the neck relax (stretch rule, never
  fires: the edges are folded, not stretched), not a girdle border (girdle_r share 1.00 both ends). Not in A (own mesh).
- Cure: fix at the source: a weight relax on B's published skin where one bone chain's weight jumps > 0.5 between
  neighbours (Laplacian smoothing of the neck chain vs spine_04 split over those rows, sum kept). Target-side stopgap:
  give the neck `relax` a fold trigger (dihedral excess over rest, e.g. > 45) beside its ratio. Size: weight relax =
  medium (moves the published column; T18/T11 frozen copies re-baselined); fold trigger = small code + one keyword.

## (2) iron_vow@72:l, front of the deltoid cap: the fair_a rule (key-on), not the map, not a border
- Where: x 164-221, y 1438-1495, z 2-26. Edges (dihedral on / fair_off / map_off / published, rest):
  5889-8236 177 / -126 / 177 / -51 (10); 5889-8237 173 / 74 / 173 / 69; 5890-8237 -159 / -90; 5722-5723 -153 / -47;
  5664-5723 135 / -54; 5831-5891 -133 / -44; 5772-5832 -114 / -28. girdle_l share 1.00, delta 31-61 mm; neck share
  0.16-0.84 with 0.0 delta (no border). Box over 45: on 74, off 121, map_off 72, pub 134; flips on 84 / off 124.
- So fair_a halves the count but makes a short line of near-folded edges (135-177) at the cap front where it was 47-126: the faired patch's ring meeting the unfaired crumple (the fair's edge, the step). map only touches 5664-5665.
- Cure: in fair_a, blend the faired offset out over the soft rings by fold severity, or grow the patch (`grow` 1 -> 2,
  `rings` 3 -> 4) until the seed core is inside; or seed on the posed dihedral excess, not only > 45. Size: a keyword
  sweep first (small); if the core still folds, a solver job on the core's fairing (alpha_core 0.02).

## (3) cast_bolt@3:r, ribcage below the armpit: B's own published fold, nothing carried there
- Sharpest in x -210..-100, y 1230-1420: e24889-24890 -166, 24888-24975 157, 21680-24889 -151 at x -122..-126,
  y 1325-1332, z 64-67, same on published / composed / fair_off / map_off; girdle_r share 0.02-0.20, delta <= 0.3 mm
  (box over 45: composed 33, published 40). No share gradient or band border makes it.
- Cure: B's source skin (same weight-relax tool as (1)) or the girdle's ramp grown to cover it. Not checked: B weights there.

## (4) Relax fold trigger (lead 22's solver, 10 Nov): (1) and (3) cleared; shift, breast top and suite NOT run (context cap)
- Why not on cf: at leap@9 the neck's carry cf is smooth in box (1) (max 8 deg). The fold is B's published surface, and the placement M keeps it (M alternates spine_04 / spine_05 frames with the weights). So the trigger reads the COMPOSED surface.
- `Her.folded` (once a pose, after every region's carry, regions in name order so overlapping regions never fix one fold twice): an edge of the region's triangles over its rest dihedral by more than `fold` deg, on the rows a rule opens, seeds a pocket `rows` wide (share > 0, the map band held). The pocket is filled on the composed surface (Pocket, rotations polar(M) R) and goes back into cf through M^-1 / share, so delta, compose and target all see it. Keywords: `relax.fold` 45 (neck ~l.838, girdle gate2 ~l.818). Absent = bit for bit.
- (3): the seeds sit ON gate2's opened rows (0 rows away). The stage is shut by elevation (cast_bolt@3:r 65.8 deg, lo 90). Rule: `fold_open` [30, 45] on the girdle opens the stage by the fold itself, per point: the smoothstep of the worst seed excess within `rows`, max with the elevation's w. Continuous in the fold.
- Box (1) R, max / over 45, off -> on: leap@5 123/11->20/0, @6 136/22->11/0, @7 134/24->15/0, @8 128/23->17/0, @9 124/17->16/0, @10 122/12->15/0, @11 109/8->24/0, @12 35/0 (no trigger). Pops: 2nd difference on the fixed points, on vs off: +0..+11 mm, at @9 +19 (45->64); the fix itself jumps 8-26 mm frame to frame.
- Box (3) cast_bolt@2/3/4:r 166/22-23 -> 90/0 (90 = its rest crease). iron_vow@72:l boxL 106/9 -> 43/0.
- Bit for bit only where nothing seeds: x:add0:l. All other dev poses seed somewhere: the fix is 5.7-17.4 mm, region-wide over-45 counts fall, except cast_bolt@0:l 335 -> 338.
- Tests: T18 and T23 now run under `Her.fold_off()` (stored before it / the ratio rule alone). New T26: no region edge over fold on leap@6/@9:r and cast_bolt@3:r; x:add0:l bit for bit.
- Tests (11 Nov, solver 2): T9, T11 (h0.fold_on False) and T21 also run under fold_off: isolation tests of the carry / the stored pre-border targets / the map; all pass there (T9 was 29 mm, T11 to 3e-2 m, T21 outside-band 2-11 mm: the trigger's own fix).
- T26 neck (OPEN, real folds): the 42-48 edges are visible skin, not seams: no non-manifold edges, 3-6 rest slivers; the left/right deltoid top (upperarm_share 0.5-1), trap_r, and under the jaw (Head 0.5-0.7 / neck_02 / spine_04, y 1.59-1.61 m). Only 7-15 were over 45 with the trigger off: the fill itself makes the rest. They sit on compressed triangles (area < 0.5x rest on 21-40 of them; published has 41-67 region triangles under 0.2x). No harmonic variant clears them (rows 2-10, seed 15-45, rest delta x0-1, R none/smoothed, uniform weights, Taubin): best 15/27/19. Needs a compression-aware fill (bulge or tangential relaxation), not an edge-set rule.
- Pops (leap@4..12:r, @8 and @13 not in the pose files): the fix's own 2nd difference max 16-23 mm (p95 5-9), the carry's (trigger off - published) 11-72 mm, published (rigid jump) 105-497. A smoothstep fold_open [30,45] on the neck is WORSE (fix d2 20-30 mm, neck over-45 54/92/47): not adopted.
- (c) shift, 13 dev, target_a_l22r.npz rebuilt: worst in95 fold_front 7.7 (iron_vow@72:l) / deltoid 7.6 (leap@9:r) / breast 5.0 / trap 31.9, against 6.0 / 5.0 / 5.0 / 31.9. (d) p5 breast top: axe_heavy@9 l max dihedral 166 -> 176 composed (>2.5x 3 = 3); r 52 -> 47, >2.5x 4 -> 0; sword_heavy@9 l 168 -> 135, >2.5x 1 -> 0; r 47 = 47, >2.5x 4 -> 4 (max 6.24 -> 4.89).

## (5) Source weight relax (lead 23's solver, 10 Nov): mark (1) cured at the source
- Rule: `weights_topo.chain_relax` (build_topo stage_weights, after the a_* rules, before the head; both tiers). Spec
  her_b "weights" "chain_relax" {"chains": [["neck_01","neck_02","Head"]], "jump": 0.5, "rows": 2, "min_w": 0.01}; absent =
  bit for bit (round_37a without it: body.glb / play.glb POSITION, JOINTS, WEIGHTS = round_36's exactly). Seeds: points of
  quad edges and diagonals whose chain sum steps > jump; grown `rows` rings; harmonic fill (1 / length^2) of the whole
  weight row there, outside and the head ring held; < min_w dropped, renormalised, mirrored, capped (RULES cap 8).
- Build round_37 (published, backup of round_36's glbs/json in inputs/body/p1b_l23_pub_before): close 133 seeds,
  region 410 points (428 glb rows), chain edges > 0.5 159 -> 0, > 0.3 419 -> 52; play 123 / 323 pts, 151 -> 0, 281 -> 7.
  Published probe (wjump): > 0.5 0 / 0 a side, > 0.3 18 / 18. Rows sum 1 (4.5e-8, float32); max influences 8 = 8 (changed
  rows median 4 -> 5); ring_weight_step_max 1.1e-16 (as before); head and every other row unchanged; positions unchanged.
- The neck region's `fold` trigger is OFF (carried_target HER, ratio 2.4 rows 2 kept); the girdle's stays.
- Box (1) right / mirrored left, max dihedral / edges > 45 (published; composed), before trigger-off -> after:
  @5 137/25; 123/11 -> 15/0; 11/0 | L 43/0; 25/0 -> 27/0; 12/0. @6 153/26; 136/22 -> 15/0; 17/0 | L 28/0 -> 13/0.
  @7 167/18; 134/24 -> 15/0; 20/0 | L 37/0 -> 15/0. @8 177/10; 128/25 -> 13/0; 20/0 | L 98/8 -> 14/0.
  @9 148/5; 124/17 -> 16/0; 16/0 | L 161/8; 118/12 -> 30/0; 13/0. @10 109/4; 122/12 -> 19/0; 14/0 | L 125/18 -> 16/0.
  @11 87/4; 109/8 -> 19/0; 13/0 | L 136/25; 127/25 -> 29/0; 21/0. (The old trigger got 11-24/0 on the right only.)
- Box (3) cast_bolt@2/3/4:r (x -210..-100, y 1230-1420, all z): unchanged, published 166/45, composed (girdle trigger)
  93/14-16. No bone has a weight jump > 0.5 there: (3) is not a checkerboard; the skin's shape or the clip.
- Neck region, T26's metric (fold_tris, opened rows, past rest > 45) heroic_leap@6 / @9 / cast_bolt@3: old body trigger
  on 40 / 53 / 42, old trigger off 135 / 157 / 47, new (off) 79 / 91 / 47. What is left sits outside box (1): the deltoid
  cap front x +-200-225 y 1450-1500 (mark 2's zone), the throat x 0+-50 y 1600-1625, the shoulder top x +-125 y 1525.
- Other per-bone jumps > 0.5 (not relaxed; seen by the rule's report): pelvis / spine_01 across the lower back (230 /
  135 edges, y 875-1137, z < -85), upperarm_share (92 a side) and trap (64) behind the shoulder, thigh / thigh_share
  (28 / 13) at the back of the hip. Candidates for "chains" if they fold in game; not checked posed.
- Also moved: publish copied round_37's passing bake (ao, curvature, thickness; the sidecar normal.png now equals the
  glb's embedded one); the glbs' embedded images are unchanged. pieces.json gained "carried_by_ref" (code since round_36).
