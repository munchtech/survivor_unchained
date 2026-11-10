# The lead's three marks on the carried column, located (lead 21's helper, 10 Nov; dev target target_a_dev.npz)

Probes (CPU, read-only, nothing written to out/): `survivorsunchained_inputs/scratch_p1_notch/` probe.py (sharpest
composed edges in a rest box, fair on / `fair_off` / `map_off` / published, region share + delta per end), neck.py,
wjump.py. Live compose == dev Xc (0.0 mm). Rest frame: +z front, -x her right, y up (mm). md vertex ids below are for
the lead's checks only; the cures are rules.

## (1) heroic_leap@6:r / @9:r, upper-chest notch: B's SOURCE WEIGHTS, checkerboard neck_01 / spine_04
- Where: rest x -45..-69, y 1508-1531, z 43-75 (just under the right clavicle, sternum side of the breast top).
  Edges e23033-23034, 23034-23075, 23074-23139, 23075-23140, 23204-23205, 23268-23269, 22913-22914.
- Cause: neighbouring vertices alternate neck_01 0.82-0.95 (23034, 23075, 23140, 23204, 23205, 22914) and
  spine_04 0.76-0.82 + trap 0.1-0.18 (23033, 23074, 23139, 23268). 28 front edges per side with a neck-chain weight jump
  > 0.5 (y 1510-1544; symmetric, so the left has it too). The neck region's delta alternates with it: 30-34 mm on the
  neck_01 points, 1-3 mm on the spine_04 points (share 1.00, core, not stiff; neck relax on = off, cf = cr).
- Numbers, box of 179 edges, max dihedral / edges over 45: @6 published 153/26, composed 136/22, girdles only 147/27;
  @9 published 148/5, composed 124/17, neck only 137/15 (the neck region adds 12 on @9); @12 pub 77/4 -> 35/0;
  iron_vow@72:l 68/8 -> 18/0; cast_bolt@3, add0 flat.
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
- So fair_a halves the count but makes a short line of near-folded edges (135-177) at the cap front where it was
  47-126: the faired patch's ring meeting the unfaired crumple (the fair's edge, the step). map only touches 5664-5665.
- Cure: in fair_a, blend the faired offset out over the soft rings by fold severity, or grow the patch (`grow` 1 -> 2,
  `rings` 3 -> 4) until the seed core is inside; or seed on the posed dihedral excess, not only > 45. Size: a keyword
  sweep first (small); if the core still folds, a solver job on the core's fairing (alpha_core 0.02).

## (3) cast_bolt@3:r, ribcage below the armpit: B's own published fold, nothing carried there
- Sharpest in x -210..-100, y 1230-1420: e24889-24890 -166, 24888-24975 157, 21680-24889 -151 at x -122..-126,
  y 1325-1332, z 64-67, identical on published / composed / fair_off / map_off; girdle_r share 0.02-0.20, delta 0.0-0.3 mm.
  Box over 45: composed 33, published 40. No share gradient or band border makes it.
- Cure: B's source skin (same weight-relax tool as (1)) or the girdle's ramp grown to cover it. Not checked: B weights there.
