# The soft chest fold overhead, and the armpit pinch (P1 lead 19's helper, 10 Nov; measured, nothing fixed)

Tool: `tools/body/fold_probe.py` (new; general core: `dihedral`, `depth`, `rows_from`, `edge_ratio`; `dump` reads HER).
`python tools/body/fold_probe.py dump "x:abd150:l,x:abd170:l,x:flex170:l,x:add0:l,cast_bolt@3:r,crossbow_shoot@10:r,x:abd90_int60:l" a` (30 s, writes git-ignored `tools/body/out/shoulder/fold_probe/`), then `python tools/body/fold_probe.py measure a [--top 12] [--k 3]`.
**Measures.** depth = mm a point lies under the mean of its ring 3 rows away, along its normal, MINUS the same at rest (valley +). Angle = valley angle of an edge minus rest. "A" = A carried at share 1 (the region's own carrier on region points, a plain wide carrier elsewhere), on B's points and B's kinematics. Fold set = points of (own breast part + ramp rows, within 14 rows of the list) where depth B - A is at least half the worst.

## 1. Where
Model point ids (md) 6376, 6398, 6399, 6421, 6422, 6490 lead on all three poses (22-34 points in the set). All in the part map's **breast**, left, on the gate's BLEND rows next to the wall: rows from the list 3-8, rows from the open wall 0-5, **share 0.00-0.38** (6376: 0.00, 6398/6399: 0.02, 6421/6422: 0.07, 6490: 0.38). Not the neck (neck delta 0.000 mm on all three poses), not the 12-row wall ramp on the collar side.

## 2. How deep (fold set, mean / max)
| pose | depth mm B | A | published | valley angle deg B | A | published |
|---|---|---|---|---|---|---|
| x:abd150:l | 1.05 / 1.60 | 0.02 / 0.57 | 0.71 / 3.44 | 4.0 / 23.0 | 0.1 / 5.8 | 1.9 / 17.8 |
| x:abd170:l | 1.22 / 2.19 | 0.13 / 1.15 | 0.88 / 3.79 | 5.1 / 27.1 | 0.2 / 6.5 | 2.7 / 19.3 |
| x:flex170:l | 1.24 / 1.64 | -0.01 / 0.36 | 0.29 / 1.71 | 5.4 / 26.6 | -0.5 / 3.2 | 1.2 / 12.7 |
At the leading points B equals published (abd150: 6422 B 1.27 / pub 1.30 / A -0.20; 6399 1.46 / 1.27 / 0.00; 6421 1.27 / 1.26 / -0.16; 6376 1.27 / 1.02 / -0.10): the carry alone (A) has no fold there, the published side does.

## 3. Why: (ii), with (i) as its carrier. Not (iii), not (iv)
- **The published breast stays low while A's lifts.** A carried minus published on the own breast part, mean mm by rows from the list (lift along the body's long axis | whole offset | share): abd150 r1 1.7|17.0|0.73, r2 4.0|17.3|0.62, r4 10.3|17.4|0.32, r6 16.2|18.3|0.08, r8 19.1|20.8|0.00, r10 20.6|22.2, r14 19.7|20.6, r20 10.3|10.8. abd170: r8 20.5|22.7, r10 22.5|24.6. flex170: r8 20.1|22.1, r10 21.8|23.7. At the fold points the offset is 7-11 mm normal and 17-23 mm tangential. The gate is fully open (g = 1 from 75 deg): the share still falls to 0 by row 8, so a 17-23 mm offset is taken up in 5-8 rows, and the row where it lands is the published surface's OWN crease (published depth max 3.44 / 3.79 / 1.71 in the set).
- (iii) neck: its delta is 0 on these poses. (iv) A's own shape: 0.02-0.13 mm mean, angle 0.1-0.2 deg.
- add0 (gate shut): B 0.40 / 0.84 on its own set = published under the ramp (published 1.07 / 2.02): no fold of the overhead kind.

## 4. Candidates (recomputed surfaces in the probe: comp + (new share - share) x A's delta; CRUDE shares, see limits)
| candidate | abd150 depth, angle max, worst edge | abd170 | flex170 | cast_bolt@3:r (66) | add0 |
|---|---|---|---|---|---|
| today | 1.05/1.60, 23.0, 1.60 | 1.22/2.19, 27.1, 1.70 | 1.24/1.64, 26.6, 1.60 | 0.21/0.90, 11.0, 2.34 | 0.40/0.84, 1.24 |
| (a) wall back to row 14 | -0.36/0.57, 7.0, **3.58** | -0.22/1.15, 6.8, 3.58 | -0.53/0.32, 7.1, 3.59 | 0.05/1.50, **47.9**, 2.32 | moves 7.0 mm |
| (a) wall back to row 20 | = A, 5.8, 8.69 | = A, 6.5, 8.88 | = A, 3.2, 8.81 | as row 14 | moves 7.0 mm |
| (b) ramp 20 rows | 0.58/3.44, 111.6, 3.50 | 0.75/4.18, 118.5, 3.94 | 0.16/3.18, 109.1, 3.62 | 0.26/1.25, 11.0, 2.34 | moves 5.0 mm |
| (c) share diffused over breast + ramp (60 passes) | 0.35/1.30, 10.0, 2.18 | 0.47/1.88, 10.3, 2.18 | 0.29/0.81, 6.6, 2.19 | 0.14/0.76, 12.3, 2.33 | moves 0.9 mm |
Reading: the fold goes only when the breast's upper rows FOLLOW the carry (a: depth to A's, angle 23-27 -> 7). A wider ramp alone (b) does not help. A smooth field (c) cuts it by 60-75 % for 7-8 mm of motion and a worst edge of 2.18. Ranked: **(a) as a second gate stage (elevation above ~90 only), with (c)'s smooth share as the ramp's shape**; (b) last. Every candidate moves add0 as built here (the probe applies them at any elevation): each must sit under an elevation gate to stay published at <= 45; at 66 deg (cast_bolt@3:r) (a) ungated makes a 47.9 deg valley, so the stage must start above the 60-90 poses.

## The armpit pinch (front, deltoid against chest): A has the same, to the degree
Sharpest valley edges inside the list, share 1.00: edge (5832, 5833) abd150 **B 141 / A 141** / published 8 / rest 9 deg; abd170 155 / 155; flex170 edge (5773, 5833) 150 / 150; edge (2882, 2932) 128 / 128, 147 / 147, 141 / 141. List valley edges over 90 deg: B 5 = A 5 (abd150), 7 = 7 (abd170, flex170). It is A's carried shape (share 1), not the border.

## NOT measured / limits
- Right-side mirror poses (x:abd150:r ...) are not in `poses.npz`: not measured.
- Candidate shares are approximations (wall moved by rows from the list, the region's border share taken as is; "A" off the region uses a plain carrier, 10246 points without A fall back to published): the candidates' WORST EDGE numbers (3.58, 8.69) include steps at my crude share's outer edge and are upper bounds, not verdicts; (b)'s 110 deg is likely such a step. A real test = the share built in `support_region` with a second gate stage.
- crossbow_shoot@10:r and x:abd90_int60:l are in the dump and printed by `measure`; their lines were NOT read (context). The 60-90 check rests on cast_bolt@3:r only.
- "A" for the pinch is A carried onto B's points (pocket fill), not A's own mesh; A's own mesh angle was not measured. Point ids are model points (md), source vertex = `md.first[id]`. No picture was made: the one to make is abd150:l front34, B | (a) row 14 | A, to see whether the 7 deg remainder reads.
