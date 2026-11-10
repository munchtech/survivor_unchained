# Neck diagnosis: B's published stretch at the throat pit and neck base (10 Nov, helper for P1 lead 17)

Read-only, numpy on `tools/body/out/shoulder/poses.npz`; B and A through `deform_audit.body`, published = `region_target.published`.
Scripts (scratch, not committed): session scratchpad `body\neck\common.py`, `s2.py`, log `s2.log`.
Edges: every mesh edge of B with y 1.40-1.62 m. Zones by rest midpoint: pit = |x| < 25 mm, y 1525-1560, front; trap = |x| 25-80,
y 1500-1560, z > 20 (the front neck-base ring the classifier calls trap_line); nape = |x| < 40, y 1500-1560, z < -80.
F = a vertex's total weight on neck_01 and all below it in the chain (neck_02, Head, face). Brackets = edges over 2.5x.

## 1. Geometry (rest, mm)
B: spine_04 y 1333.5, spine_05 y 1443.5, neck_01 y 1458.0 (z -27.6), neck_02 y 1584.1, Head y 1636.2.
A: spine_03 y 1333.5, neck_01 y 1584.1, Head y 1636.2 (no joint between 1333 and 1584).
Worst pit edges: rows y 1541.6 -> 1545.1, z 35-38, l0 4.7 mm, 106-107 mm from neck_01's joint, 90-95 from neck_02's.
Worst trap edges: (-51, 1519, 62) and (-58, 1522, 57), l0 5.0-6.3 mm, 119-122 mm from neck_01, 131-139 from neck_02.
Nape: (37, 1540, -104), l0 13.7 mm, 117-122 mm from neck_01.

## 2. Weights: the ring is fine, a second step above it is not
B's ring, F 0.1 / 0.5 / 0.9 by height: front midline y 1434 / 1458 / 1482 (82 mm along the surface), front x=20 the same (92 mm),
front x=50 y 1441 / 1469 / 1491 (76 mm), nape y 1434 / 1458 / 1482 (49 mm). Centred on the joint (y 1458). Not narrow.
ABOVE the ring F falls back to the trunk on a band of rows, and the fall is ONE edge wide:
| edge | lower vertex | upper vertex | dF | l0 mm |
|---|---|---|---|---|
| pit, 9.10x | y 1541.6: neck_01 0.76, spine_04 0.18, Head 0.05 (F 0.82) | y 1545.1: spine_04 0.71, Head 0.23, neck_01 0.03 (F 0.29) | 0.54 | 4.7 |
| trap, 11.68x | y 1517.1: neck_01 0.95, clavicle_r 0.05 (F 0.95) | y 1520.0: spine_04 0.82, trap_r 0.15, Head 0.02 (F 0.03) | 0.92 | 5.0 |
| trap, 9.30x | y 1520.1: neck_01 0.89, clavicle_r 0.11 (F 0.89) | y 1523.3: spine_04 0.79, trap_r 0.18, Head 0.03 (F 0.04) | 0.85 | 6.3 |
| nape, 3.71x | y 1536.2: spine_04 0.75, trap_l 0.13, neck_02 0.08 (F 0.12) | y 1548.1: neck_01 0.97 (F 0.98) | 0.86 | 13.7 |
Steepest dF: 0.115 / mm at y 1542 (front midline), 0.183 / mm at y 1517 (x=50), 0.044 / mm at y 1578 (nape).
So a band at y 1517-1545 (front) rides spine_04, the bone TWO joints below neck_01, with neck_01-weighted skin under it: the field
is not monotonic up the neck. spine_05 carries nothing at these vertices. A's ring: NOT measured (A's weight columns do not index
its 100 bone names the way I assumed; out of budget before resolving it).

