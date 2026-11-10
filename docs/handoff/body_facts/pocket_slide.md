# Armpit pocket as a band sliding on A: built once, FAIL (10 Nov)

Verdict: the slide puts the pocket ON A's hollow (off A 33 mm -> under 3 mm) but does not bring the edges to 2.5x, and
it collapses and turns over edges the fill did not. Default stays the fill (`pocket_mode` absent = "fill", output
unchanged, T1-T7 green). The slide is in the file behind `pocket_mode: "slide"`. No full 141-pose run was made.

## Step 0, the skin budget (measured before the solver)
Across the fold, per bridge: B's REST path (border row - bridge - border row, along B's edges) against A's POSED
surface path between the same two borders' carried feet (graph geodesic with flap diagonals). Median / max over bridges.

| pose | rows 4 | rows 6 | rows 8 | rows 12 (through the bridge feet) |
|---|---|---|---|---|
| x:abd120:l | 1.91 / 1.97 | 1.74 / 1.83 | 1.66 / 1.69 | 1.51 / 1.58 |
| x:abd150:l | 2.21 / 2.40 | 2.01 / 2.13 | 1.89 / 1.91 | 1.70 / 1.75 |
| x:abd170:l | 2.34 / 2.54 | 2.15 / 2.27 | 2.02 / 2.05 | 1.75 / 1.86 |
| x:flex170:l | 2.33 / 2.46 | 2.12 / 2.19 | 1.97 / 2.03 | 1.75 / 1.84 |
| p4:iron_vow@72:l | 1.56 / 1.67 | 1.51 / 1.62 | 1.51 / 1.56 | 1.17 / 1.51 |
| p4:heroic_leap@9:r | 2.08 / 2.45 | 2.00 / 2.22 | 1.87 / 2.07 | 1.72 / 1.85 |
| p4:heroic_leap@19:r | 2.24 / 2.63 | 2.11 / 2.38 | 1.97 / 2.17 | 1.76 / 1.96 |
| p4:heroic_leap@20:r | 2.23 / 2.65 | 2.14 / 2.40 | 2.01 / 2.20 | 1.72 / 1.96 |

Facts under the table:
- A's rest fold hides almost no skin: A rest path / B rest path is 1.21 (rows 4), 1.10 (rows 8). The opening
  (43-66 mm at the bridge feet) is A's OWN STRETCH: A's surface on the path stretches 1.8-2.0x overhead.
- So the budget is a MEAN of 1.9-2.2 at rows 8, against a bar of 2.5: 15-25% of room for scatter, no more.
- Carried alone, non-bridge edges already sit at p90 1.9-2.1 in rows 0-4 and 1.6-1.7 at rows 8-9, with single edges at
  2.3-2.9 in rows 5-9 and 2.8-3.6 at rows 12-13 (A's own). A band has no slack row to borrow from.
- The region's blended border (beta < 1) reaches row 4 from the bridges (a wedge: 1, 3, 5, 7, 9 points at rows 4-8) and
  the region's edge row 10. The band must stay off it (a slide blended against the published surface shears edges).

## The method as built (general core: `Band(Pocket)`, `facing`, `Carrier(pocket_mode, hold, tris)`)
Band point = a point of A's surface (triangle + barycentrics; at rest its closest point) + rest offset re-aimed along
A's smooth rest normal and turned by A's local rotation there. Holders (carried neighbours) fixed. Balance in the
tangent plane of A's posed smooth normal: T^t (R c - L x) = 0, L the length-weighted Laplacian, c the tangent part of
delta at rest (rest is a fixed point). Newton in the tangent planes, step cut to half an A edge (2.4 mm), landed by the
closest point over the two rings around the point's own triangle. Her: rows 8, hold = beta < 1: 347 points a side.

## Numbers (rows 8, 12 poses; fill today in brackets where known)
| pose | band edge min..max | off A max mm | flips | iterations |
|---|---|---|---|---|
| rest l / r | exact (4e-19 m), 0 steps | | 0 | 0 |
| x:add0:l | 0.30..1.28 | 2.6 | 7 | 29 |
| x:abd120:l | 0.53..2.17 | 2.8 | 2 | 200, not converged |
| x:abd150:l | 0.26..2.61 [0.43..2.69] | 2.8 [25.5] | 3 | 22 |
| x:abd170:l | 0.17..2.76 | 2.8 [31.2] | 5 | 22 |
| x:flex170:l | 0.12..2.75 | 2.7 [33.6] | 7 | 29 |
| p4:iron_vow@72:l | 0.22..2.09 | 2.9 | 13 | 200, not converged |
| p4:heroic_leap@7:r | 0.25..2.53 [3.17] | 2.7 | 54 | 200, not converged |
| p4:heroic_leap@9:r | 0.27..3.31 [3.60] | 2.6 | 22 | 200, not converged |
| p4:heroic_leap@18:r | 0.14..2.86 [3.18] | 2.6 | 0 | 200, not converged |
| p4:heroic_leap@19:r | 0.08..3.04 [3.32] | 2.6 [33.5] | 5 | 200, not converged |
| p4:heroic_leap@20:r | 0.11..3.08 [3.33] | 2.5 [33.5] | 2 | 200, not converged |
| p4:heroic_leap@21:r | 0.24..2.84 [3.10] | 2.5 | 4 | 57 |
Repeat calls are identical. No point reached the patch's edge. Edge max over 2.5 in 9 of 11 opened poses, over 3 in 3.

## Why (do not re-derive)
1. Budget: the mean is 1.9-2.2; the converged poses land at 2.6-2.8, a scatter of 30-40% over the mean. Under 2.5
   needs the band flatter than A's own surface is. More rows buy 0.1-0.2 of mean and run into the blended border.
2. The balance is not sound on a surface that also SHRINKS along the fold: zero-length springs pull the rows together
   (min 0.08-0.30, triangles turned over), and even the closed pose x:add0 slides 8 mm and turns 7 triangles.
3. Half the opened poses cycle at the step cut (2-4 mm steps after 200 iterations): their numbers are not a balance.
What would be a different job, not a tune: springs with rest length (no pull under compression) plus a shear term,
or accept the fill's web and spend the effort on B's rest skin in the armpit (B has 8 mm less path than A there).
