# The girdle's rigid border + breast blend rows (10 Nov, solver for P1 lead 17)

**State: NOT finished. Done: step 1 (cause confirmed, 100%), the general function `carried_target.support_region`
(committed, not called by `Her` yet), the design measured on the dev poses by a prototype in the girdle-only frame.
NOT done (the budget went on measurement and design): wiring into `Her` / `Model.blend` / the npz / `region_shape`,
T15-T17, the T11 experiment. `carried_target.py test | target` behave as before this job. No second design tried.**
Scripts (not in git): `tools/body/out/shoulder/border_scratch/measure.py`, `proto.py` (+ `measure_cache.npz`).

## Step 1: 141 poses, girdle-only part pose, on the border rows of the 105 edges (mm, p50 / max)
| border | edges | B published motion | A carried motion | disagreement | B weight on the bones the pose moves p50 / min / max | the blend alone tears |
|---|---|---|---|---|---|---|
| trunk back | 42 | 0.0 / 0.0 | 28.4 / 49.4 | 28.4 / 49.4 | 0.00 / 0.00 / 0.00 | 37 |
| breast edge | 42 | 84.9 / 98.2 | 38.3 / 59.9 | 52.3 / 67.8 | 1.00 / 0.00 / 1.00 | 42 |
| trap line | 21 | 75.1 / 93.5 | 18.8 / 24.7 | 55.3 / 69.4 | 0.82 / 0.63 / 0.99 | 21 |
Motion over 5 mm on the border rows: 105 of 105 (the stop line was 80%). Two causes:
- **Trunk back: B does not move there (weight 0), A does**: A's back skin follows its arm 28-49 mm at 150-180 deg, and that
  motion reaches 31 rows past the list (why no row count cured it).
- **Trap line and breast edge are both the BREAST PART's top rows.** Outside the list B's surface moves only the arm and the
  breast part's first 8 rows (clavicle weight; Jog_Fwd@11:r row 1 mean 36 / max 99 mm, row 6 10 / 52, row 8 1 / 11). A moves
  the WHOLE breast part with a high arm (abd170 rows 10-12: A 25 / 33 mm, published 0; row 20: 11 / 16).
Motion support of one girdle (points either surface moves over eps; the explicit list is 3764 a side):
| eps mm | B published | A carried | breast part (586 points, 24 rows) | trunk past the list (rows out) | across the midline (rows) |
|---|---|---|---|---|---|
| 0.5 | 6983 | 8558 | A 586, B 187 | 508 (32) | 284 (31) |
| 1.0 | 6871 | 8286 | A 586, B 164 | 434 (31) | 164 (24) |
| 2.0 | 6737 | 7966 | A 586, B 141 | 335 (29) | 54 (21) |
Both also move the arm and hand past the list (3804 points): left out (below). 339 list points move under 0.5 mm.

## The design: `support_region(adj, moved, core, stiff, gated, rows, ring, gate_rows, wall_rows)` (no names, any set)
- **Support** `moved`: points B's published OR A's carried surface moves over eps 1.0 mm under the girdle's part poses. The
  pose set itself (each pose on its side, mirrored), not probe turns: the driver's elevation law is not linear (lat and pec
  act only at high arms). 85 s for 141 poses: cache it.
- **Region** = (moved | the list as core) grown 4 rows; share 0 on the outer row, 1 from 4 rows in. The ramp lies in rows
  nothing moves: outer row = published by construction, the ramp hides under eps.
- **Far border** `stiff`: points rigid (>= 0.999) to the upper arm's subtree outside the list (first row past the list: min
  weight 1.0000). Nothing grows into them; share 0 within `ring` 3 rows, rising over 4 = today's beta (measured: equal).
- **Breast rule** `gated` = the breast part, both sides: a WALL, share 0, the share rising over `wall_rows` 12 away from it.
  Gate shut: the whole part is published. Gate open: the wall stands back `gate_rows` 8 rows from the list (so only upper
  and lateral rows): the blend rows. Share(G) = (1 - g) closed + g opened, g = s01((elevation - lo) / (hi - lo)), the arm's
  elevation in spine_05's frame (as `region_target.describe`): this is `Model.blend`.
- **Jog's keyed clavicle does not open the gate**: T16 binds it (Jog_Fwd@11:r: elevation 43, clavicle 40 deg, the only pose
  with clavicle > 20 under 45), and opening would cut the breast's top rows from 99 to 37 mm of motion in a jog.

