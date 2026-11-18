# Ride travel: her shoulder skin against a rigid plate's ride (10 Nov, helper for P1 lead 19)

Tool: `tools/body/ride_travel.py` (new; imports `carried_target`, `region_shape`, `region_target`, `deform_audit` as they are, nothing from the gear worktree).

    python tools/body/ride_travel.py                      # the whole table, about 4 minutes; also tools/body/out/ride_travel/table.json
    python tools/body/ride_travel.py --surfaces old pub   # seconds
    python tools/body/ride_travel.py --sides l --clips sword_heavy cast_flick

Rerun the first line after the target changes: NEW is composed live per frame, nothing stored is read.

## The answer

**No. The NEW target is not under 5 mm against any single rigid ride, and not against the rigid floor either.** Over the four clips (91 frames), measured from rest, on the skin under the cop's box:

- best single ride for NEW (a turn about the joint, a quarter of the way from the clavicle to the upper arm): travel max 49 mm left / 43 mm right, sink 46 / 36 mm.
- the FLOOR (per-frame least-squares rigid fit of the patch, what no rigid plate can remove): travel p95 / max OLD 25 / 30 left, 25 / 28 right; **NEW 26 / 41 left, 25 / 36 right**; A 27 / 40 left, 25 / 35 right.
- NEW equals A within 1 to 3 mm in every row (the target does bring A across), and **NEW moves MORE against a rigid ride than today's bare linear blend** (clavicle ride, left, travel max: OLD 45, NEW 66, A 63).
- Where it sits (floor, NEW, left, travel p95 / max by zone): armpit front 37 / 41, back 27 / 30, deltoid cap top 23 / 27, trap / neck end 16 / 16. Right: front 32 / 36, back 25 / 29, cap top 24 / 26, neck end 20 / 22. The worst frame is daggers_heavy frame 0 on both sides.

A rigid cop over this whole box cannot sit within 5 mm on OLD, NEW or A: the box spans the joint (its neck end rides the clavicle, its arm end the upper arm), and the clips hold her arm far from the rest pose.

## Did OLD reproduce the gear lead's 8-16 mm? No

