# The girdle's rigid border + breast blend rows (10 Nov, solver for P1 lead 17)

**State: NOT finished. Built and measured: step 1 (cause confirmed, 100%), the general function
`carried_target.support_region` (committed, not called by `Her` yet), and the design proven on the dev poses by a prototype
in the girdle-only frame. NOT done (context budget spent on the measurement and the design): the wiring into `Her` /
`Model.blend` / the npz / `region_shape`, tests T15-T17, the T11 experiment. `carried_target.py test | target` behave as
before this job. No second design was tried; the open choices are at the end.**

## Step 1: the measurement (141 poses, girdle-only part pose, on the border rows of the 105 edges)
| border | edges | B published motion mm p50 / max | A carried motion | disagreement | B weight on the bones the girdle pose moves p50 / min / max | the blend of the two alone tears over 2.5x |
|---|---|---|---|---|---|---|
| trunk back | 42 | 0.0 / 0.0 | 28.4 / 49.4 | 28.4 / 49.4 | 0.00 / 0.00 / 0.00 | 37 |
| breast edge | 42 | 84.9 / 98.2 | 38.3 / 59.9 | 52.3 / 67.8 | 1.00 / 0.00 / 1.00 | 42 |
| trap line | 21 | 75.1 / 93.5 | 18.8 / 24.7 | 55.3 / 69.4 | 0.82 / 0.63 / 0.99 | 21 |
Motion over 5 mm on the border rows: 105 of 105 (100%; the stop line was 80%). Two different causes:
- **Trunk back: B does not move there at all (weight 0), A does.** A's back skin follows its arm 28-49 mm at 150-180 deg. The
  list's border is rigid for B and not for A. No row count cures it because A's motion reaches 31 rows past the list.
- **Trap line and breast edge: both are the BREAST PART's top rows.** B's published surface moves outside the list only on the
  arm and on the breast part's first 8 rows (clavicle weight: Jog_Fwd@11:r row 1 mean 36 / max 99 mm, row 6 10 / 52, row 8
  1 / 11). A moves the WHOLE breast part with a high arm (abd170: rows 10-12 A 25 / 33 mm, published 0; row 20 11 / 16).
Motion support of one girdle (points moved over eps by either surface; explicit list 3764 a side):
| eps mm | B published | A carried | outside the list: breast part | trunk past the list (rows out) | across the midline (rows) |
|---|---|---|---|---|---|
| 0.5 | 6983 | 8558 | 586 of 586 (A), 187 (B) | 508 (32) | 284 (31) |
| 1.0 | 6871 | 8286 | 586 (A), 164 (B, 9 rows) | 434 (31) | 164 (24) |
| 2.0 | 6737 | 7966 | 586 (A), 141 (B) | 335 (29) | 54 (21) |
Both also move the arm and hand past the list (3804 points): not the region's (the list's own arm border stays).
339 list points (321 of them border rows) move under 0.5 mm: rigid already. Scripts: scratch `measure.py`, `proto.py`.

## The design (general form: `support_region(adj, moved, core, stiff, gated, rows, ring, gate_rows, wall_rows)`)
- **Support.** `moved` = points that B's published surface OR A's carried surface moves over eps 1.0 mm under the girdle's part
  poses: the pose set itself (141 poses, each on its own side, mirrored to the other), not probe turns, because the driver's
  elevation law is not linear (lat and pec only act at high arms). No weights, no names. Costs 85 s: cache it in a file.
- **Region** = (moved | the explicit list as core) grown 4 rows; share 0 on the outer row, 1 from 4 rows in. The ramp lies in
  rows nothing moves: outer row = published by construction, the ramp hides under eps.
- **Far border** (`stiff`): points rigid (>= 0.999) to the upper arm's subtree OUTSIDE the list (first row past the list on the
  arm: min weight 1.0000). Nothing grows into them; share 0 within `ring` 3 rows, rising over 4: today's beta there.
- **Breast rule** (`gated` = the breast part, both sides; a WALL with share 0, the share rising over `wall_rows` away from
  it). Gate shut: the whole part is published. Gate open: the wall stands back `gate_rows` 8 rows from the list (upper and
  lateral rows only, measured from the list); those are the blend rows. Share(G) = (1 - g) closed + g opened,
  g = s01((arm elevation - lo) / (hi - lo)), elevation in spine_05's frame (as `region_target.describe`): `Model.blend`.
- **Jog's keyed clavicle does NOT open the gate.** T16 binds it (Jog_Fwd@11:r: elevation 43, clavicle 40 deg, the only pose
  with clavicle > 20 under 45), and opening would cut the breast's top rows from 99 to 37 mm of motion in a jog.

