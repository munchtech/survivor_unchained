# Armpit strip rest (B' = B's band laid into A's groove): prototype, 10 Nov. Lay NOT at the bar; MAP MODE measured

Tool: `tools/body/strip_rest.py` (`build [--relax] | target [--map] | sheet`, `--snap` = frozen carried_target in
out/shoulder/snap). Output: out/shoulder/strip_rest.npz (ids, loc, V0, V1, snap, bridge per side). Nothing wired.
STATE: the npz on disk is the OLD LINEAR LAY. The one attempt at a better lay (`build --relax`, off by default,
never written to the npz) passes the edge limits on the right and fails on the left. No second design made.

## Method (general core: lscm, Unfold, Curve, relay, relax)
A's patch under the band unfolded flat (LSCM); per bridge the apex = where A's normal is halfway between the two
mouths; a cubic through them; the bridge ends on the nearer side go ONTO the apex line; the rest by least squares
on the unfolded edge vectors; lifted back with heights from the band's neighbours. Band = rows 4 & beta == 1.

## The old lay's rest defects (new / old 0.49..1.80 l, 0.34..1.41 r; 2 turned l), measured
- The least squares runs on PLANE lengths and the unfold's scale is 0.32..1.41: where the plane is small (l, 30-37
  mm from the apex) real stretch is 1.4-1.8 (19 edges over 1.35 on l, 5 on r); on the groove wall edges come short.
- Short edges (9 under 0.75 a side): the bridging edges, now apex row to far wall (l 0.49-0.63, r 0.58-0.73),
  edges ALONG the apex row (l 0.59-0.72), and r 2326-2386 (0.34). The apex row puts all the new skin on the near
  side (rows 1.01, 1.07, 1.14, 1.16, 1.16) and squeezes the far side's first row (0.86).
- Min triangle quality: old band 0.296 (l) / 0.423 (r); the old lay 0.270 / 0.061.

## The attempt: `relax` (build --relax), and where it fails
Energy on REAL 3D edge lengths (sum l0 * (L / l0 - 1)^2, soft walls 0.82 / 1.28, a barrier on triangle area under
half of rest; L-BFGS through the lift), the apex row walked onto its line in 4 steps. Over 10 minutes a build.
- RIGHT: 0 edges outside 0.75..1.35; min quality 0.295 against the old band's 0.423 (fails that count).
- LEFT: 3 under 0.75, 11 over 1.35, min quality 0.116. The left apex row is not one mesh row: it zigzags 2444,
  2445 | 2386 | 2327..2332, and 2386-2327 is a 3.5 mm rest edge that ends 0.17-0.29 of rest on the line.
- Not measured on it: path / chord, off A, turned rest triangles, l / r difference, rest visibility. The old
  lay's rest visibility stands: outline front 3/4 2 px, others 0; depth change over 0.5 mm 4.5-6.8 cm2 a view.

