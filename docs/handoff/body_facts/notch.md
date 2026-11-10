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