## Prototype, dev poses (eps 1, rows 4, gate rows 8, wall rows 12): ramp edges over 2.5x / not explained by A's or the
published surface's own stretch + 0.15, worst ramp edge
| pose (elevation) | today | gate 45-75 | gate 65-95 |
|---|---|---|---|
| p4:heroic_leap@19:r (170) | 29 / 26, 4.33 | 1 / 0, 2.93 | same |
| x:abd170:l, x:flex170:l, x:abd150:l | 28 / 26 3.66, 19 / 19 3.57, 13 / 13 3.20 | 0 / 0: 1.70, 1.60, 1.60 | same |
| p4:iron_vow@72:l (109) | 13 / 9, 5.30 | 0 / 0, 1.96 | same |
| cast_bolt@0:l (59) | 9 / 9, 4.92 | 0 / 0, 1.94 | 11 / 3, 2.77 (unexplained 2.59) |
| Jog_Fwd@14:l (54) | 26 / 24, 4.66 | 9 / 0, 4.00 | 15 / 2, 4.00 (2.70) |
| Jog_Fwd@11:r (43) | 34 / 30, 5.30 | **27 / 5, 4.04 (3.05)** | same |
| idle_warden_town@122:l, x:add0:l | 0 / 0 | 0 / 0 (1.83, 1.24) | same |
Wall rows 16 with gate 65-95: Jog@11 29 / 1 (2.51), Jog@14 16 / 0, cast_bolt 11 / 0, but abd150's worst ramp edge 1.60 ->
2.47. Wall rows 8: Jog@11 45 / 29. Gate rows 12: abd poses 2 / 0 at 2.80; gate rows 6 = 8 on these poses.
Limits of the prototype: plain carrier (no pocket fill), no trunk placement M, no neck delta, edges of md.adj.

## Region size (eps 1, gate rows 8): 5340 points a side (3764 + 1576); share 1 on 3072 shut, 3431 open
New: breast rows 339 (225 cm2), back 282 (111 cm2), front incl. the trap line 599 (221 cm2), across the midline 356
(129 cm2). The carrier finds all of them (not ok 0). The arm side is today's (|share - beta| 0.00).
**Weight fit:** its region grows by the same 1576 a side. B's weights there (summed): spine_03 566, spine_04 464, neck_01
210, Head 72, clavicle 59, spine_05 53, breast_tip 47, breast 33. Following A on the back means trunk points take lat / scap
/ clavicle weight; the breast's top 8 rows join the fit.

## Wiring left
1. `Her.__init__`, explicit provider: cache the max motion per md point (`out/shoulder/support.npz`, keyed by the pose
   names); `support_region(md.adj, moved, list mask, stiff, md.part == breast)`; region points = the list first, then the new
   ids; carrier = the list's (pocket) + a plain Carrier on the new ids; edges over all.
2. `Model.blend(G, side, grown=False)` = (1 - g) closed + g opened (False: the list's 3764, so region_shape runs as is).
   `Her.carried(.., full=False)` likewise; `Her.target` returns X on the list and keeps the grown rows; `cmd_target` adds
   `ext_l`, `ext_r` (md ids) and `Xe`; `region_shape.surface("carried")` must write `Xe` too or sheets crack at the list's
   border; `edges` needs the grown edges to class the new ramp.
3. T11 with the old share (beta, list only) for the identity-turn experiment; T15-T17 as briefed.
Full run after that, unchanged commands: `python tools/body/carried_target.py target`, `python tools/body/region_shape.py edges --provider carried`.

## Needs a decision
- **Gate range.** Idle / run / jog poses reach 65 deg (idle_warden_town@126:r 65, run_warden@13:l 60, Jog_Fwd@14:l 54, six
  idles 48-55). "Idle and walk within 1 mm" needs lo >= 65; T16 alone allows 45. 65-95 costs cast_bolt and Jog@14 (table).
- **Jog_Fwd@11:r is not cured at wall rows 12** (5 edges, 3.05): B's clavicle weight on the breast's top rows, which the rule
  keeps published in a jog. Wall 16 cures it and costs the abd poses 0.9x; or leave it "published" until the weight fit.
- eps: 0.5 mm adds about 194 points a side (120 across the midline), 2.0 removes about 209.