## 3. Experiment I: weights held, the head's end orientation re-shared over neck_01 / neck_02 / Head
As keyed, against spine_05 (rotvec deg; x nod, y twist, z side): iron_vow@75 neck_01 (-12.8, -18.3, 16.7), Head end (-35.7, 22.0,
23.6) = 48.1 total; local turns 27.9 / 16.2 / 30.9. idle_warden_town@122 neck_01 (28.6, 2.1, 1.8), Head end (1.4, 18.6, 9.5) =
20.9 total; local 28.7 / 7.6 / 26.6. Both clips turn neck_01 one way and take it back above: 28.6 deg of nod on neck_01 under a
head that ends 1.4 deg nodded (warden town); an 18 deg twist one way under a head that ends 22 deg the other way (iron_vow).
| pose | split | pit | trap | nape |
|---|---|---|---|---|
| iron_vow@75 | as keyed | 9.10 (45) | 11.68 (96) | 3.71 (12) |
| | thirds | 3.57 (13) | 3.30 (12) | 3.21 (4) |
| | 20 / 30 / 50 | 3.98 (15) | 3.59 (8) | 2.26 (0) |
| | 0 / 50 / 50 (A's chain) | 4.64 (15) | 3.88 (20) | 1.16 (0) |
| | A's own, config map / joint map | 1.13 / 1.57 | 1.18 / 1.51 | 1.18 / 1.06 |
| idle_warden_town@122 | as keyed | 7.17 (30) | 11.20 (88) | 4.66 (26) |
| | thirds | 1.58 (0) | 2.71 (1) | 1.96 (0) |
| | 20 / 30 / 50 | 1.62 (0) | 1.93 (0) | 1.57 (0) |
| | A's own, config map / joint map | 1.16 / 1.28 | 1.18 / 1.25 | 1.27 / 1.09 |
Config map = carried_target's (A neck_01 <- B neck_01; A's Head rides, since `pose_bones` lists "head" and A's bone is "Head").
Joint map = A neck_01 <- B neck_02, Head <- Head. iron_vow still fails with neck_01 at ZERO (0/50/50: pit 4.64): Head's 0.23 on
the pit's upper row is a step of its own under a 48 deg head.

## 4. Experiment II: clips held, neck_01 alone from rest (pit / trap / nape)
| deg | flex (+x) | extend | side bend (z) | twist (bone axis) |
|---|---|---|---|---|
| 5 | 2.06 / 2.66 / 1.62 | 1.73 / 1.89 / 1.53 | 1.51 / 2.09 / 1.49 | 1.41 / 2.11 / 1.50 |
| 10 | 3.12 / 4.38 / 2.25 | 2.46 / 2.83 / 2.07 | 2.19 / 3.31 / 1.97 | 1.85 / 3.75 / 2.00 |
| 15 | 4.17 / 6.10 / 2.89 | 3.18 / 4.38 / 2.61 | 2.95 / 4.55 / 2.46 | 2.49 / 5.46 / 2.50 |
| 20 | 5.22 / 7.81 / 3.52 | 3.90 / 6.10 / 3.29 | 3.73 / 5.79 / 2.93 | 3.20 / 7.18 / 3.00 |
| 25 | 6.26 / 9.51 / 4.15 | 4.62 / 7.81 / 4.02 | 4.51 / 7.03 / 3.41 | 3.92 / 8.90 / 3.48 |
| 30 | 7.28 / 11.19 / 4.77 | 5.38 / 9.51 / 4.76 | 5.29 / 8.25 / 3.88 | 4.64 / 10.60 / 3.96 |
2.5x is crossed under 5 deg (trap, flex), by 10 deg on every axis at the trap ring, by 10-20 deg at the pit. Flexion is worst, no
axis is safe. No corrective or driven bone acts here: V0 + F (turned - V0) matches published to 0.00 mm.

## 5. Clips (max local turn over the whole clip, deg: neck_01 / neck_02 / Head; share = neck_01 of the sum)
p4:idle_warden_town 41.4 / 21.0 / 42.9 (0.39); p4:iron_vow 27.9 / 16.7 / 36.1 (0.35); p4:bladestorm_loop 23.8 / 12.2 / 23.9 (0.40);
p4:heroic_leap 21.0 / 16.5 / 38.9 (0.27); p4:shield_charge 20.4 / 10.2 / 26.8 (0.36); p4:run_warden 13.2 / 11.2 / 14.6 (0.34);
p4:run_warden_town 12.7 / 7.5 / 10.6 (0.41). All 25 library dumps: neck_01 0.0 (they key neck_02, up to 41.4 in Jog_Fwd, and
Head, up to 68.6 in axe_heavy). Only A1's seven p4 clips load neck_01, and every one does. NOT traced: which line of
`tools/anim/p4.py` writes the neck_01 track (out of budget before the grep; the clips are read from the motion-a1 worktree).

## 6. What-if, weights alone (F averaged over neighbours n passes on the welded mesh; no file written)
| n | flex 25 pit / trap / nape | extend 25 | twist 25 | iron_vow@75 AS KEYED (approximate) |
|---|---|---|---|---|
| 0 | 6.26 / 9.51 / 4.15 | 4.62 / 7.81 / 4.02 | 3.92 / 8.90 / 3.48 | 9.10 / 11.68 / 3.71 |
| 2 | 1.75 / 3.05 / 1.75 | 2.51 / 1.99 / 2.68 | 1.61 / 2.52 / 2.07 | 4.65 / 4.59 / 1.70 |
| 4 | 1.22 / 2.57 / 1.35 | 1.97 / 1.68 / 2.01 | 1.32 / 2.27 / 1.66 | 4.04 / 3.66 / 1.36 |
| 8 | 1.02 / 2.26 / 1.14 | 1.63 / 1.45 / 1.56 | 1.20 / 1.99 / 1.40 | 3.83 / 3.16 / 1.17 |
| 32 | 1.08 / 1.66 / 1.05 | 1.24 / 1.24 / 1.21 | 1.07 / 1.47 / 1.17 | 3.80 / 3.22 / 1.13 |
The ring's own heights (0.1 / 0.9 at y 1433 / 1482) do not move up to n=4: this removes the step, it does not widen the ring.
The last column moves weight between spine_05 and neck_01 only (the Head and neck_02 steps on the same rows stay), so its floor
of 3.8 is a lower bound on what a full fit would gain, not a neck_01 limit. Nothing here was re-skinned in full or looked at.

## VERDICT
1. BOTH, weights first. Not a narrow or misplaced ring (48 mm high, centred on the joint) but a one-edge fall-back to spine_04 on
   the rows y 1517-1545 (front) and y 1536-1548 (nape), 106-122 mm above the joint: dF 0.54-0.92 across 5 mm. It fails alone at
   5-10 deg of neck_01 on any axis; removing it alone takes neck_01-alone at 25 deg from 6.3 / 9.5 to 1.0-1.2 / 2.3-2.6 (pit /
   trap). Re-sharing the clips alone takes iron_vow@75 from 9.1 / 11.7 to 3.6-4.0 / 3.3-3.6 and warden town to 1.6 / 1.9. In
   iron_vow each removes 65-80% of the excess over 1.0, overlapping; only the weight fix clears the single-bone test.
2. Weight target for the fit: F monotonic up the neck; no vertex above the ring on spine_04 (the trunk's share there belongs to
   spine_05 / clavicle / trap); each neck-chain bone's weight (neck_01, neck_02, Head separately) changing under 0.03 per mm of
   surface (dF < 0.15 on a 5 mm edge; today 0.115-0.183 per mm). Head's 0.23 on row y 1545 falls under the same rule.
3. Rule for A1: neck_01 at most 10 deg, never against the head's end turn (neck_01, neck_02 and Head each turn the way the head
   ends), split about 20 / 30 / 50. All seven p4 clips break the cap today (12.7-41.4 deg), worst idle_warden_town and iron_vow.
   Until the weights are fixed even 10 deg shows 3-4x at the trap ring, so the rule alone does not close it.