## Posed edges 3.7-4.5x on B' (defect 2): mostly A's OWN (old lay, 3 poses, ratios against B' rest)
A's own = A's skin under the same edge (`Unfold.length(V=)`, the path between the edge's feet, posed / rest).
All worst edges run from the apex row up a wall: A's groove floor opens that much.
| pose | B' edge min..max, mean | A's own min..max, mean | edges over A + 0.15 | over 3.0 (rest under 0.75) |
|---|---|---|---|---|
| x:abd150:l | 0.55..3.80, 1.44 | 0.58..3.67, 1.43 | 6 of 330 | 12 (4) |
| x:flex170:l | 0.58..3.73, 1.47 | 0.60..3.52, 1.46 | 6 of 330 | 11 (4) |
| p4:heroic_leap@19:r | 0.60..4.50, 1.49 | 0.64..4.28, 1.47 | 16 of 332 | 15 (6) |
Worst: l 2333-2393 3.80 (A 3.20, rest 0.75), 2386-2446 3.76 (A 3.67, rest 0.70); r 2326-2386 4.50 (A 4.28, rest 0.34).

## The lay as a CARRY MAP only (`target --snap --map`): fill | map | A's own
B's rest is NOT changed. Per pose the band's target = (1 - w) * the fill + w * the re-laid band carried on A's
posed surface (the old lay in the npz), w = smoothstep of the arm's elevation, 45 -> 90 deg. Elevation = the upper
arm against the body's down in the trunk's frame (matches the x: names to 1 deg; rest = 38.3 deg). Ratios against
B's OLD rest. Cells: band edge min..max, mean, off A mm, turned triangles. A's own: min..max, mean.
| pose (elev, w) | fill | map | A's own |
|---|---|---|---|
| x:abd120:l (120, 1) | 0.69..2.41, 1.35, 9.3, 0 | 0.70..2.78, 1.37, 1.4, 0 | 0.65..3.01, 1.34 |
| x:abd150:l (150, 1) | 0.43..2.69, 1.48, 25.5, 0 | 0.55..3.91, 1.49, 1.4, 1 | 0.58..3.67, 1.43 |
| x:abd170:l (170, 1) | 0.39..2.83, 1.52, 31.2, 2 | 0.55..3.81, 1.54, 1.4, 1 | 0.60..3.62, 1.47 |
| x:flex170:l (169, 1) | 0.25..2.75, 1.52, 33.6, 3 | 0.58..3.67, 1.53, 1.4, 1 | 0.60..3.52, 1.46 |
| p4:iron_vow@72:l (109, 1) | 0.22..2.33, 1.12, 20.6, 12 | 0.15..2.98, 1.11, 1.4, 3 | 0.21..2.20, 1.05 |
| p4:heroic_leap@7:r (98, 1) | 0.33..3.17, 1.23, 16.9, 12 | 0.46..2.89, 1.29, 1.3, 1 | 0.54..2.67, 1.25 |
| p4:heroic_leap@9:r (123, 1) | 0.27..3.60, 1.36, 17.7, 21 | 0.43..3.46, 1.47, 1.3, 4 | 0.48..3.10, 1.42 |
| p4:heroic_leap@19:r (171, 1) | 0.56..3.32, 1.51, 33.5, 2 | 0.61..4.55, 1.52, 1.3, 0 | 0.64..4.28, 1.47 |
| p4:heroic_leap@20:r (157, 1) | 0.51..3.33, 1.48, 33.5, 12 | 0.55..4.42, 1.49, 1.3, 0 | 0.57..4.19, 1.43 |
| x:abd90_int60:l (90, 1) | 0.62..2.11, 1.22, 6.9, 0 | 0.63..2.95, 1.26, 1.4, 2 | 0.63..2.46, 1.22 |
| crossbow_shoot@10:r (75, 0.74) | 0.32..1.73, 0.97, 7.2, 0 | 0.27..1.60, 0.98, 2.2, 0 | 0.27..1.56, 0.96 |
| cast_bolt@3:r (67, 0.47) | 0.62..1.76, 1.10, 6.9, 0 | 0.49..1.66, 1.10, 3.6, 0 | 0.60..1.68, 1.09 |
| p4:heroic_leap@25:r (60, 0.27) | 0.49..1.98, 1.08, 11.4, 0 | 0.53..1.95, 1.08, 8.4, 0 | 0.45..1.88, 1.09 |
No x:abd45 / 60 / 90 exists in poses.npz: the last four rows are the nearest by elevation (45.2 deg,
p4:shield_charge@20:l, w 0.00: map = fill, 0.89..1.22, 3.8 mm).
- PROOF: 49 of 141 poses have elevation <= 45 deg; max |map - fill| over them is 0.0 exactly (the general formula,
  no shortcut). Rest l / r: elevation 38.3, w 0, |map - fill| 0.0, and the fill there IS B's rest (0.00 mm).
- TRANSITION (8 poses, w 0.27..0.74): nothing turns over in the map (the fill has up to 3); worst edge 1.95 (fill
  2.14). The shortest edge is 0.05-0.13 under the fill's in 5 of 8 (0.43-0.50 where A's own is 0.60-0.66 in 3):
  a mild extra squeeze, no crumple.
- 9 named, map against the fill: off A better in 9 of 9 (1.3-1.4 mm against 9-34), turned no worse in 8 of 9
  (abd150: 1 against 0), means within 0.11; worst edge no worse in only 2 of 9 (leap 7 and 9).
- 9 named, map's worst edge against A's own worst + 0.15: 2 of 9 (abd120; flex170 on the line). Over A's worst
  by 0.19-0.36 in 6, by 0.78 at iron_vow@72. Means within 0.03-0.07 of A's.
- NOT better than the fill on every count. The map shows A's hollow and with it A's own 3.5-4.3 floor edges,
  plus the lay's short edges on top. At x:abd90_int60 it loses on edge (2.95 / 2.11) and turned (2 / 0).

## What a next lay needs (not built), and what was not touched
- An apex row the mesh HAS (one edge loop; on l the bridge ends change mesh row at 2386), the new skin split over
  both sides, a quality term, a faster `Unfold.locate`. With such a lay the map's worst edges fall to about A's.
