# The girdle-relative carry (10 Nov, solver for P1 leads 16 / 17)

`python tools/body/carried_target.py test | target [--carry absolute]` (default relative; absolute writes `target_a_absolute.npz`).
Old outputs kept: `out/shoulder/target_a_abs.npz`, `edges_carried_abs.json`. New: `target_a.npz`, `edges_carried.json`, logs `target_a_rel.log`, `edges_rel.log`.

**Verdict: the border fault is cured where the cause was the trunk and neck (border blend 460 -> 105 edges), but the target now
takes B's published neck skinning inside the region, and that skinning is broken: the worst edge went 9.10x -> 11.76x. Not a pass
as it stands; the choice it leaves is the lead's (last section).**

## The experiment (cause confirmed, with one exception)
Border rows (share < 1), max |carried - published| mm: (i) the pose | (ii) only the girdle's locals kept | (iii) girdle reset.
| pose | all border rows | trunk back | trap line | breast edge |
|---|---|---|---|---|
| Jog_Fwd@11:r (clavicle keyed 39.7 deg) | 76.1 / 76.1 / 62.8 | 62.8 / 5.2 / 62.8 | 76.1 / 76.1 / 31.2 | 70.9 / 70.9 / 36.6 |
| p4:idle_warden_town@122:l (neck_01 28 deg) | 60.4 / 8.8 / 60.4 | 47.3 / 2.9 / 47.3 | 60.1 / 6.6 / 60.1 | 60.4 / 8.8 / 60.4 |
| p4:iron_vow@75:r | 61.1 / 29.9 / 61.1 | 61.1 / 8.7 / 61.1 | 49.6 / 14.8 / 49.7 | 42.2 / 29.9 / 42.5 |
Trunk back, trunk front, midline, neck top: millimetres with the girdle alone, the centimetres ride the trunk and neck (A's 3 spine
bones for B's 5, other weights, one rigid anchor). Exception: with the clavicle keyed 40 deg the girdle ALONE keeps 71-76 mm at the
trap line and breast edge: B's ring rows there are weighted 0.97 to the clavicle (published moves 95 mm, A's surface 19 mm).

## The method as built
Girdle pose Gg = rest + the LOCAL transforms of clavicle, upperarm, lowerarm, hand of the side from G, driven by B's driver (bd.rig).
c = A posed by Gg's turns, carried, pocket filled, in the rest trunk frame. Per point `X = published(G) + M (c - published(Gg))`,
`M = L(G) L(Gg)^-1` (3x3 of the blended skin matrix; same J, W, inverse binds as `published`). This is the brief's
`L(G) L(Gg)^-1 c` plus B's correctives that other bones drive; that term measured 0.000 mm (T9, T10 poses), so the two are one.
- Guard: under sigma 0.35 of L(Gg) the blend of per-bone relative turns takes over. 141 poses: sigma min 0.485, guarded points 0.
- The driver is not idempotent: it wants driven bones at rest local. Main bones = all but helpers of kind != "unroll" and scap.
  So rebuilt, it gives back a stored pose but for trap (clavicle_roll_keep) and keyed helpers of dump clips (up to 0.275 in matrix
  entries, idle_reaver_look@27:l). That offset is put on the same bone in Gg (`girdle_pose`), so a trunk-at-rest pose is its Gg.