Not within a millimetre or two. In the gear builder's own form (`sink_nn`: the carried point's height over the nearest moving skin vertex, less the same at rest) OLD reads, over the four clips: floor 19 left / 23 right, sphere 0.25 20 / 21, clavicle 28 / 31, upperarm_share 37 (left). Per clip against the clavicle, left / right: daggers_heavy 24 / 22, run_reaver 7 / 16, sword_heavy 28 / 18, cast_flick 5 / 31. Same order of size as 8-16, up to twice it. Not explained: my points are the SKIN under the cop's whole box, theirs the cop's inner-face grid (a standoff off the skin, the cop's arched outline, the tuck); their mean ride is a blend of bones, not rigid; I did not run their code. Read the table as "comparable in kind, not point for point".

## Table (mm). Cells: travel p50 / p95 / max, s = sink max, n = sink_nn max. ALL = the four clips, 91 frames

Side l (patch 249 vertices):

| ride | OLD bare blend | PUB (with shapes) | NEW target | A |
|---|---|---|---|---|
| upperarm | 57/113/129 s113 n64 | 62/113/129 s112 n65 | 59/112/129 s109 n79 | 60/111/128 s109 n73 |
| clavicle | 12/35/45 s38 n28 | 16/65/71 s57 n38 | 16/51/66 s62 n42 | 14/51/63 s57 n40 |
| sphere 0.25 | 17/31/35 s24 n20 | 32/57/59 s47 n28 | 25/40/49 s46 n33 | 26/40/46 s41 n32 |
| FLOOR fit | 11/25/30 s26 n19 | 22/32/40 s38 n33 | 12/26/41 s33 n24 | 12/27/40 s31 n24 |

Side r (patch 244 vertices):

| ride | OLD bare blend | PUB (with shapes) | NEW target | A |
|---|---|---|---|---|
| upperarm | 85/113/141 s107 n60 | 86/115/141 s106 n59 | 80/113/142 s100 n60 | 80/112/140 s97 n58 |
| clavicle | 12/44/48 s37 n31 | 15/64/68 s56 n31 | 17/50/59 s47 n32 | 14/49/57 s51 n32 |
| sphere 0.25 | 26/33/39 s25 n21 | 32/57/58 s46 n23 | 27/38/43 s36 n31 | 25/38/42 s36 n30 |
| FLOOR fit | 16/25/28 s26 n23 | 22/31/39 s33 n28 | 13/25/36 s34 n24 | 12/25/35 s30 n24 |

Per clip and the two single frames: travel max, n = sink_nn max, as OLD | NEW | A.

| side, frames | upperarm | clavicle | FLOOR fit |
|---|---|---|---|
| l daggers_heavy | 129 n35 / 129 n40 / 128 n36 | 45 n24 / 66 n26 / 63 n21 | 30 n19 / 41 n24 / 40 n24 |
| l run_reaver | 76 n25 / 78 n24 / 78 n25 | 17 n7 / 32 n7 / 32 n7 | 11 n4 / 23 n6 / 23 n6 |
| l sword_heavy | 85 n64 / 87 n79 / 85 n73 | 29 n28 / 50 n42 / 46 n40 | 19 n16 / 22 n20 / 24 n20 |
| l cast_flick | 66 n17 / 66 n13 / 66 n13 | 11 n5 / 18 n7 / 18 n8 | 8 n3 / 13 n6 / 13 n6 |
| l sword_heavy@13 | 83 n63 / 84 n76 / 81 n70 | 29 n26 / 49 n41 / 46 n39 | 18 n15 / 22 n20 / 22 n20 |
| l cast_flick@6 | 45 n8 / 45 n4 / 45 n4 | 5 n2 / 18 n2 / 18 n2 | 4 n1 / 11 n3 / 11 n4 |
| r daggers_heavy | 128 n35 / 128 n38 / 127 n36 | 41 n22 / 59 n24 / 56 n21 | 28 n19 / 36 n17 / 35 n17 |
| r run_reaver | 106 n60 / 95 n60 / 94 n58 | 44 n16 / 39 n13 / 39 n13 | 25 n15 / 27 n14 / 27 n14 |
| r sword_heavy | 141 n54 / 142 n51 / 140 n54 | 48 n18 / 47 n19 / 47 n17 | 28 n19 / 29 n15 / 30 n16 |
| r cast_flick | 115 n47 / 113 n45 / 113 n44 | 44 n31 / 57 n32 / 57 n32 | 28 n23 / 30 n24 / 30 n24 |
| r sword_heavy@13 | 112 n26 / 112 n23 / 112 n24 | 12 n1 / 32 n5 / 32 n5 | 10 n1 / 20 n9 / 20 n10 |
| r cast_flick@6 | 114 n47 / 112 n45 / 112 n44 | 39 n31 / 57 n32 / 57 n32 | 23 n23 / 30 n24 / 30 n24 |

Every other row (upperarm_share, delt, scap, sphere 0.5 and 0.75, PUB per clip, p50 / p95 per clip) is in the tool's printout and `tools/body/out/ride_travel/table.json` (git-ignored; the last run's printout is `tools/body/out/ride_travel_run.txt`).

## Definitions