- `cmd_sheet` is unchanged and unrun (2 columns, no A column, no numbers line, no `--under`): a worker's job.
  Commands: `python tools/body/strip_rest.py target --snap --map [--poses a,b]` (98 s for the default 19 poses).

## Lay 2 (carry map only): 10 Nov, lead 19's solver. NOT at the bar on the left; right 3 of 4 clean
The STATE line at the top is superseded: `out/shoulder/strip_rest.npz` is now LAY 2 (adds u, h per side); the old
linear lay is `out/shoulder/strip_rest_l18.npz` (`--lay l18` loads it; it reproduces to 0.000 mm through the new code).
B's rest, weights, order: untouched. Cells as above: edge min..max, mean, off A mm, turned. A's own is under LAY 2's edges.
| pose (elev, w) | fill | map, lay 2 | A's own | old map (l18): max, turned |
|---|---|---|---|---|
| x:abd120:l (120, 1) | 0.69..2.41, 1.35, 9.3, 0 | 0.60..2.84, 1.47, 1.4, 1 | 0.64..2.87, 1.34 | 2.78, 0 |
| x:abd150:l (150, 1) | 0.43..2.69, 1.48, 25.5, 0 | 0.42..3.15, 1.60, 1.4, 1 | 0.44..2.82, 1.43 | 3.91, 1 |
| x:abd170:l (170, 1) | 0.39..2.83, 1.52, 31.2, 2 | 0.42..3.14, 1.63, 1.4, 1 | 0.46..2.89, 1.46 | 3.81, 1 |
| x:flex170:l (169, 1) | 0.25..2.75, 1.52, 33.6, 3 | 0.47..3.07, 1.62, 1.4, 1 | 0.50..2.86, 1.45 | 3.67, 1 |
| p4:iron_vow@72:l (109, 1) | 0.22..2.33, 1.12, 20.6, 12 | 0.17..2.25, 1.14, 1.4, 2 | 0.18..2.10, 1.03 | 2.98, 3 |
| p4:heroic_leap@7:r (98, 1) | 0.33..3.17, 1.23, 16.9, 12 | 0.26..2.63, 1.34, 1.3, 0 | 0.33..2.58, 1.25 | 2.89, 1 |
| p4:heroic_leap@9:r (123, 1) | 0.27..3.60, 1.36, 17.7, 21 | 0.19..3.00, 1.52, 1.3, 0 | 0.28..2.92, 1.41 | 3.46, 4 |
| p4:heroic_leap@19:r (171, 1) | 0.56..3.32, 1.51, 33.5, 2 | 0.46..3.26, 1.58, 1.3, 1 | 0.50..3.41, 1.45 | 4.55, 0 |
| p4:heroic_leap@20:r (157, 1) | 0.51..3.33, 1.48, 33.5, 12 | 0.47..3.16, 1.54, 1.3, 0 | 0.51..3.23, 1.41 | 4.42, 0 |
| x:abd90_int60:l (90, 1) | 0.62..2.11, 1.22, 6.9, 0 | 0.55..2.49, 1.36, 1.4, 1 | 0.67..2.35, 1.24 | 2.95, 2 |
| crossbow_shoot@10:r (75, 0.74) | 0.32..1.73, 0.97, 7.2, 0 | 0.40..2.01, 1.02, 2.2, 0 | 0.34..1.50, 0.99 | 1.60, 0 |
| cast_bolt@3:r (67, 0.47) | 0.62..1.76, 1.10, 6.9, 0 | 0.62..1.77, 1.12, 3.7, 0 | 0.65..1.72, 1.10 | 1.66, 0 |
| axe_heavy@7:r (67, 0.47) | 0.57..2.14, 0.98, 6.4, 0 | 0.47..2.16, 1.00, 4.1, 0 | 0.63..1.76, 1.00 | - |
| p4:heroic_leap@5:r (65, 0.43) | 0.56..1.85, 1.10, 9.9, 3 | 0.49..1.80, 1.11, 5.7, 0 | 0.58..1.87, 1.09 | - |
| axe_back@3:l (65, 0.43) | 0.70..1.46, 1.06, 4.8, 0 | 0.56..1.48, 1.08, 3.0, 1 | 0.65..1.51, 1.07 | - |
| p4:idle_warden_town@126:r (65, 0.42) | 0.51..1.87, 1.14, 5.4, 0 | 0.56..1.75, 1.14, 3.8, 0 | 0.61..1.78, 1.11 | - |
| axe_back@2:l (65, 0.41) | 0.70..1.43, 1.09, 4.0, 0 | 0.64..1.56, 1.11, 2.8, 1 | 0.78..1.61, 1.08 | - |
| p4:heroic_leap@25:r (60, 0.27) | 0.49..1.98, 1.08, 11.4, 0 | 0.54..1.88, 1.08, 8.2, 0 | 0.49..1.83, 1.09 | 1.95, 0 |
- PROOF (4), exact: 49 of 141 poses have elevation <= 45 deg; max |map - fill| over them 0.0. Rest l / r: elevation
  38.3, w 0.0, |map - fill| 0.0, fill off B's rest 0.00 mm; the lay rebuilt from the stored u matches the npz to 0.000 mm.
