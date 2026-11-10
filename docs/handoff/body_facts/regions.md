# Composable carried regions: girdle + neck (10 Nov, solver for P1 lead 17)

`python tools/body/carried_target.py test | target`. Builds the TARGET only: B's rest shape, order, bones, weights untouched.
Read `relative_carry.md` first (the relative placement); this file is what was added on top.

## The design as built (all in `tools/body/carried_target.py`, section REGIONS and `Her`)
- **Region** (`class Region`): a bone set of the source rig (their LOCAL transforms make the part pose, `Her.part_pose`), the
  chain map reference bone <- source bone, the anchors [(source, reference)] root first, the far anchors' fields, the points
  (source vertex ids), their share (an array, or a function of the pose), edges, a Carrier, and `spread` (every source vertex
  welded to a point, so body and head pieces get one delta at the seam).
- **Providers.** EXPLICIT: the two girdles, exactly today's (`region_target.Model` ids, `Model.blend` seam, pocket fill).
  DERIVED (`derive_region`): core = points whose weight on the set is > eps 0.02 and that are not rigid to a far anchor
  (weight >= 0.999); grown by `rows` 4. Share 0 on the outer row and on every far-rigid point, rising over 4 rows from either:
  toward the trunk the ramp lies in the grown rows (share 1 on the whole core), toward the head it lies inside the core, so
  head-rigid points are B's own by construction. Neck: 5542 welded points over body AND head piece, share 1 on 3739.
- **Chain map (neck).** A has neck_01 + Head for B's neck_01, neck_02, Head, and A's neck_01 joint sits exactly on B's neck_02
  joint (y 1.5841). Map: A neck_01 <- B neck_02, A Head <- B Head (config `ref`). So the END's turn against the trunk equals
  B's, and A's two joints turn as B's upper two; what A lacks is B's base joint (neck_01 at y 1.458).
- **Anchors and the blend field.** Each anchor gives a rigid registration of A's posed surface (`anchor_align`): the trunk
  (identity in a part pose) and the Head (rotation = identity because the END turn is matched, so it is the translation by which
  B's base joint swings the head; 66 mm at neck_01 30 deg). They are blended on A's VERTICES (`register`) by a field in 0..1 =
  how far each A vertex follows the mapped chain, MEASURED by turning the chain's top bone 0.5 deg about three axes
  (`follow_field`: no weights read, works for any poser; for a blend skin it is the chain's subtree weight). The trunk takes
  1 - field. Then the carry, then `relative_place` as before. Why A's own field and not B's weights or a harmonic field on B:
  B's neck weights are the fault, and B's support of the set reaches 23 cm out over the traps, where a harmonic field would
  smear the head's registration into the shoulders. A's field is 0 where A's surface is trunk and 1 where it is neck or head, so
  the swing of B's base joint is spread over A's own trunk-to-neck transition.
- **Composition** (`compose`): target = published(G) + the regions' deltas `share M (c - published(part pose))`, ADDED, each
  under its own share, in the order of the regions' NAMES (bit-identical whatever the listing order). Not normalised to sum 1:
  girdle and neck are sibling chains off spine_05, and a blend skin is exactly additive over sibling chains in the anchor's
  frame, so (A - B) for the whole pose = the sum of (A - B) per chain; halving in the overlap would halve A's deformation.
  `Her.target(G, side)` = the composed target on the side's girdle points (file format unchanged); `Her.compose(G)` = on every
  source vertex. Only regions that touch the output region are computed (`Her.touch`).
- **Config** (`HER`): `regions` (girdle_{s} explicit, neck derived; bones, ref, root, far, rows, eps, rigid), `sides`,
  `out_region`, `driven` (the 22 driven bones by name). The core reads none of her rig's keys and assumes no sides.

## Tests (`carried_target.py test`)
T1-T7, T10 green, unchanged numbers. T9 (spine_02 20, spine_03 25, spine_05 30 only, all regions composed): X - published
max 0.0000 mm l and r (limit 0.01 mm).
**NOT a pass: T11 and T14 (iron_vow) fail; stopped after one attempt, no second design.**
- T11 FAIL: girdles only vs stored target_a.npz, 7 poses: max 2.5e-06 .. 6.7e-06 m (limit 1e-06). Likely cause, NOT verified: the
  reference is now posed with the region's 4 bones only (before: 13, identity turns on spine and neck; A's poser is off its
  rest by 2.7e-05 m under identity turns).
- T12 PASS: outside the region, head-rigid (16574), outer row all 0.0000 mm; ramp rows hide 2.6 mm; worst edge target 2.32,
  published 11.39, A's own 2.23 (A registered at both anchors 2.32); sigma min 0.954, guarded 0.
- T13 PASS: listed backwards, bit-identical (whole body and side). Overlap rows worst 2.83 (iron_vow@75:r; girdle interior 2.02,
  neck interior 3.27) and 1.66 (idle_warden_town@122:l; 1.47, 6.75). **The neck interior OUTSIDE the girdles reaches 6.75x in
  idle_warden_town: not looked into (midline, breast part or head stump), and no file shows it.**
- T14: iron_vow@75:r FAIL: target 2.83 | published 11.68 | A's own there (absolute carry) 1.63 (limit 2.5 or A + 0.15).
  idle_warden_town@122:l PASS: 1.66 | 11.20 | 1.41.
- Dev subset (target_a_dev.npz): edge max iron_vow 2.83, idle_warden 1.66, abd150 3.20, Jog_Fwd@11:r 5.28 (girdle's, as before).
  Logs: out/shoulder/regions_test.log, regions_dev.log.

## Still her-only (carried_target.py)
- `Her.carrier`, `Her.target` info (girth rings, volume, pocket) and the explicit provider read `region_target.Model`.
- `cmd_target` writes X on the side's girdle points only (`out_region`); the neck's own points outside the girdles (831
  welded body points at the midline and breast part, and the head piece's stump) are in `Her.compose(G)` but in no file yet.
- `HER["bone_map"]` / `pose_bones` / `Her.pose_ref`: only the absolute carry uses them now.

## For the lead
- Full target: `python tools/body/carried_target.py target > tools/body/out/shoulder/target_a_regions.log` (overwrites
  `target_a.npz`; copy it to `target_a_rel.npz` first to keep the girdle-only relative target).
- Edge table: `python tools/body/region_shape.py edges` as before. `edge_rows` now adds `h.last["others"]` (the neck's delta)
  to the live blend and to the carried column, so `stale` stays 0. Its "A's own" column is still A's GIRDLE-only pose: neck
  stretch that is A's own will be classed "carrier", not "A's own".

## Needs a decision
- The neck target moves the HEAD piece's stump too (its vertices with Head weight < 0.999; the body's seam row has Head
  0.51-0.78, it is not a rigid border: the rigid border is inside the head piece). A fit of body weights alone cannot follow
  the target at the seam unless the head stump's weights are fitted with it, or the seam row is held to published.
