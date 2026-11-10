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

## Lay 2: where it fails (located)
`python tools/body/strip_rest.py turned --snap [--poses a,b] [--lay l18]` (new, read-only: per pose the turned
triangles and the worst / over-limit band edges, ids region-local + tag (A apex row, b other bridge end, . band,
r fixed ring) and mesh vertex ids, the split ratio = lay (lay rest edge / B's old rest) x pose, A's own along the edge).
Run on abd150, abd170, flex170, abd90_int60, axe_back@3, iron_vow@72 (l), leap@19, crossbow_shoot@10 (r).
- LEFT, the turned triangle: ONE, the same in all 6 left poses: tri 275 = 2326A / 2327b / 2386b (mesh 5551 / 5552 /
  5611): one apex-row point and two bridge ends of the other (+) side, AT mesh row 2386 where the bridge ends change
  row. It is INVERTED IN THE LAY ITSELF, at rest: signed area -1.64 x B's (against A's normals at the feet), quality
  0.90 (a full-size triangle, not a sliver; B's own is 0.30); its normal . A's rest triangles under its 3 points =
  -0.75, -0.86, -0.97. So the build's "rest triangles turned 0" is wrong for it (not traced why). Not a fold of A:
  in the opened poses its 3 carriers' normals agree (least mutual dot 0.93-0.99; rest 0.49) and its normal is -0.95
  to -1.0 against all three. Turned by the map alone at w = 1 (fill: not turned); the blend only inherits it.
  `stats` tests the sign of ct.facing with the mixed carried vertex normals against B's rest sign; the geometric
  test against A's carrier triangles agrees here, so the measure is right for this one.
  iron_vow@72's second: tri 110 = 2386b / 2327b / 2387. (mesh 5611 / 5552 / 5612), the neighbour across edge
  2327-2386; lay quality 0.24 (B 0.63), sound at rest (+0.94), turned in the fill too; there A does fold (carriers'
  least mutual dot 0.43 / 0.00).
- LEFT, the edges over A's worst + 0.15: all at point 2386b (mesh 5611), all the LAY'S OWN REST STRETCH times A's
  stretch as it is (pose factor = A's own along the edge to 0.01-0.02):
  edge 173 2327b-2386b: abd150 3.15 = lay 1.34 x 2.35 (+0.18 on the limit), abd170 3.05 (+0.01), flex170 2.96;
  edge 206 2385A-2386b: abd150 3.12 = lay 1.66 x 1.88 (+0.16), abd170 3.14 (+0.11), flex170 3.07 (+0.07);
  edge 208 2386b-2446.: abd90_int60 2.49 = lay 1.85 x 1.34 (the pose's worst; fill 1.68), iron_vow 2.25 = 1.85 x 1.21;
  edge 243 2446.-2506. abd150 3.01 (+0.04) = lay 1.34 x 2.25; edge 209 2387.-2388. 2.97 = lay 1.94 x 1.53 (on the limit).
  The lay's longest rest edges (l): 212 2388-2389 2.06, 175 2328b-2329b 2.02, 209 1.94, 156 2318r-2319 1.86.
- RIGHT: tri 290 = 2445. / 2386A / 2385b (mesh 24628 / 24569 / 24568), again at row 2385 / 2386: a SLIVER in the lay
  (area 0.37 x B's, quality 0.18; B's 0.91), its apex point's carrier facing off it at rest (-0.15; carriers' least
  mutual dot 0.18: two walls). leap@19: near edge-on (its normal . A's carriers +0.06 / +0.33 / +0.13; the mixed
  normals -0.18 on the apex point tip the count): marginal. crossbow_shoot@10: truly turned at w = 1 (-0.37 / -0.50),
  not in the blend at w 0.74.
  crossbow_shoot@10:r worst edge: 262 = 2455. - 2456r (mesh 24638 / 24639), a BORDER edge to the fixed ring: 2.01 =
  lay 1.86 x 1.08 (A's own along it 1.14; fill 1.73; +0.36 on the limit). The lay's rest stretch, not A.
- NOT DONE: no trial move was run (the helper's budget ended). Untested reading: point 2386 (l) lies across the line
  2326-2327 and 1.3-1.85 x too far from 2385 / 2446 / 2327; putting it back on its own side and nearer those three
  should clear tri 275 and edges 173 / 206 / 208 together. Right: 2445 against the 2385-2386 edge, 2455 toward 2456r.

## Lay 3 (lay 2 repaired): 10 Nov, builder. NOT at the bar; WORSE than lay 2 on the nine. Lay 2 is back as strip_rest.npz
`out/shoulder/strip_rest_l19_lay3.npz` = the repaired lay (measured below); `strip_rest.npz` = lay 2 again (byte copy of
`strip_rest_l19_lay2.npz`); `strip_rest_l18.npz` untouched. B's rest, weights, order: untouched.
New in `strip_rest.py` (general core, no ids): `lay_faults` (per triangle signed area against A's normals at the feet /
B's rest area, quality lay and rest; per edge lay / rest) and `untangle` (the faulty points re-placed one at a time on
A's surface by a pattern search in the unfold's plane: first every triangle at the point sound, then the least worst
max(r, 1 / r) - 1 of its edges; ring and apex row never move; the free set grows a ring while faults remain).
`relay(..., repair={})` runs it; `build --repair [--fix '{"lim": [0.6, 1.6], "qrel": 0.5, "amin": 0.25, "grow": 2}']`
untangles the npz's lay without a solve (about 1 min); a fresh lay 2 build runs it after the solve.
- THE BUILD'S COUNT, traced and fixed: relay compared the lay's facing with the sign of B's REST triangle against A's
  normals at B's rest feet. B's rest tri 275 (l) bridges the fold and faces against those normals, so the inverted lay
  triangle "agreed". Now against B's own rest normals: lay 2 l counts 1 (tri 275, area -1.12 x B's by lay_faults),
  after the repair 0; the old measure is printed beside it (it says 1 AFTER the repair). `lay2`'s barrier divides by
  the same signed a0, so it HELD tri 275 inverted: that is the cause of the fault. lay2 NOT changed, not rerun.
- REST, lay 2 -> lay 3 (default limits): l turned 1 -> 0, faulty triangles 30 -> 0, edges outside 0.6..1.6 14 -> 2
  (131 2261-2262 0.50, 204 2384-2385 0.59, both between held points), rest edge 0.50..2.06 -> 0.50..1.48; r turned 0,
  faulty 21 -> 0, edges out 6 -> 0, 0.47..1.94 -> 0.67..1.50 (tri 290 and edge 262 repaired at rest).
  COST: the default quality floor (0.5 x rest) names 30 / 21 triangles, not the located few: 91 points moved on the l
  (3 rounds), 64 on the r (2 rounds), mostly 0.1-2.8 mm (the full per-point list is the build's stdout; max not read off).
- POSES (target --snap --map, lay 3). Cells: edge min..max, mean, off A mm, turned. A's own is under LAY 3's edges.
| pose (elev, w) | fill | map, lay 3 | A's own | bar |
|---|---|---|---|---|
| x:abd120:l | 0.69..2.41, 1.35, 9.3, 0 | 0.60..3.13, 1.43, 1.4, 0 | 0.64..2.78, 1.35 | edge +0.35 FAIL |
| x:abd150:l | 0.43..2.69, 1.48, 25.5, 0 | 0.42..4.54, 1.56, 1.4, 1 | 0.44..3.50, 1.44 | 1 turned, +1.04 FAIL |
| x:abd170:l | 0.39..2.83, 1.52, 31.2, 2 | 0.42..4.47, 1.60, 1.4, 1 | 0.46..3.44, 1.47 | 1 turned, +1.03 FAIL |
| x:flex170:l | 0.25..2.75, 1.52, 33.6, 3 | 0.47..4.32, 1.58, 1.4, 1 | 0.50..3.33, 1.46 | 1 turned, +0.99 FAIL |
| p4:iron_vow@72:l | 0.22..2.33, 1.12, 20.6, 12 | 0.17..2.29, 1.13, 1.4, 5 | 0.16..2.10, 1.05 | 5 turned, +0.19 FAIL |
| p4:heroic_leap@7:r | 0.33..3.17, 1.23, 16.9, 12 | 0.20..2.73, 1.32, 1.3, 0 | 0.22..2.56, 1.25 | 0 turned, +0.17 FAIL |
| p4:heroic_leap@9:r | 0.27..3.60, 1.36, 17.7, 21 | 0.26..3.38, 1.51, 1.3, 3 | 0.29..2.91, 1.43 | 3 turned, +0.47 FAIL |
| p4:heroic_leap@19:r | 0.56..3.32, 1.51, 33.5, 2 | 0.46..4.21, 1.58, 1.3, 0 | 0.50..3.56, 1.47 | 0 turned, +0.65 FAIL |
| p4:heroic_leap@20:r | 0.51..3.33, 1.48, 33.5, 12 | 0.47..4.04, 1.54, 1.3, 0 | 0.48..3.37, 1.43 | 0 turned, +0.67 FAIL |
| x:abd90_int60:l (w 1) | 0.62..2.11, 1.22, 6.9, 0 | 0.62..2.38, 1.32, 1.4, 1 | 0.60..2.28, 1.24 | 1 turned, fill +0.27 FAIL |
| crossbow_shoot@10:r (0.74) | 0.32..1.73, 0.97, 7.2, 0 | 0.26..1.65, 1.01, 2.2, 0 | 0.28..1.56, 0.98 | met |
| cast_bolt@3:r (0.47) | 0.62..1.76, 1.10, 6.9, 0 | 0.62..1.77, 1.11, 3.7, 0 | 0.61..1.69, 1.09 | met |
| axe_heavy@7:r (0.47) | 0.57..2.14, 0.98, 6.4, 0 | 0.43..1.82, 1.00, 4.1, 0 | 0.63..1.77, 1.00 | met |
| p4:heroic_leap@5:r (0.43) | 0.56..1.85, 1.10, 9.9, 3 | 0.60..1.80, 1.11, 5.8, 0 | 0.50..1.87, 1.09 | met |
| axe_back@3:l (0.43) | 0.70..1.46, 1.06, 4.8, 0 | 0.76..1.48, 1.07, 2.9, 0 | 0.65..1.51, 1.07 | met |
| p4:idle_warden_town@126:r (0.42) | 0.51..1.87, 1.14, 5.4, 0 | 0.59..1.75, 1.14, 3.2, 0 | 0.59..1.77, 1.11 | met |
| axe_back@2:l (0.41) | 0.70..1.43, 1.09, 4.0, 0 | 0.77..1.49, 1.10, 2.6, 0 | 0.80..1.61, 1.08 | met |
| p4:heroic_leap@25:r (0.27) | 0.49..1.98, 1.08, 11.4, 0 | 0.54..2.00, 1.08, 8.4, 0 | 0.49..1.88, 1.10 | met |
- THE NINE: 0 of 9 at the bar (lay 2: turned 3 of 9, edge 6 of 9). The worst posed edges ROSE (abd150 3.15 -> 4.54,
  leap@19 3.26 -> 4.21): the repair judges the REST alone; lay 2 was balanced in the poses, and moving 91 / 64 points by
  rest criteria broke that balance. A rest-only untangle with these limits is the wrong tool for the pose bar.
- TRANSITION: 8 of 8 met (nothing turned, worst edge <= the fill's + 0.15; the two left poses no longer carry a turned
  triangle; crossbow_shoot@10:r 2.01 -> 1.65). x:abd90_int60:l NOT met (1 turned, +0.27 on the fill).
- PROOF: 49 of 141 poses have elevation <= 45 deg; max |map - fill| over them 0.0. Rest l / r: w 0.0, |map - fill|
  0.0; relay vs the npz 0.000 mm. OFF A: 1.3-1.4 mm on the nine.
- Tri 275 (l) is gone in every pose. The left's one turned triangle is now tri 274 = 2325 / 2386b / 2385A (mesh 5550 /
  5611 / 5610): it lies ACROSS A's fold at rest in lay 3 (its normal . A's rest carriers +0.59 / -0.30 / +0.03,
  carriers' mutual dot -0.73), positive only on the SUMMED foot normals that lay_faults uses: the measure passes a
  triangle that straddles the apex. The test wanted: positive against EACH corner's carrier normal.
- Tri 110 at p4:iron_vow@72:l: no longer turned (not in the list). The 5 turned there: tri 109 2385A/2386b/2446. (fill
  turned too; carriers' least mutual dot in the pose -0.75: A's own fold), 141 2503/2504/2564 (-0.44: A's fold), 274
  (the one above; -0.03), 253 2259/2326A/2325 (0.48; lay rest -0.12 on the apex point), 289 2381/2442/2441 (0.11).
  A's own triangles turned under them: NOT counted (the carriers' mutual dots are the only evidence).
Commands: `python tools/body/strip_rest.py build --snap --repair` (reads and rewrites strip_rest.npz: copy
strip_rest_l19_lay2.npz over it first), `target --snap --map`, `turned --snap --poses a,b`.
Not done: a narrow run (`--fix '{"qrel": 0.25, "grow": 0}'`, or only turned triangles + edges over a limit: few points
moved; the located reading of point 2386 l is still untested as a small move); the pose walls of lay2 inside the
untangle; the per-corner facing test; lay2's signed a0 fixed and the left re-solved (the direct cure of tri 275); the
structural road (apex row through the mesh row that does not change at 2386): not started; turned on all nine (run on
iron_vow@72, abd150, leap@19 only; leap@9's 3 turned not located); all 141 poses.

## Lay 4 (orientation in the plane): 10 Nov, lead 19's solver. LEFT at the bar (5 of 5 named, abd90_int60, 2 of 2 transition); right = lay 2's
ACTIVE `out/shoulder/strip_rest.npz` = LAY 4 = the left re-solved + lay 2's right, byte for byte (copy:
`strip_rest_l19_lay4.npz`). `strip_rest_l19_lay4_r.npz` (= `_lay4c.npz`) = the same left + the RIGHT re-solved too (NOT
active: see below). `_lay2`, `_lay3`, `_l18` untouched (build now refuses to write them). `_lay4a` / `_lay4b`: steps on the way.
Cells: turned; worst edge map / A's own (under lay 4's edges) / fill; excess = map - A's own (nine) or map - fill (rest); off A mm.
| pose (w) | turned | map / A's own / fill | excess | off A | bar |
|---|---|---|---|---|---|
| x:abd120:l | 0 | 2.56 / 2.85 / 2.41 | -0.29 | 1.4 | met |
| x:abd150:l | 0 | 3.03 / 2.93 / 2.69 | +0.10 | 1.4 | met |
| x:abd170:l | 0 | 2.99 / 2.87 / 2.83 | +0.12 | 1.4 | met |
| x:flex170:l | 0 | 2.94 / 2.89 / 2.75 | +0.05 | 1.4 | met |
| p4:iron_vow@72:l | 0 | 2.31 / 2.27 / 2.33 | +0.04 | 1.4 | met |
| p4:heroic_leap@7:r | 0 | 2.63 / 2.58 / 3.17 | +0.05 | 1.3 | met (lay 2's) |
| p4:heroic_leap@9:r | 0 | 3.00 / 2.92 / 3.60 | +0.08 | 1.3 | met (lay 2's) |
| p4:heroic_leap@19:r | 1 | 3.26 / 3.41 / 3.32 | -0.15 | 1.3 | 1 turned FAIL (lay 2's) |
| p4:heroic_leap@20:r | 0 | 3.16 / 3.23 / 3.33 | -0.07 | 1.3 | met (lay 2's) |
| x:abd90_int60:l (1) | 0 | 2.24 / 2.35 / 2.11 | fill +0.13 | 1.4 | met |
| crossbow_shoot@10:r (0.74) | 0 | 2.01 / 1.50 / 1.73 | fill +0.28 | 2.2 | FAIL (lay 2's) |
| cast_bolt@3:r (0.47) | 0 | 1.77 / 1.72 / 1.76 | fill +0.01 | 3.7 | met |
| axe_heavy@7:r (0.47) | 0 | 2.16 / 1.76 / 2.14 | fill +0.02 | 4.1 | met |
| p4:heroic_leap@5:r (0.43) | 0 | 1.80 / 1.87 / 1.85 | fill -0.05 | 5.7 | met |
| axe_back@3:l (0.43) | 0 | 1.49 / 1.51 / 1.46 | fill +0.03 | 3.0 | met |
| p4:idle_warden_town@126:r (0.42) | 0 | 1.75 / 1.78 / 1.87 | fill -0.12 | 3.8 | met |
| axe_back@2:l (0.41) | 0 | 1.47 / 1.56 / 1.43 | fill +0.04 | 2.6 | met |
| p4:heroic_leap@25:r (0.27) | 0 | 1.88 / 1.83 / 1.98 | fill -0.10 | 8.2 | met |
- THE NINE, active lay 4: 8 of 9 (lay 2: turned 3 of 9, edge 6 of 9). Left turned sum 6 -> 0, excess +0.33 / +0.25 / +0.21
  -> +0.10 / +0.12 / +0.05. Left lay rest: plane rule 0 turned, no corner facing off A, rest edge 0.49..1.99 (mean 1.11).
- PROOF: 49 of 141 poses have elevation <= 45 deg; max |map - fill| over them 0.0. Rest l / r: w 0.0, |map - fill| 0.0,
  relay vs the npz 0.000 mm (run on `_lay4_r`, whose left is the active left; the right lines on lay 2's right in the first lay 4 run).
- TURNED LEFT in the active lay, with A's own count (A's own = the same triangle with its feet on A, no height, A's
  normals; `turned` prints it per pose): ONE, tri 290 r at leap@19 (lay 2's sliver). A's own under it: NOT turned
  (corners +0.04 / +0.28 / +0.14, edge-on in A too), A's own count in that pose 0, fill not turned: the lay's, not A's
  fold. Tri 110 / 109 / 141 at iron_vow@72:l: not turned in lay 4 (map 0; A's own count there 0 turned, 14 with a corner
  facing off; fill 12). At w = 1 only (not in the blend): tri 290 at crossbow_shoot@10:r; tri 98 / 100 / 271 at leap@5:r
  (A's own turned under 98 and 271, 100 turned in the fill). A's own count: leap@9:r 1 (tri 292), leap@5:r 2, leap@25:r 1; else 0.
- `_lay4_r` (right re-solved from lay 2's, same settings): the nine 9 OF 9 (leap@7 0, 2.63 / 2.58 +0.05; @9 0, 2.98 /
  2.92 +0.06; @19 0 TURNED, 3.32 / 3.31 +0.01; @20 0, 3.14 / 3.13 +0.01). NOT made active, by the storing rule: its
  excess is higher than lay 2's on @19 (-0.15 -> +0.01) and @20 (-0.07 -> +0.01), inside the bar; crossbow_shoot@10:r
  is worse (2.07 against the fill's 1.73, +0.34); shortest edge at leap@7 0.11 (A's own 0.19; lay 2 0.26 / 0.33); rest
  edges r 0.42..2.35 (lay 2 0.47..1.94). Edge 2455-2456 not cured. Transition 7 of 8 in both. The lead's call.
What changed (`strip_rest.py`):
1. ONE orientation rule, `plane_area`: a lay triangle is right when its signed area in the unfold's plane is over 0
   (A's own unfolded triangles' sign); `corner_facing` per corner where there is no plane. lay2's barrier: the plane at
   rest, the carried normals in a pose, both over B's UNSIGNED rest area (the signed one held tri 275 inverted). The
   build's count, `lay_faults`, `untangle` (now a safety net on turned triangles only; it moved 0 points) use it;
   `turned` prints the rule against the map count's measure at rest: AGREE on lay 2 (1: tri 275), lay 4 (0), both sides.
2. lay2: `start` (from a stored lay and its stored apex row, no walk); `ratchet` (a pose's limit never rises between
   passes: A's own worst is read under the lay's edges and moved with the lay, 2.88 -> 3.14 -> 2.95, so the limit chased
   it); poses up to 90 deg are also held to the fill's worst + capm (cfg `fill_bar`); run with wall 150.
3. `--file` (which lay npz), `--start`; stored `snap` is used on reload (lay 3 had lost its 11th apex point).
Commands: `build --snap --file X.npz --only l --start strip_rest_l19_lay2.npz` (lay 4a) -> `--start 4a --set '{"passes":
4, "wall": 150}'` (4b) -> both sides `--start 4b --set '{"passes": 3, "wall": 150, "capm": 0.05}'` (4c = `_lay4_r`);
`target --snap --map [--file X.npz]`; `turned --snap [--file X.npz] --poses a,b`. Logs: `out/shoulder/build_l19_lay4*.log`,
`map_l19_lay4c.log`, `turned_l19_lay4.log` (the active file, 18 poses).
Not done: `target --map` not rerun on the composite active file (its left rows are `_lay4_r`'s, its right rows lay 2's;
`turned` WAS run on it and gives the same turned / worst-edge numbers); the first start put one slid apex point 13 mm back
on the line's end (fixed before 4c; 4a / 4b began from that jolt); the right alone for tri 290 without the cost above;
edge 2455-2456; lay 3's left as a second start; per-corner barrier in the poses; all 141 poses; a fresh build from B's
feet under the new rule; the sheet; the map is not in `Her`.

## Lay 5 (right): 10 Nov, lead 20's solver
NOT MET, NOT PROMOTED: active `strip_rest.npz` stays lay 4. Best: `out/shoulder/strip_rest_l20_f.npz` (left = lay 4's,
right re-solved from lay 4). 8 of 10 right poses at every check; fails crossbow edge and axe_heavy shortest.
| pose (w) | turned | map / ref (A's own nine, fill rest) | excess | shortest map / A's own | rest r | bar |
|---|---|---|---|---|---|---|
| p4:heroic_leap@7:r | 0 | 2.65 / 2.58 | +0.07 | 0.29 / 0.31 (0.94) | 0.51..1.90 | met |
| p4:heroic_leap@9:r | 0 | 3.02 / 3.40 | -0.38 | 0.23 / 0.27 (0.85) | | met |
| p4:heroic_leap@19:r | 0 | 3.31 / 4.17 | -0.86 | 0.47 / 0.36 | | met (tri 290 cured) |
| p4:heroic_leap@20:r | 0 | 3.21 / 3.94 | -0.73 | 0.42 / 0.36 | | met |
| crossbow_shoot@10:r (0.74) | 0 | 1.96 / 1.73 | +0.23 | 0.38 / 0.37 | | FAIL edge (262, 2455-2456r, lay 1.82) |
| cast_bolt@3:r (0.47) | 0 | 1.78 / 1.76 | +0.02 | 0.62 / 0.61 | | met |
| axe_heavy@7:r (0.47) | 0 | 2.10 / 2.14 | -0.04 | 0.46 / 0.65 (0.71) | | FAIL short (edge 171 2325A-2385b, lay 0.51; lay 2 was 0.75 too) |
| p4:heroic_leap@5:r (0.43) | 0 | 1.80 / 1.85 | -0.05 | 0.53 / 0.56 | | met |
| p4:idle_warden_town@126:r (0.42) | 0 | 1.76 / 1.87 | -0.11 | 0.56 / 0.59 | | met |
| p4:heroic_leap@25:r (0.27) | 0 | 1.90 / 1.98 | -0.08 | 0.48 / 0.46 | | met |
Checks: 1 met (4 of 4); 2 not met (1.96 > 1.88); 3 met; 4 structural (w = 0 -> map = fill), `target --map` NOT rerun on `_f`;
5 not met at axe_heavy only (0.71 < 0.8). Note A's own worst read under `_f`'s edges rose (leap@19 3.41 -> 4.17), so
check 1's margin there is partly the reference moving with the lay. Variant `_b` hit crossbow 1.88 exactly (capwall 50,
capm 0.10) but left tri 290 turned and leap@7 short 0.50: the lifted-quality floor and the crossbow cap pull apart.
What changed (`strip_rest.py`, all off at defaults, old builds unchanged): lay2 keywords `qmin`/`qwall` (floor on each
rest lay triangle's LIFTED quality over B's; the plane quality floor did not cure tri 290: plane 0.35 was 0.17 lifted),
`capwall` / `hiwall` (wall factor over hi in fill-judged / other poses), `lo_own` / `lowall` (lo >= part of A's own
shortest, its wall), `rest_wall`, `ring_lim` (rest ratio limits on edges to the fixed ring). `turned` prints fill max,
the shortest map edge (id, lay, A's own, fill) and the lay's rest edge range.
Commands: `cp strip_rest_l19_lay4.npz strip_rest_l20_f.npz` then `build --snap --only r --start strip_rest_l19_lay4.npz
--file strip_rest_l20_f.npz --set '{"passes": 4, "wall": 150, "capm": 0.05, "qmin": 0.4, "qwall": 5, "capwall": 50,
"hiwall": 10, "lo_own": 0.95, "lowall": 50, "rest_wall": 30, "lim": [0.55, 1.85], "fold": [0.3, 0.25]}'` (80 s);
`turned --snap --file strip_rest_l20_f.npz --poses <the 10>`. Logs `out/shoulder/build_l20_*.log`, `turned_l20_*.log`.
Next (built, NOT measured): `_g` (= f + lim [0.6, 1.85], ring_lim [0.6, 1.5]) and `_h` (lim [0.58, 1.85], ring_lim
[0.55, 1.6], capwall 200) aim at the two fails (ring edge 262 down, edge 171 up); run `turned` on them first.

## The map in Her (lead 20's builder)

- Config: `HER["regions"]["girdle_{s}"]["support"]["map"] = {"file": "strip_rest.npz", "elev": [45.0, 90.0]}`. Her loads the lay through `strip_rest.HerStrip(cfg, h=self).load()` (no second Her). `Her.mapped` runs `strip_rest.map_targets` after the relax, on the registered part reference Vr, with w = `strip_rest.share(strip_rest.elevation(G))`, and writes only the list's band points (`hs.loc`). Normals are blended the same way and kept in `part()["map_N"]` (reference frame). With no key, w = 0, or inside `with h.map_off():`, the result is bit for bit the fill alone. cmd_map's `targets` now calls the same `map_targets`.
- Tests (61, all pass). T20: 25 of 141 poses have both arms at or under 45 deg; on 8 sampled, map minus no map is 0.0 m. T21 (abd150:l, heroic_leap@9:r, crossbow_shoot@10:r): the composed band equals a second path's result (a fresh HerStrip and Her, its own carry, placed as compose places it) to 0.0 m, normals 0.0 too; every vertex outside the moved bands (both sides when the other arm is over 45) is bit for bit the map-off target. T18 runs with the map off (the gate2 stage alone). T5 judges the pocket fill with the map off and prints a watch line: abd150 is filled max 3.03 with the map and 2.99 without (against B's old rest).
- Dev run, band edges (an end on the band, against B's OLD rest), map vs fill: add0:l w 0 1.15 vs 1.15; cast_bolt@0:l w 0.20 1.51 vs 1.48; abd150:l w 1 3.03 vs 2.69; abd170:l w 1 2.99 vs 2.83; heroic_leap@19:r w 1 3.28 vs 3.31; crossbow_shoot@10:r w 0.74 1.97 vs 1.69. region_shape edges (target_a_dev.npz): 121 edges over 2.5, 87 classed pocket, 33 A's own, 1 carrier; no crack.

## Lay 5 PROMOTED (lead 20): `strip_rest_l20_h.npz` is the active `strip_rest.npz` (backup `survivorsunchained_inputs\body\p1b_l20_lays\`)
Only the `*_r` keys differ from lay 4 (left byte for byte). Runner's `turned_l20_h.log` / `map_l20_h.log`: turned 0 on all ten right poses; the nine's right four map / A's own: leap@7 2.69 / 2.58 (+0.11), @9 3.07 / 3.40, @19 3.43 / 4.16, @20 3.33 / 3.93; crossbow_shoot@10:r 1.87 against fill 1.73 (+0.14, bar 1.88); cast_bolt@3 1.78 / fill 1.76, axe_heavy@7 2.08 / 2.14, leap@5 1.80 / 1.85, warden_town@126 1.76 / 1.87, leap@25 1.88 / 1.98; proof 49 poses <= 45 deg |map - fill| 0.0; rest feet facing off A 0. FACTS FOR GATE T: the absolute map worst on the right overhead rose against lay 4 (@19 3.26 -> 3.43, @20 3.16 -> 3.33; fill 3.32 / 3.33) while A's own under the lay's edges rose more (3.41 -> 4.16): the bar is met as written, but the reference moves with the lay. Shortest edge at axe_heavy@7 0.47 against A's own 0.64 (lay 2 0.75 of A's too). `carried_target.py test` ALL PASS with the map in Her on this lay.

## Lay 6 (lead 21's solver): 10 Nov. NOT MET; partial candidate `strip_rest_l21.npz` (left of `_l21_a` + lay 5's right)
Method change (`strip_rest.py`, all off at defaults, old builds unchanged):
- lay2 `judge` (`--set '{"judge": true}'`, built by `HerStrip.judge`): the poses' barrier uses THE MAP COUNT'S OWN RULE
  (cmd_turned / Her): normals = (1 - w) fill + w (B' rest vertex normals carried by the B' carrier), signed against B's
  rest facing, re-read each pass (about 3 s a pass). Triangles the fill itself turns in a pose weigh w x; `turnwall`
  multiplies the rest. `guard` / `guardwall`: minimum-width guard, no posed edge under guard x A's own shortest there.
- `turned` prints `FOLD deg`: the dihedral across band edges in the pose (map max / p95, fill max / p95): the smoothness number.
Runs (start lay 5 `_l20_h`, both sides, lay 5 `_h` settings + the new keys; logs `out/shoulder/build_l21_{a,b}.log`,
`turned_l21_{a,b}_all.log`, baseline `turned_l21_lay5_all.log`, all 141 poses):
- `_a`: judge, guard 0.8, guardwall 50. `_b`: + guardwall 500, turnwall 30 (worse: abd150 / abd170 / leap@7 +0.33; dropped).
| check | lay 5 | `_a` |
|---|---|---|
| (1) turned, w > 0 poses over the fill's own | crossbow@0 / @2:r, cast_flick@8:r, cast_bolt@6:l 3, leap@6:r 3 | crossbow@0 cured; @2:r 1, cast_flick@8:r 1, cast_bolt@6:l 1, leap@6:r 2; NEW leap@9:r 1, x:hadd40:l 1 |
| (1) fill-inherited (w <= 0.18, map = fill's count) | axe_back@0 / @1:r, warden_look@150:l, iron_vow@8:r, cast_bolt@11:l, reaver_look@27:l | the same: a carry map at w 0.02-0.18 cannot cure the fill; "turned 0 on EVERY pose" is not reachable as written |
| (2) guard, least map / A's own shortest (w > 0) | 0.64 (crossbow@2:r) | 0.66 (warden_look@150:l); 0.8 asked, the soft wall does not hold it |
| (3) T22 own + fill + the 5 + leap@0 / @30:l | leap@0 / @30:l fill +0.18 / +0.16 | left ALL met (leap@0 / @30:l +0.06); right leap@7 +0.20, cast_flick@8 +0.25 FAIL |
| (4) FOLD max deg leap@5/6/7/9/12/14/16/17/18/19/20:r | 123/143/110/137/122/47/62/54/75/87/71 | 120/148/107/151/135/45/63/51/71/72/64 |
| (5) rest corner facing off A | l 0, r 0 | l 0, r 2 |
`strip_rest_l21.npz` = `_a`'s `*_l` + lay 5's `*_r` (byte for byte): left gains leap@0 / @30:l (fill +0.18 / +0.16 -> +0.06),
cast_bolt@6:l 3 -> 1 turned, rest l facing off 0; right = lay 5. Proof (5) at <= 45 deg is structural (w = 0). `turned` /
`target --map` NOT rerun on the composite (left rows are `_a`'s run). Sheet not made.
WHY IT STALLS (the finding): the turned triangles left are not seen by lay2 even under the judge's normals. lay2 places a
band point at foot(u) + h N on its own unfold triangle; the B' carrier (car1, what Her and cmd_turned use) re-picks A's
closest triangle for that rest point, at the fold often the other wall. So positions differ, not only normals. Next: make
lay2's posed points the carrier's (carry the rest lay point with car1's face / bary / d0, rebuilt each pass, held as a
fixed linear map within a pass), or make car1 keep the lay's own foot face (the HerStrip carrier given face = the unfold's).

## Lay 6b (lead 21's max solver): 10 Nov. NOT MET; nothing promoted; active `strip_rest.npz` stays lay 5 (untouched)
CAUSE (a)/(b) CHECKED AND WRONG (`verify` on lay 5, live module): car1 re-binds only 5 of 147 right band points (3 of 147
left) to an A triangle other than the lay's own unfold triangle, none to the other wall (face normal dot >= 0.5 on all 8);
car1's posed point vs lay2's own model (foot + h N) differs at most 0.26 / 0.29 / 0.48 / 0.49 / 1.13 / 0.93 mm at
crossbow@0 / @2 / cast_flick@8 / leap@6 / @9 / @19:r, and the count is THE SAME under both placements (1 / 1 / 1 / 3 vs 2 /
0 / 0; cast_bolt@6:l 3 vs 3). So a lay-face carrier changes nothing. What differs is the NORMALS: with lay2's own normals
(A's at the foot) lay 5 has 0 turned at crossbow@0 / @2 / cast_flick@8. Lay 6's `judge` uses the count's normals, but it
reads them only at each pass's START. The triangles left turned straddle A's crease (`_a`: tri 290 r 2445/2386A/2385b,
rest quality 0.22 against B's 0.91, its corners' A normals mutual dot -0.03 / -0.57 in crossbow@2 / cast_flick@8; tri 117 /
291 at leap@6, 323 at leap@9, 305 at cast_bolt@6:l: A's own surface under them turned). Their facing flips with the lay's
own rest normals between passes.
Method change (`strip_rest.py` lay2, off at defaults, old builds unchanged): `boost` / `extra` (with `judge`). The shipped
count is re-read at each pass's END. Every triangle it still turns (any where w >= 0.5; where w < 0.5, those the fill does
not turn) gets weight x boost, and every posed edge under the guard gets its guard wall x boost (cap 1000 x). Up to
`extra` more passes run until the count sees none. `gwm` replaces the guard wall scalar.
Run `_l21b` (start lay 5, both sides, lay 5 `_h` settings + judge, guard 0.8, guardwall 50, boost 4, extra 8; 8 min; logs
`out/shoulder/build_l21b.log`, `turned_l21b_all.log` (+ `.tsv`), baseline `turned_l21_lay5_all.log`; backup
`survivorsunchained_inputs\body\p1b_l21_lays\`). Left: lay2's own count reached 0 at step 5. Right: stuck at 4 turned in
3 poses; the weights capped, L-BFGS 0 its, e 35k -> 404k, rest edges 0.40..2.00.
| req | lay 5 | `_l21b` |
|---|---|---|
| (1) turned where w >= 0.5 | crossbow@0:r 1, @2:r 1, cast_flick@8:r 1, cast_bolt@6:l 3, leap@6:r 3 | crossbow@0 and cast_bolt@6:l cured; @2:r 1, cast_flick@8:r 1, leap@6:r 2; NEW x:hadd40:l 1 (lay2's own count says 0: the model's 1 mm / height-cut gap) |
| (1) w < 0.5, map = the fill's own | axe_back@0:r 4 (w 0.18), @1:r 1 (0.08), warden_look@150:l 4 (0.02), iron_vow@8:r 4 (0.01), cast_bolt@11:l 1 (0.08), reaver_look@27:l 1 (0.13, fill 3) | the same |
| (2) guard, least map / A's own (w > 0) | 0.64 crossbow@2:r | 0.66 warden_look@150:l: NOT MET (0.8) |
| (4) FOLD max deg leap@5/6/7/9/12/14/16/17/18/19/20:r | 123/143/110/137/122/47/62/54/75/87/71 | 128/158/108/145/128/48/63/57/80/93/77: WORSE |
| (3) T22, (5), (6) | | not run: the candidate fails (1), (2) and (4) |
FINDING: on the right, more weight on the count's triangles crumples the hollow (FOLD up 6 to 14 deg). Those triangles
span A's own closed crease (A's normals -0.9 to -1.0 apart under one triangle). A carry map that rides A's surface
inherits the crease. The bowl the judge asks for needs the band OFF A's crease walls in the arm-behind poses: a band
point placed by a smooth surface over the pec and lat ridges (a hull or membrane of A's posed hollow), not by foot + h N.
Next: build that posed bowl as the map's target (then the count's normals come from a smooth surface), or cure the
right's crease on A first (judge fix 1's depinch at the armpit). The left half of `_l21b` (cast_bolt@6:l 3 -> 0) is not
kept: it adds x:hadd40:l 1 and moves the guard on the left (warden_look@150:l 0.66).

## Lay 7 (faired A, lead 21): 10 Nov, lead 21's max solver. NOT MET; NOT PROMOTED; active `strip_rest.npz` stays lay 5 (41be13363b7a)
Run: `build --start strip_rest_l20_h.npz --file strip_rest_l21c_a.npz --set` lay 5 `_h` keys + `judge` true, `guard` 0.8,
`guardwall` 50, `boost` 4, `extra` 8 (the `_l21b` recipe), both sides, LIVE (HER["fair_a"] on: design poses = faired A);
17m41 (first fairs; cache out/fair_a now warm). Candidate `strip_rest_l21c.npz` = `_l21c_a` (sha1 43cc9215b675).
Measured live (no `--snap`), all 141 poses: `turned_l21c_all.log`; baseline lay 5 on faired A `turned_l21c_lay5fair_all.log`
(+ `build_l21c_a.log`; backup with parse.py / check.py in `survivorsunchained_inputs\body\p1b_l21_lays\`).
RIGHT CONVERGED (lay2's count 0 turned, 0 under the guard at step 5); LEFT DID NOT (step 11: 4 turned in 2 poses,
20 edges under the guard, e 150k -> 3.0M, poses over hi 243 by up to 0.96: the boost escalates and L-BFGS stalls).
| req | lay 5 on faired A | `_l21c` |
|---|---|---|
| (1) turned, w >= 0.5 | crossbow@0:r 1, cast_flick@8:r 2, leap@7:r 1, leap@9:r 1 (total 68) | right 0 everywhere; LEFT x:hadd40:l 2 (fill 9), x:flex120:l 1 (fill 1) (total 64) |
| (1) w < 0.5 | = fill's own | all <= the fill's own (24 poses, all w <= 0.18; axe_back@0:r 5 vs fill 6) |
| (2) guard, least map / A's own, w > 0 | 0.61 axe_back@0:r | 0.54 warden_look@150:l (w 0.02), 0.74 iron_vow@72:l, 0.77 flex120:l: NOT MET |
| (3) T22 right 9 + the new right 5 | leap@7 / @9 FAIL, crossbow@0 / cast_flick turned | ALL MET: leap@7 -0.13, @9 +0.10, @19 0.00, @20 -0.01, crossbow@0 +0.01, @2 +0.02, cast_flick@8 -0.05 (own); crossbow@10 -0.02, cast_bolt@3 -0.05, axe_heavy -0.27, leap@5 -0.07, warden@126 -0.16, leap@25 -0.04, leap@6:r +0.06 (fill) |
| (3) T22 left | abd120 +0.21, iron_vow +0.56 FAIL | abd120 +0.61, abd150 +0.86, abd170 +0.85, flex170 +0.81, iron_vow@72 +0.37, leap@0:l +0.17 FAIL; cast_bolt@6:l +0.04, leap@30:l +0.09 ok |
| (4) FOLD max leap@5/6/7/9/12/14/16/17/18/19/20:r | 123/152/167/159/80/47/62/54/76/90/72 | 127/144/148/124/84/60/76/69/78/68/72 |
| (4) frame-to-frame FOLD jump (max over the 11) | 79.2 deg | 39.6 deg |
| (5) rest corner facing off A | l 0, r 0 | r 0, l 2 (tri 107, 291): NOT MET |
(4) NOT MET as written: @6 -8, @7 -19, @9 -35, @19 -22 deg, but @5 +3, @12 +5, @14 +13, @16 +14, @17 +15, @18 +2
(the bowl spreads into the late frames). (5)'s <= 45 deg proof and (6) not run: (1)-(4) fail. T22 split used here
(w = 1 own, w < 1 fill, as the lists are): own + crossbow_shoot@0:r, @2:r, cast_flick@8:r; fill + cast_bolt@6:l,
p4:heroic_leap@6:r, @0:l, @30:l. carried_target.py NOT edited (no promotion; the active lay would fail the new rows).
FINDING: on faired A the right's crease is gone and the `_l21b` recipe converges there (every right row at the bar,
the leap's worst jump halved). The left breaks: faired A's left poses (abd / flex / iron_vow) leave hi + boost unmet.
Next: lay the left alone with lay 6 `_a`'s recipe (judge, guard 0.8, guardwall 50, no boost) on faired A:
`build --only l --start strip_rest_l21c.npz --file strip_rest_l21d.npz`; then (4) on the right's late frames
(@14-@17: a FOLD cap or `fold` [0.3, 0.3]); the composite's left must also clear tri 107 / 291 at rest.