- (1) TURNED = 0: met on 3 of 9 (leap 7, 9, 20). 1 on abd120 / 150 / 170, flex170 and leap@19; 2 on iron_vow@72.
  Sum over the nine 7 (old lay 11). On the LEFT one triangle is turned in EVERY pose with w > 0, the mild ones too
  (axe_back at w 0.41): it is the lay, not A's surface. Which triangle: not located (the build's own count of rest
  triangles turned, against A's normals, is 0; the map tests against the carried B' normals).
- (2) WORST EDGE <= A's own + 0.15: met on 6 of 9 (abd120 -0.03, iron_vow +0.15 on the line, leap 7 +0.05, 9 +0.08,
  19 -0.15, 20 -0.07). NOT met: abd150 +0.33, abd170 +0.25, flex170 +0.21 (old lay +0.24, +0.19, +0.15 against ITS
  A's own of 3.67, 3.62, 3.52; in absolute terms the worst edges fell 3.91 -> 3.15, 4.55 -> 3.26). The solver ends
  with those limits still broken on the left (74 edge-poses over, worst +0.45 on its own estimate): with the - row on
  the line the 48 poses cannot all be met. Which edges: not located. The map's MEAN is now 0.13-0.17 over A's mean on
  the left (old 0.03-0.07): the lay's rest edges run 0.50..2.06 of B's (l), 0.47..1.94 (r).
- (3) TRANSITION (8 poses, w 0.27..0.74): right 6 of 6 nothing turned; left 2 of 2 have the 1 turned triangle (fill
  0). Worst edge over the fill's + 0.15 in 1 of 8: crossbow_shoot@10:r 2.01 against 1.73 (+0.28; A's own 1.50).
  Shortest edge under the fill's by 0.14 at axe_back@3:l (the limit is 0.13), 0.10 axe_heavy@7, <= 0.07 elsewhere.
  x:abd90_int60:l: 1 turned, 2.49 against the fill's 2.11 (+0.38; +0.14 over A's own).
- (5) OFF A: 1.3-1.4 mm on all nine.
What changed in the lay (`lay2`, general core; `relay(..., design=, side=, u_given=)`):
1. It is judged IN THE POSES IT IS USED IN: rest spring on real lengths + per pose walls (posed edge / B's rest <= A's
   own worst under the lay's edges + 0.05, >= the smaller of A's and the fill's shortest - 0.10) + the triangle
   barrier in every pose of the side with w > 0 (l 48, r 44 of poses.npz; THE NINE NAMED ARE AMONG THEM, no held-out set).
2. The apex row is walked onto the line on the rest surface alone (8 steps), slides along it, then 3 pose passes. Left:
   the - side's bridge ends (cfg "side"; the nearer + side crushes on the line: rest edge 0.18, 1 rest triangle
   turned; the - side walks on clean, 0.72..1.43, 0 turned) and a second snapping round (11 points on the line). Right:
   the nearer (-) side, 10 points.
3. `Unfold.locate` tries the 16 nearest triangles, then the full search (same answers); an energy call is 21 ms.
Commands: `python tools/body/strip_rest.py build --snap [--only l|r] [--side l=-1,r=0] [--set '{"iters": 800}']` (about
2-4 min a side; writes strip_rest.npz); `target --snap --map [--lay l18] [--poses a,b]` (about 100 s for the 19).
Not done: ONE mesh edge loop as the apex row (in the region's edge list the bridge ends of either side are two paths
plus loose points, `chain_order` prints it; no single-loop row was built); the new skin is split by the energy, not by
a rule; no run over all 141 poses; no sheet; `cmd_target` (B' as a rest) and `build --relax` not rerun; the map is not
in `Her`. `out/shoulder/strip_rest_l19_round1.npz` = the left before its second round (3.22 / 3.22 / 3.15, iron_vow 3 turned).