- `carried()` still returns (filled, alone, A's vertices); A's are the girdle-only pose moved rigidly with the anchor.

## Tests
T1-T7 green, unchanged. T9 (spine_02 20, spine_03 25, spine_05 30, neck_01 30, neck_02 25, Head 20 deg, girdle locals at rest):
X - published max 0.0065 mm l, 0.0051 mm r (absolute carry: 66.7 / 78.3 mm). T10: whole-body rigid motion 1.8e-15 m, twice the
same bit for bit. Dev poses absolute | relative: equal (arm-only poses), crossbow_shoot@0:r edge max 2.57 | 2.59.

## Edges over 2.5x, 141 poses: before | after (730 | 476)
| class | before | after | where the change is |
|---|---|---|---|
| border blend | 460 | 105 | trunk back 183 -> 42, trap line 113 -> 21, trunk front 50 -> 0, neck top 47 -> 0, midline 19 -> 0, trunk top 3 -> 0, breast edge 45 -> 42 |
| published | 104 | 104 | unchanged (throat pit 27 at 9.10, breast edge 57, trap 13, midline back 6) |
| A's own | 84 | 91 | deltoid cap 47 -> 50, back fold 16 -> 18 |
| carrier | 43 | 129 | **trap line 11 -> 78 (6.21 -> 11.76)**, inner back 0 -> 6, trunk back 12 -> 21, midline top 7.31 -> 8.53, trunk top 4.32 -> 7.86 |
| pocket | 36 | 36 | back fold worst 3.60 -> 3.73, inner 2.76 and 3.33 unchanged |
| bridge | 3 | 11 | trap line 0 -> 8 (6.71) |
Per pose: target edge max p50 2.89 -> 2.85, max 9.10 -> 11.76; poses over 2.5x 88 -> 84. Carried surface before the blend: max 3.72 ->
11.85, poses over 2.5x 39 -> 67.

## What the new "carrier" edges are (the cost)
All 78 trap-line edges are noted "carry over A", but they are the PUBLISHED surface's stretch: t = p = c (11.76 / 11.68 / 11.85 at
p4:iron_vow@75:r, 11.20 at idle_warden_town@122:l), A's own 1.00. iron_vow 52, idle_warden_town 26; 34 are interior (share 1).
The absolute carry had A's neck there (ratio about 1.0). The relative carry is B's skinning for every bone outside the girdle by
definition (T9), so B's neck_01 fault (24-29 deg turns) now covers the neck side of the region instead of its border rows only.

## Disagreement LEFT at the border (girdle moved alone)
| border | edges | worst | mm p50 / max | rows needed p50 / max (4 today) |
|---|---|---|---|---|
| trunk back | 42 | 4.34 p4:heroic_leap@19:r | 38.9 / 50.2 | 13.2 / no count cures some |
| breast edge | 42 | 5.30 p4:iron_vow@72:l | 52.6 / 67.8 | 8.7 / 16.8 |
| trap line | 21 | 5.02 Jog_Fwd@11:r | 55.3 / 69.4 | 11.1 / 27.2 |
By clip: Jog_Fwd 49 (keyed clavicle), heroic_leap 32 and x:abd170 16 (arm 150-180 deg), iron_vow 7, cast_flick 1. Trunk back in
Jog_Fwd is gone as a trunk fault (62.8 -> 5.2 mm); what is left of Jog is the clavicle-weighted ring rows.
Pocket: edges 36 | 36; per pose edge max p50 1.56 -> 1.64, max 3.60 -> 3.73 (heroic_leap@9:r); off A p50 5.2 -> 5.1, max 33.6 -> 33.9 mm.

## General form
General (no names, any rigged mesh): `local_pose` (:514), `blend_skin` (:529), `relative_place` (:534): any bone set, placed by the
source's own skin matrices. Still her / shoulder only, all in `tools/body/carried_target.py`:
- :574 `"girdle"` and :571 `"anchor_child"`, :567 / :569 bone map and pose bones, :578 T9's turns: config, lists by name with `{s}`.
- :608 the region's points, border share and sides come from `region_target.Model` (the shoulder region, not a bone set).
- :628 the driven bones are read from her rig's keys (`helpers` kind "unroll", `girdle.scap`).
- :615, :631 two sides "l" / "r" are assumed; :748 the girth rings `mid_deltoid`, `insertion`.

## Do not re-derive
- The cause of the 460 is proven and removed; 355 went, 105 are girdle-alone (above). Wider rows do not cure trunk back (13 rows).
- Re-driving a stored G doubles helpers; rebuild from main-bone locals first. lowerarm / calf are "unroll" helpers but MAIN bones.
- The inverse is safe (sigma >= 0.485); correctives outside the girdle add nothing in the region.
- Open, the lead's call, not started: (a) B's neck_01 weights are the fault now showing (throat pit and neck side, published
  alone); or (b) put the neck in the carried bone set, which brings A's neck back and its border disagreement at the head seam.
