# De-pinch A before carrying it (judge fix 1, Gate T round 2; lead 21's max solver, 10 Nov): CAUSE FOUND, ARAP FAIR BUILT, NOT MET, key absent

## The old attempt (first solver), in 6 lines
- `Her.depinched` seeded on valley folds over B's, filled a pocket ("frames" = B's rest differentials on A's smoothed rotations, or "membrane" = least area), and gave volume back as a bump.
- Membrane, rows 2, passes 3: the folds were cured on abd120-170 (named 11 / 3 / -1) but volume was lost: fold_front in95 21.9 (round 1 16.0), deltoid 35.0 (15.5), 62 mm moves.
- The bump re-crumpled the patch (bump 23-26 mm). Frames made new creases. iron_vow@72:l was never cured.
- Its finding stands: the front armpit (md 5770-5900, 8220-8360) is a CRUMPLE (valleys 140-179 next to ridges -100 to -170), not one pinched edge.

## Cause verdict: A's OWN posed skin, not the carry (`C:/Users/munch/Desktop/survivorsunchained_inputs/scratch_p1_depinch2/cause.py`)
| pose | A's own edges under the patch, abs fold > 45 / > 90, posed (rest) | A max fold posed / rest | binding: foot n . B n p50 / p5 | feet dist / B edge p50 | abs d0 max | sharp edges of the fill that the feet-only surface has |
|---|---|---|---|---|---|---|
| x:abd120:l | 58 / 15 (0 / 0) | 147 / 32 | 1.00 / 0.91 | 1.00 | 2.7 mm | 106 of 114 |
| p4:iron_vow@72:l | 101 / 29 (0 / 0) | 175 / 34 | 1.00 / 0.89 | 1.00 | 2.7 mm | 261 of 261 |
| x:abd150:l | 24 / 7 (0 / 0) | 159 / 29 | 1.00 / 0.88 | 1.00 | 2.7 mm | 82 of 96 |
- B's rest sits on A's to 2.7 mm. The feet are consistent at rest (0 inverted foot triangles, no jumps, carrier ok everywhere on the patch). A's LBS collapses its own triangles in the pose (8-9 foot triangles inverted posed, 0 at rest).
- So a better binding cannot cure it. The cure is an untangle of the carried surface. B's published part pose is crumpled there too (pub folds > 45: 102 abd120, 388 iron_vow).

## Built (tools/body/carried_target.py; inert: HER has no "depinch" key, `test` ALL PASS, today's target unchanged)
- `Pocket.fair(X, R, alpha, iters, keep)`: as-rigid-as-possible (Sorkine-Alexa local/global) from B's rest, with a data pull alpha toward X. keep = (area, normals): the area-weighted mean normal offset from X is held at 0 by a Lagrange step (measured offset 1e-15 mm).
- `Her.depinched(rg, G, cf, Vr, mw, info)`, now run AFTER `mapped` (the map's band is held when map w > 0; T21 is untouched). Seeds: an abs fold > fold_deg beyond B's rest fold, or a triangle turned against its smoothed rotation. Pocket = union over `passes` rounds, rows + k. The first guess is the carrier's rotations smoothed (frame_passes). Blend = smoothstep of the elevation over deg (<= lo returns early, bit for bit).
- Rule tried: `{"deg": [90, 105], "fold_deg": 20, "rows": 2, "passes": 3, "alpha": a, "iters": 20}` (scratch `meas.py` / `diag.py`, env DP).

## Sweep: composed patch counts (patch = 3 rows around list edges with abs fold > 45, rule off; same edges before -> after)
| alpha | abd120:l: >45 / >90 / flipped; named (5832,5833) (5773,5833) | iron_vow@72:l: >45 / >90 / flipped; named | move p95 / max mm |
|---|---|---|---|
| 0.1 | 125->93 / 40->23 / 62->36; -29->21, -17->18 | 307->253 / 99->62 / 110->104; -83->-65, -92->-65 | 8.8 / 11.6; 11.4 / 18.4 |
| 0.01 | 125->69 / 40->17 / 62->6; -29->57, -17->41 | 307->169 / 99->57 / 110->90; -83->-47, -92->-71 | 19.3 / 25.7; 25.7 / 33.9 |
| 0.001 | 125->64 / 40->17 / 62->6; -29->51, -17->39 | 307->152 / 99->52 / 110->68 | 25.5 / 34.9; 36.6 / 44.0 |
- B's rest has 30 edges over 45 inside the same patch (the floor). Flipped = against a 20-pass smoothed copy's normals.
- Cap top edges (iron_vow@72:l) stay 180 / 179 / 175.
- Of the edges still sharp at alpha 0.1, many sit on the held map band: abd120 26 of 91, iron_vow 98 of 228. That part is strip_rest's.
- The rest (65 / 130) are INSIDE the pocket. ARAP's local step refits its rotations to the crumple, so the folds stay as a local minimum. A lower alpha lets B's rest shape make new creases at the named edges (57 / 41).

## Acceptance
- (a) NOT MET (above).
- (b) and (c) not run: the rule is not live.
- (d) ALL PASS with the key absent. T24 is not written: no live rule to test.
- (e) The cap is not cured: 180 / 179 / 175.

## Next step (a solver)
1. Untangle first, then fair. Solve the pocket from a smooth start (the membrane, or Taubin-smoothed cf) with the rotations fixed from the smoothed carrier and not refitted. Then run a few ARAP iterations with alpha 0 at the seed points and alpha up to 0.1 on the outer rows, keep on.
2. Add a flip barrier (reject the step, or halve the pull, where a triangle turns).
3. iron_vow@72's crumple is half on the map's band: it needs strip_rest's lay on the band and this rule beside it, run together.
