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
- **Trunk back: B does not move there (weight 0), A does**: A's back skin follows its arm 28-49 mm at 150-180 deg, and that motion reaches 31 rows past the list (why no row count cured it).
- **Trap line and breast edge are both the BREAST PART's top rows.** Outside the list B's surface moves only the arm and the breast part's first 8 rows (clavicle weight; Jog_Fwd@11:r row 1 mean 36 / max 99 mm, row 6 10 / 52, row 8 1 / 11). A moves the WHOLE breast part with a high arm (abd170 rows 10-12: A 25 / 33 mm, published 0; row 20: 11 / 16).
Motion support of one girdle (points either surface moves over eps; the explicit list is 3764 a side):
| eps mm | B published | A carried | breast part (586 points, 24 rows) | trunk past the list (rows out) | across the midline (rows) |
|---|---|---|---|---|---|
| 0.5 | 6983 | 8558 | A 586, B 187 | 508 (32) | 284 (31) |
| 1.0 | 6871 | 8286 | A 586, B 164 | 434 (31) | 164 (24) |
| 2.0 | 6737 | 7966 | A 586, B 141 | 335 (29) | 54 (21) |
Both also move the arm and hand past the list (3804 points): left out (below). 339 list points move under 0.5 mm.

## The design: `support_region(adj, moved, core, stiff, gated, rows, ring, gate_rows, wall_rows)` (no names, any set)
- **Support** `moved`: points B's published OR A's carried surface moves over eps 1.0 mm under the girdle's part poses. The pose set itself (each pose on its side, mirrored), not probe turns: the driver's elevation law is not linear (lat and pec act only at high arms). 85 s for 141 poses: cache it.
- **Region** = (moved | the list as core) grown 4 rows; share 0 on the outer row, 1 from 4 rows in. The ramp lies in rows nothing moves: outer row = published by construction, the ramp hides under eps.
- **Far border** `stiff`: points rigid (>= 0.999) to the upper arm's subtree outside the list (first row past the list: min weight 1.0000). Nothing grows into them; share 0 within `ring` 3 rows, rising over 4 = today's beta (measured: equal).
- **Breast rule** `gated` = the breast part, both sides: a WALL, share 0, the share rising over `wall_rows` 12 away from it. Gate shut: the whole part is published. Gate open: the wall stands back `gate_rows` 8 rows from the list (so only upper and lateral rows): the blend rows. Share(G) = (1 - g) closed + g opened, g = s01((elevation - lo) / (hi - lo)), the arm's elevation in spine_05's frame (as `region_target.describe`): this is `Model.blend`.
- **Jog's keyed clavicle does not open the gate**: T16 binds it (Jog_Fwd@11:r: elevation 43, clavicle 40 deg, the only pose with clavicle > 20 under 45), and opening would cut the breast's top rows from 99 to 37 mm of motion in a jog.

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
1. `Her.__init__`, explicit provider: cache the max motion per md point (`out/shoulder/support.npz`, keyed by the pose names); `support_region(md.adj, moved, list mask, stiff, md.part == breast)`; region points = the list first, then the new ids; carrier = the list's (pocket) + a plain Carrier on the new ids; edges over all.
2. `Model.blend(G, side, grown=False)` = (1 - g) closed + g opened (False: the list's 3764, so region_shape runs as is). `Her.carried(.., full=False)` likewise; `Her.target` returns X on the list and keeps the grown rows; `cmd_target` adds `ext_l`, `ext_r` (md ids) and `Xe`; `region_shape.surface("carried")` must write `Xe` too or sheets crack at the list's border; `edges` needs the grown edges to class the new ramp.
3. T11 with the old share (beta, list only) for the identity-turn experiment; T15-T17 as briefed.
Full run after that, unchanged commands: `python tools/body/carried_target.py target`, `python tools/body/region_shape.py edges --provider carried`.

## Needs a decision
- **Gate range.** Idle / run / jog poses reach 65 deg (idle_warden_town@126:r 65, run_warden@13:l 60, Jog_Fwd@14:l 54, six idles 48-55). "Idle and walk within 1 mm" needs lo >= 65; T16 alone allows 45. 65-95 costs cast_bolt and Jog@14 (table).
- **Jog_Fwd@11:r is not cured at wall rows 12** (5 edges, 3.05): B's clavicle weight on the breast's top rows, which the rule keeps published in a jog. Wall 16 cures it and costs the abd poses 0.9x; or leave it "published" until the weight fit.
- eps: 0.5 mm adds about 194 points a side (120 across the midline), 2.0 removes about 209.

## Wired (lead 18's helper, then a solver): tests ALL PASS, dev run written; `region_shape.py` NOT wired
**Wired:** `region_target.Model.blend(G, side, grown=False)` + `Model.elevation`; `carried_target`: `Carriers`, HER `regions.girdle_{s}.support`, `Her.motion` (cache `out/shoulder/support.npz`), `Her.grow` (list first, then new ids; `h.ext[s]`, `rg.nlist`, `rg.gated`, `rg.gate_own`), `Her.carried(.., full=False)`, `Her.target`, `Her.shut`, `cmd_target`, T11, T15-T17. Region: 5340 points a side (3764 + 1576), share 1 on 3072 shut / 3431 open; the girdles touch each other across the midline.
**Interface (unchanged):** `Her.target(G, side)` returns X on the side's list (3764, same order); grown rows in `h.last["Xe"]`, per-pose share in `h.last["share"]` (list, then grown); the npz carries `ext_l`, `ext_r` (md ids), `Xe`. **Changed:** info `gated_d_max` is now `Her.shut`'s first number (below), new info `gated_oth_max`; `cmd_target` prints a gate-shut line for EACH shut side of a pose (dev run; the full run prints only a side over 1 mm) and a summary line with the max and the seconds a pose.
**Causes of the three failures (one line each):**
- **T13: code was wrong, the builder's fix holds.** The support cache was read in the first LISTED side's indexing; with `min(cfg["sides"])` both poses are True bit for bit.
- **T11: the test read the wrong file.** `target_a.npz` was rewritten at 01:07 by the full run WITH the neck, so "girdles alone" differed from it by the neck's delta (6-60 mm; 0 on one-arm poses, neck at rest). A `Her` without `support`, every region composed, equals that file TO THE BIT (0.00e+00 on all 7 poses): the no-support path is the pre-wiring path. T11 now reads frozen copies (config `t11_stored`): `target_a_regions.npz` (that composed target, limit 1e-9) and `target_a_rel.npz` (the relative target of before the regions).
- **T11 experiment CONFIRMED:** girdles alone - `target_a_rel.npz` is 2.5-6.7 um with the region's 4 reference bones and 0.00e+00 with the 13 that file was posed with (identity turns on the other 9 are not exact). Limit 1e-5, cause in the comment; the 13-bone identity is asserted at 1e-9 on the same line.
- **T16: the test's measure was wrong; no girdle fault.** The 57.7 mm is the NECK on rows it owns: the part map's "breast" (586 points a side) runs up to the collar, 452 of its 1172 points carry neck_01 weight over 0.02 (max 0.908), 458 have neck share 1. neck_01 turned (idle 28.7 deg, iron_vow@75 27.9): the neck moves 233 points of one breast part over 1 mm (max 57.7); neck_01 at rest (Jog, cast_bolt, crossbow): 0.008 mm. The girdles on the shut left breast in that pose: own 0.000, the other 0.002 mm. T16 is now per side on the composed target: `Her.shut(G, side)` = (how far the regions under the gate, BOTH girdles, move the side's whole gated part, 586 points, in a region or not; how far the other regions move it), for each side under 45 deg whatever the other arm does; limit 1 mm on the first, the second printed.
- **The other girdle does reach a shut breast, under the limit:** 21 of a breast's points lie in the other girdle's region, 14 with open share > 0 (max 0.156). Over all 141 stored poses (69 (pose, side) shut with the other arm open): max 0.139 mm (x:abd170:l side r). Not changed.
**Jog rows: the composed target is right, the wiring reproduces the prototype.** Ramp edges over 2.5x / unexplained, worst:
| pose | composed (whole pose) | girdle alone (whole pose) | girdle alone, its part pose | prototype (part pose) |
|---|---|---|---|---|
| Jog_Fwd@14:l (54) | 28 / 0, 7.91 | 31 / 0, 7.91 | 8 / 0, 2.73 | 9 / 0, 4.00 |
| Jog_Fwd@11:r (43) | 40 / 5, 9.23 (3.05) | 43 / 5, 9.23 (3.05) | 24 / 5, 3.60 | 27 / 5, 4.04 (3.05) |
The prototype judged the girdle's PART pose; T17 judges the whole pose. The extra edges (20 and 16) are the PUBLISHED surface's own stretch in the whole pose (2.65-7.91x and 3.01-9.23x; every one "explained"), in ramp rows (own share at most 0.53 / 0.84) of the trunk and breast parts, 24 / 16 with an end in the grown rows. None is in the neck region or its ramp (published under the neck's part pose alone: 1.00 there), 3 end in the other girdle; the neck cures 3 (31 -> 28, 43 -> 40). Owner: no region (bones outside every region, the trunk in the jog); WHICH bone was not measured. Other poses, composed: abd170 0 / 0 1.70, abd150 1.60, flex170 1.60, iron_vow@72 2.09, cast_bolt 1.94, heroic_leap 0 / 0 2.18, idle 1.58, add0 1.24.
**Final tests (`out/shoulder/border_scratch/test_solver2.txt`, 79 s): ALL PASS, 48 lines.** T1-T10 (20), T11 x 7 (0.00e+00 | 2.5-6.7 um | 0.00e+00), T12, T13 x 2 True, T14 iron_vow@75:r 2.10 (published 11.68, A's own 1.63) and idle 1.58, T15 l / r (outer row 312, share 0, 0.0e+00), T16 x 9 (pose, side) max 0.139 mm (idle side l 0.0017, the neck's rows 57.7), T17 x 5.
**Cost:** `Her.part` keeps the last pose's parts (0.25 s a region), so both sides' targets, the touching regions, `shut` and `compose` of one pose compute each part once. Dev run: 9 poses in 8 s (0.89 s a pose): the full 141 poses about 2.5 min (was 8). Dev npz (`target_a_dev.npz`, overwritten, 9 poses): X (9, 3764, 3), Xe (9, 1576, 3), ext_l / ext_r 1576.
**Needs the lead's decision (not made):** the neck owns the upper rows of the part map's breast. Keep (as wired: the gate rules the girdles only), or wall the neck at the part: published then returns on the collar rows whenever neck_01 turns (the breast part inside the neck region, 652 points: worst edge published 1.71 / 1.80 against composed 1.34 / 1.28 in idle / iron_vow@75; up to 57.7 mm of the neck's cure dropped, T14's rows next to it).
**NOT done:** `region_shape.py` (`surface("carried")` does not write `Xe`; `edges` does not know the grown edges or the per-pose share); the full 141-pose run; the bone behind the Jog's published stretch. `target_a_regions.npz` and `target_a_rel.npz` (git-ignored `out/`) are T11's references: keep them (a full run rewrites only `target_a.npz`; without them T11 fails as "missing").
**Commands:** `python tools/body/carried_target.py test`; dev: `python tools/body/carried_target.py target --poses "x:abd150:l,x:add0:l,cast_bolt@0:l,crossbow_shoot@0:r,Jog_Fwd@14:l,Jog_Fwd@11:r,p4:idle_warden_town@122:l,p4:iron_vow@75:r,x:abd170:l"`; full: `python tools/body/carried_target.py target` (read its last "gate shut" line); `python tools/body/region_shape.py edges --provider carried` and `sheets` only after region_shape is wired.

## region_shape wired (lead 18's builder; dev poses only, the full edges run and the sheets are the lead's)
**Reads the grown rows:** `Ctx._stored` (X, `Xe`, `ext_<side>` of the stored target; `--target FILE`, default `target_a.npz`; a file without them = a region that did not grow), `Ctx.region(s, kind)` / `Ctx.rows` (the list, then the grown rows: ONE map), `Ctx.surface("carried")` writes X then Xe through it; `regtri` (silhouette "reg"), sheets, shift and `strip_rest sheet` read through `surface`, no second copy. One side is written a pose, so no point is written twice; a grown row that is a point of the other side's region holds the COMPOSED value (`Her.target` stores published + own delta under the pose's share + the touching regions' deltas whole, the other girdle and the neck included).
**edges:** the grown region's edges (`rg.edges`, 14766 old + 6162 new, both sides), the live rows with `carried(full=True)` and `rg.share_at(G)`; classes by the ends' share AT THE WORST POSE (json `beta` is now that share); zone of an old edge as before, of a new edge its grown end (`grown [across] <part> top / front / back`); json adds `set` per edge, `totals_old`, `totals_new`, `edges_old`, `edges_new`, `no_crack` {pose: [list-to-grown worst ratio, outer row off published mm]}, `target`; `totals` = both. The file's `ext_*` must equal `h.ext` (else exit: stale file). With `--poses` it writes `edges_carried_dev.json` (never over the full run's file). Stored against live: 0.000 mm.
**No crack (234 list-to-grown edges a side, outer row 312 points):** x:abd150:l worst 1.43, outer row off published 1.1e-06 mm; x:abd170:l 1.59, 1.1e-06 mm; add0 1.01; cast_bolt@0:l 1.68; idle@122:l 1.35; Jog_Fwd@11:r 2.48. (The prototype's 1.60 / 1.70 were over all ramp edges, not this seam only: not compared.)
**Dev edge counts over 2.5x (6 poses), old | new:** pocket 17 | 0, published 0 | 36, A's own 8 | 0, border blend 5 | 0, bridge 0 | 3, carrier 24 | 13 (old 54, new 52; every new one and every old published-led / blend one is Jog_Fwd@11:r).
**NOT done / limits:** (1) the outer row is published only where no OTHER region reaches it: off published 6.6 mm cast_bolt@0:l, 18.0 mm Jog_Fwd@11:r, 57.0 mm idle@122:l (the neck's and the other girdle's deltas, stored on this side's rows but not written outside them): `surface("carried")` writes ONE side's region, so a sheet of a pose with neck_01 turned or the other arm up steps there; the cure is the whole composed surface (`Her.compose`) stored or computed live, not built. (2) `pops` still merges the two sides by overwrite. (3) No picture was opened; the full 141-pose edges run was not run. (4) bands (shift) stay on the list's points.
**Commands:** `python tools/body/region_shape.py edges --provider carried` (full, ~3 min; read the OLD set / NEW edges lines); `python tools/body/region_shape.py sheets --provider carried --poses x:abd150:l,cast_bolt@0:l,x:add0:l,run_warden@13:l --views front34,back34,under`; dev: add `--poses "x:abd150:l,x:add0:l,cast_bolt@0:l,Jog_Fwd@11:r,p4:idle_warden_town@122:l,x:abd170:l"` to edges.

## Whole composed surface (lead 18's builder 2; dev poses only; the neck edge set is NOT built)
**Stored:** `cmd_target` adds, per pose, `Her.compose` on the union of every region's points: `ids_c` (md ids, sorted, 10139) + `Xc` (poses, 10139, 3), and `raw_c` + `Xr` (1115 source vertices of the neck region the model has NO point for: the neck is derived on the whole 57603-vertex source mesh, md covers its first 40328; md ids alone cannot hold the union). X, `Xe`, `ext_*` unchanged: equal to the bit on the 7 dev poses (`target_a_dev_before.npz`). Dev run 7 poses in 9 s.
**Read:** `Ctx.surface("carried")` writes `Xc` through `md.src`, then `Xr`, when the file has them (prints which path once; a file without `Xc` behaves as before); `region` / `rows` / `_carried` unchanged.
**Outer row (844 body edges with one end in `ids_c`, one outside; surface against published / max |surface - `Her.compose`| on every vertex):** Jog_Fwd@11:r 1.000000 / 0.0e+00 (the union moves up to 55.6 mm inside): the step is gone where the sheet's pose IS the stored pose.
**FOUND, not fixed (outside my files' scope: `Ctx.poses`):** for cast_bolt@0:l and p4:idle_warden_town@122:l `Ctx.poses` gives ANOTHER pose than `poses.npz` (82 bones differ, matrix entries up to 0.117 / 0.124; Jog_Fwd@11:r 0): the sheet lays the stored target over the published surface of a different pose, so those two still step (crossing edges 4.97 / 5.43 against published, surface off live compose 22 / 21 mm). Likely the clip poses' `:l` handling (x: poses are mirrored in `Ctx.poses`, clip poses are not). Every sheet of such a pose is wrong whatever is stored; cure: `Ctx.poses` reads G from `poses.npz` when the name is there.
**NOT done:** the `neck` edge set in `edges` (no code); `carried_target.py test`, `edges` old / new recount, `sheets` and `strip_rest sheet` were NOT rerun after the change (context budget); the full 141-pose target (file grows by about 35 MB).
**Commands:** `python tools/body/carried_target.py target --poses <dev>`; `python tools/body/region_shape.py sheets --provider carried --target target_a_dev.npz --poses Jog_Fwd@11:r --views front34`.