## Prototype on the dev poses (girdle-only frame, plain carrier; eps 1, rows 4, gate rows 8, wall rows 12, gate 45-75)
Ramp edges over 2.5x / of them not explained by A's or the published surface's own stretch + 0.15; worst ramp edge:
| pose (elevation) | today | new |
|---|---|---|
| p4:heroic_leap@19:r (170) | 29 / 26, 4.33 | 1 / 0, 2.93 |
| x:abd170:l | 28 / 26, 3.66 | 0 / 0, 1.82 |
| x:flex170:l | 19 / 19, 3.57 | 0 / 0, 1.78 |
| x:abd150:l | 13 / 13, 3.20 | 0 / 0, 1.70 |
| Jog_Fwd@11:r (43) | 34 / 30, 5.30 | 27 / 5, 4.04 (worst unexplained 3.05) |
| Jog_Fwd@14:l (54) | 26 / 24, 4.66 | 9 / 0, 4.00 |
| p4:iron_vow@72:l (109) | 13 / 9, 5.30 | 51 / 43, 3.81: see the note |
| cast_bolt@0:l (59) | 9 / 9, 4.92 | 33 / 29, 4.65: see the note |
| idle_warden_town@122:l, x:add0:l | 0 / 0 | 0 / 0 (worst 2.05, 1.34) |
**Note: that run had a fault** (far-rigid points INSIDE the list were walled, so the deltoid lost its share: iron_vow and
cast_bolt rows are that fault, not the design). Fixed in the committed function (`stiff & ~core`); rerun numbers below if
this file has a "Rerun" section, else unmeasured.
Scan: wall rows 16: Jog@11 29 / 1 (worst unexplained 2.51) but abd150's worst ramp edge 1.70 -> 2.47; wall rows 8: Jog@11
45 / 29. Gate rows 12: abd poses 2 / 0 at 2.80 (worse than 8). Gate rows 6: same as 8 on these poses.

## Region size (eps 1, gate rows 8): 5340 points a side (3764 + 1576)
Breast rows 339 (225 cm2), back 282 (111 cm2), front incl. the trap line and under the list 599 (221 cm2), across the
midline 356 (129 cm2). The carrier finds every one (not ok 0). Share 1: 2494 shut, 2853 open.
**For the weight fit:** the fit region grows by the same 1576 points a side. B's weights there are spine_03 (566 summed),
spine_04 (464), neck_01 (210), Head (72), clavicle (59), spine_05 (53), breast_tip (47), breast (33). So following A on the
back means giving trunk points lat / scap / clavicle weight, and the breast's top 8 rows are in the fit.

## Wiring left (exact)
1. `Her.__init__`, explicit provider: cache max motion per md point (`out/shoulder/support.npz`, keyed by poses.npz names);
   call `support_region(md.adj, moved, list mask, stiff, md.part == breast)`; region points = list ids first, then the new
   ids; carrier = the list's (pocket) + a plain Carrier on the new ids; edges over all.
2. `Model.blend(G, side, grown=False)`: (1 - g) closed + g opened; `grown=False` returns the list's 3764 (region_shape
   as is), True the whole region. `Her.carried(.., full=False)` the same way; `Her.target` keeps X on the list and
   stores the grown rows; `cmd_target` adds `ext_l`, `ext_r` (md ids) and `Xe` to the npz; `region_shape.surface`
   ("carried") must write `Xe` too or the sheets crack at the list's border; `edges` then needs the grown edges.
3. T11: run with the old share (beta, list only) for the identity-turn experiment. T15-T17 as briefed.

## Needs a decision
- **The gate's range.** Idle / run / jog poses reach 65 deg (idle_warden_town@126:r 65, run_warden@13:l 60, Jog_Fwd@14:l 54,
  six more idles 48-55). "Idle and walk stay published within 1 mm" needs the gate to start at 65 or above; T16's 45 deg
  alone lets it start at 45. With 60-90: cast_bolt (59) and Jog@14 stay shut and lean on the wall ramp (Jog@14 15 / 2, 2.70).
- **Jog_Fwd@11:r is not cured by a wall ramp of 12** (5 unexplained edges, 3.05): the cause is B's clavicle weight on the
  breast's top rows, which the rule keeps published in a jog. Wall 16 cures it and costs the abd poses 0.7x. Or accept it
  as "published" class until the weight fit.
- eps: 0.5 mm adds about 194 points a side (120 across the midline), 2.0 removes about 209.
