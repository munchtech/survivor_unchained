# Armpit strip rest (B' = B with the band laid into A's groove): prototype, 10 Nov. NOT FINISHED

Tool: `tools/body/strip_rest.py` (`build | target | sheet`, `--snap` = frozen carried_target 3b61c755c in
out/shoulder/snap). Output: out/shoulder/strip_rest.npz (ids, loc, V0, V1, snap, bridge per side). Nothing wired.
NOT DONE (context ran out): the 141-pose run (`target --snap`, a few minutes, writes strip_target.json) and the
picture (`sheet --snap` -> sheets/strip_owner.png + _half.jpg; the code is written, never run, never looked at).

## Method (general core: lscm, Unfold, Curve, relay)
A's patch under the band unfolded flat (LSCM, 0 flipped); per bridge the apex = where A's normal is halfway
between the two mouths; a cubic through them (residual 0.3 mm); the bridge ends on the nearer side go ONTO the apex
line (an edge that straddles the apex keeps a short rest chord and tears like a bridge); the rest of the band by
least squares on the unfolded edge vectors (weights 1 / rest length); lifted back with heights from the band's
neighbours, cut until the foot is the closest A point. Band = rows 4 & beta == 1.

## Rest proof (l / r)
- 147 / 147 points moved, 9 / 10 on the apex line. Parts: trunk 33, shoulder 114; beta 1 everywhere, 7 rows or
  more from the region's edge; nearest breast-part point 58 mm (l). None under a border row or the breast part.
- Move p50 / p95 / max: 2.1 / 9.7 / 11.9 mm (l), 2.2 / 8.6 / 10.6 mm (r).
- A's rest path / B's 1.15 (l), 1.10 med 1.23 max (r) -> A's / B' 0.99 (l), 0.96 (r). Path / chord of a band edge:
  max 4.25 / 6.73 -> 1.19 / 1.18 (none over 1.2: no edge bridges skin any more).
- B' carrier: feet within 0.2 mm of the laid feet, |d0| p95 1.2 mm. The 60 deg normal rule still names 1 / 10
  edges on B' (it reads normals, not skin), so B' is carried ALONE (pocket_rows 0).
- THE STRIP IS NOT HIDDEN AT REST. A's rest fold is not closed: a groove 8-13 mm deep, 8-9 mm wide at the mouth,
  in an open bind-pose armpit. Rays (2000 directions): 147 of 147 moved points reached before AND after.
  Outline: front 3/4 2 px (0.5 mm), back 3/4 and side 0. Surface seen: about 5 cm2 from the front 3/4, 6.5 cm2
  from the back 3/4, 6 cm2 from under the arm changes depth by over 0.5 mm (a crease where B is smooth); side 0.
- Defects of the lay itself: rest edges new / old 0.49..1.80 (l), 0.34..1.41 (r); 2 rest triangles turned over (l).

## Fill | B' (band edges against each one's own rest; 9 named poses)
| pose | fill edge, off A mm, turned | B' edge, off A mm, turned |
|---|---|---|
| x:abd120:l | 0.69..2.41, 9.3, 0 | 0.67..3.00, 1.4, 2 |
| x:abd150:l | 0.43..2.69, 25.5, 0 | 0.55..3.80, 1.4, 1 |
| x:abd170:l | 0.39..2.83, 31.2, 2 | 0.56..3.71, 1.4, 1 |
| x:flex170:l | 0.25..2.75, 33.6, 3 | 0.58..3.73, 1.4, 1 |
| p4:iron_vow@72:l | 0.22..2.33, 20.6, 12 | 0.19..2.26, 1.4, 3 |
| p4:heroic_leap@7:r | 0.33..3.17, 16.9, 12 | 0.43..2.68, 1.3, 1 |
| p4:heroic_leap@9:r | 0.27..3.60, 17.7, 21 | 0.39..3.26, 1.3, 4 |
| p4:heroic_leap@19:r | 0.56..3.32, 33.5, 2 | 0.60..4.50, 1.3, 0 |
| p4:heroic_leap@20:r | 0.51..3.33, 33.5, 12 | 0.57..4.41, 1.3, 0 |
Pass 2.5x: fill 2 of 9, B' 1 of 9. Pass 3x: fill 5, B' 3.

## Reading, and what not to re-derive
- B' puts the band ON A's hollow (33 mm -> 1.4 mm) with fewer turned triangles, but its worst edge is WORSE on the
  left (3.7-3.8 against 2.7-2.8) and at leap 19/20 (4.5). Not looked into: which edges (the short 0.34-0.49 rest
  edges are the first suspects, then A's own 2.8-3.6 single edges). Until that is known this is not a yes.
- The premise "hidden at rest" is false in the bind pose; whether it shows in play is a game-frame question.
- An apex row is needed (straddling edge = path / chord 2-4). Skin alone (1.15) was never the whole budget.
