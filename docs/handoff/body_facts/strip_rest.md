# Armpit strip rest (B' = B with the band laid into A's groove): prototype, 10 Nov. THE LAY DOES NOT MEET THE BAR

Tool: `tools/body/strip_rest.py` (`build [--relax] | target | sheet`, `--snap` = frozen carried_target in
out/shoulder/snap). Output: out/shoulder/strip_rest.npz (ids, loc, V0, V1, snap, bridge per side). Nothing wired.
STATE: out/shoulder/strip_rest.npz ON DISK IS STILL THE OLD LINEAR LAY (rebuilt 10 Nov, same numbers as before).
One honest attempt at the lay fix (solver, 10 Nov) passes the edge limits on the RIGHT and FAILS on the LEFT.
It is in the code behind `build --relax` (off by default) and was never written to the npz. No second design made.

## Method (general core: lscm, Unfold, Curve, relay, relax)
A's patch under the band unfolded flat (LSCM); per bridge the apex = where A's normal is halfway between the two
mouths; a cubic through them; the bridge ends on the nearer side go ONTO the apex line; the rest by least squares
on the unfolded edge vectors; lifted back with heights from the band's neighbours. Band = rows 4 & beta == 1.

## Why the old lay has 0.34..1.80 rest edges (measured, both sides)
- The least squares runs on PLANE lengths, and the unfold's scale is not 1 (plane / surface 0.32..1.41). Where the
  plane is small (l, 30-37 mm from the apex, by the band's edge: plane 2.4 mm for a 4.4 mm edge) the real stretch
  comes out 1.4-1.8 (19 edges over 1.35 on l, 5 on r). Where the plane is large (the groove wall) edges come out short.
- The SHORT edges (9 under 0.75 a side) are: the bridging edges themselves, now running from the apex row up the
  far wall (l 0.49, 0.61, 0.63; r 0.58, 0.63, 0.66, 0.71, 0.73: plane length right, real length 3.7-4.7 mm for
  6-8 mm), edges ALONG the apex row (l 0.59, 0.67, 0.68, 0.72), and r 2326-2386 (0.34, a 3.6 mm edge by the row).
- Per row from the apex (mean new / old): near side 1.01, 1.07, 1.14, 1.16, 1.16 (l); far side 0.86, 1.02, 1.03.
  The apex row puts ALL the new skin on the near side: its 4 rows take it, the far side's first row is squeezed.
- Old band min triangle quality 0.296 (l) / 0.423 (r); the old lay 0.270 / 0.061.

## The attempt: `relax` (build --relax), and where it fails
Unknowns stay plane points (apex row slides along its line), but the energy is REAL: sum l0 * (L / l0 - 1)^2 on
3D edge lengths of foot + height, a soft wall at 0.82 / 1.28, a barrier on triangle area under 0.5 of rest
(L-BFGS, exact gradients through the lift); the apex row is walked onto its line in 4 steps from the feet.
- RIGHT: every band and band-to-neighbour edge inside 0.75..1.35 (0 outside), apex row 0.83..0.95, 10 on the row.
  Min triangle quality 0.295 against the old band's 0.423: FAILS "no worse than the old min".
- LEFT: 3 edges under 0.75, 11 over 1.35, min quality 0.116. Cause, measured: the left apex row is not one mesh
  row. It zigzags 2444, 2445 | 2386 | 2327..2332 (+ 2 added in round 2), and 2386-2327 is a 3.5 mm rest edge
  whose two ends want 7.6 mm between them on the line (2445-2386 is a quad diagonal). The pair ends 0.17-0.29 of
  rest, in either order; with the barrier the row beside it goes to the 1.28-1.30 wall instead. The first rest
  feet already hold 1 turned triangle on l (the closest-point map folds at the groove's mouth).
- Cost: over 10 minutes for both sides (iteration caps reached); the linear lay takes 44 s.
- NOT measured on the relaxed lay: path / chord, off-A distance, turned rest triangles, l / r mirror difference,
  rest visibility. The old lay's rest visibility stands (re-run today, unchanged): outline front 3/4 2 px, back
  3/4 and side 0; depth change over 0.5 mm 5.3 / 4.5 cm2 front 3/4, 6.4 / 6.8 back 3/4, 6.0 / 6.4 under (l / r).

## Posed edges 3.7-4.5x (defect 2): MEASURED on the old lay, 3 poses. They are mostly A's OWN
A's own = A's skin under the same edge (`Unfold.length(V=)`: the path between the edge's two feet, posed / rest)
and the principal stretch of A's triangle at the edge's middle (`Unfold.stretch`). All worst edges leave the apex
row up a wall (apex-to-wall, bridging or not): A's groove floor opens that much.
| pose | B' edge min..max, mean | A's own path min..max, mean | edges over A + 0.15 | over 3.0 (rest under 0.75) |
|---|---|---|---|---|
| x:abd150:l | 0.55..3.80, 1.44 | 0.58..3.67, 1.43 | 6 of 330 | 12 (4) |
| x:flex170:l | 0.58..3.73, 1.47 | 0.60..3.52, 1.46 | 6 of 330 | 11 (4) |
| p4:heroic_leap@19:r | 0.60..4.50, 1.49 | 0.64..4.28, 1.47 | 16 of 332 | 15 (6) |
Worst edges (rest new / old; posed x new; A's path; A's triangle): l 2333-2393 0.75; 3.80; 3.20; 3.40 |
2386-2446 0.70; 3.76; 3.67; 3.28 | 2445-2446 1.04; 3.61; 3.51; 3.28 | 2327-2387 0.85; 3.58; 3.44; 3.46.
r 2326-2386 0.34; 4.50; 4.28; 4.53 | 2267-2333 0.71; 3.93; 3.33; 3.79 | 2266-2332 0.63; 3.83; 3.53; 4.17.
So: A itself is at 3.2-4.3 there; the lay's short rest edges add 0.1-0.6 on 6 (l) / 16 (r) edges. A lay inside
0.75..1.35 would bring the worst to about A's 3.5-3.7 (l) and 4.3 (r), not under the fill's 2.7-3.3.

## Fill | B' on the OLD lay (unchanged; 9 named poses; band edges against each one's own rest)
The 9-row table is in git (this file at 2a2572f14) and still holds: fill worst edge 2.33..3.60, off A 9-34 mm,
turned 0-21; B' worst edge 2.26..4.50, off A 1.3-1.4 mm, turned 0-4. A's-own for the other 6 poses, and pass counts over all 9, are not computed (`cmd_target` does not print them).

## Is B' better than the fill on every count? NO
B' wins off-A (33 mm -> 1.4 mm), turned triangles, and follows A (mean 1.44-1.49 against A's 1.43-1.47). It LOSES
worst edge to the fill on l (3.7-3.8 against 2.7-2.8) and at leap 19 / 20 (4.5 against 3.3), because A's own floor
is there; and its rest lay is outside 0.75..1.35 on both sides (old) or on l (relaxed).

## What the next attempt needs (not built)
- The apex row must be a row the mesh HAS: on l the bridge ends change mesh row at 2386, so the line gets a 3.5 mm
  edge along it. Pick the row by mesh topology (one edge loop) or let the short edge leave the line. Split the
  new skin over both sides. A quality term (r falls 0.423 -> 0.295). A faster `Unfold.locate` (brute force).
- `cmd_sheet` was read, NOT fixed, NOT run: 2 columns, no A column, no numbers line, no `--under`. `target --snap`
  and `sheet --snap` run as before on the old npz; neither shows a fixed lay.