- **Surfaces**, all on B's own clip kinematics (`B.clip_frames(da.load_clip(c), 1)`: 21 + 20 + 31 + 19 = 91 frames): OLD = `B.p._skin(G, {})`, today's weights with no corrective shapes. PUB = `rt.published(B, G)`; it differs from OLD by tens of mm on this patch (the shapes are large there), so both are printed. NEW = `Her.target(G, "l", Vp)` then `Her.compose(G, Vp)`, `carried_target.cmd_target`'s own order: the whole composed surface, both shoulders in one call (checked at sword_heavy@13: equal to `Her.target`'s points on both sides to 1e-12 mm, and the same after a left or a right call). **NEW is the TARGET the fit will aim at; no new weights exist, so a fitted skin can only be equal or worse.** A = her old body posed by B's bone turns (`Ctx.a_from_B`), read at the points of A's rest surface nearest B's patch vertices (0.1-0.2 mm p50, 1.2 mm max apart at rest), against A's own upper arm and clavicle bones.
- **Patch**: B's skin vertices under the cop's box of `plate_spaulders_plain/build.json` (s -88..+36 mm along upperarm -> lowerarm, theta 21..172, rho < 90 mm) on the gear builder's shoulder frame. Frame, crest line, crest drop and footprint are copied into the tool from gear-p2 `tools/armor/native_build.py` and `native_spaulder.py` (named in the tool's head).
- **Rides**: a bone = `G_f[bone] inv(G_rest[bone])`. Sphere t = a turn about the shoulder joint, t of the way from the clavicle's turn to the upper arm's (my definition, the gear builder's sphere was not read; sphere 0.5 lands on `upperarm_share` to 0.1 mm, which checks both). FLOOR = Kabsch fit of the patch from rest per frame, vertex-area weights: a least-squares floor (a floor on the RMS, not strictly on the max).
- **travel** = per patch point the largest `|p_f - M_f x0|` over the frames, then p50 / p95 / max over the patch. **sink** = the largest `(p_f - M_f x0) . n_f` (posed mesh normal; + = the skin comes up through the plate). **sink_nn** = `native_travel.on_skin`'s form on the patch's own points.
- **Reference = the REST pose** (as the gear builder's sink is). The clips never pass through rest: every number carries the arm's drop from rest to her stance. A plate fitted at rest is what was asked.

## Not measured, not verified

- The gear lead's own numbers were not rerun; OLD does not reproduce 8-16 mm (above). Whether gear-p2's `body.glb` is the same B as body-p1b's `da.body("B")` was not checked.
- The gear builder's `mean_ride` (a blend, not rigid) and its sphere; the cop's arched outline, its inner-face grid and the tuck.
- Travel from a stance pose instead of rest (a plate seated at her idle would read lower; the tool takes any rest only through `Track`, HER's reference is rest).
- A smaller plate: the floor over a part of the box (the cap top alone, or the neck end alone) was not fitted separately; the zone rows are zones of the whole-box fit.
- A on its own clip kinematics (`rt.a_frames`); only B's turns were used.
- No picture, no render; numbers only.

## Stance-referenced, cap top (lead 20's worker)

New options of `tools/body/ride_travel.py`: `--ref rest|first` (first = each clip's first frame is the reference for every displacement and fit) and `--patch box|cap_top|neck_end` (floor fitted on that zone's points, travel reported on it). Floor = best rigid motion of the patch per frame; cells are travel p50 / p95 / max mm over all 91 frames (each point's largest). Runs: (a) `--ref first --patch cap_top` (cap_top 60-130 deg, s >= -45 mm), (b) `--ref first --patch box`. Outputs: `tools/body/out/ride_travel/first_cap_top.json`, `first_box.json`. The 5 mm line is met by none.

Side l:

| surface | (a) cap top, floor p50 / p95 / max | (a) worst | (b) box, floor p50 / p95 / max | (b) worst |
|---|---|---|---|---|
| OLD | 9.5 / 14.6 / 17.7 | daggers_heavy @ 9 | 11.9 / 25.2 / 31.2 | daggers_heavy @ 10 |
| pub | 15.7 / 25.1 / 27.7 | daggers_heavy @ 12 | 18.9 / 29.3 / 40.9 | daggers_heavy @ 12 |
| NEW | 11.8 / 21.0 / 23.5 | daggers_heavy @ 9 | 14.9 / 28.5 / 42.4 | daggers_heavy @ 12 |

Side r:

| surface | (a) cap top, floor p50 / p95 / max | (a) worst | (b) box, floor p50 / p95 / max | (b) worst |
|---|---|---|---|---|
| OLD | 13.6 / 20.8 / 23.4 | cast_flick @ 6 | 18.1 / 25.2 / 31.6 | cast_flick @ 6 |
| pub | 16.8 / 29.6 / 31.6 | cast_flick @ 9 | 21.5 / 32.7 / 40.3 | cast_flick @ 6 |
| NEW | 10.9 / 19.4 / 21.7 | daggers_heavy @ 9 | 15.4 / 25.8 / 37.1 | daggers_heavy @ 11 |

Today's defaults reproduced: yes (rows and zones of a default run equal the previous table.json exactly).
