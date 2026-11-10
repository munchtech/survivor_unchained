# Neck region: its own edge table (lead 18's builder 3, 10 Nov; full run, 141 poses, `target_a.npz`)

**Command:** `python tools/body/region_shape.py edges --provider carried` (prints the NECK set after OLD / NEW; json `edges_carried.json` adds `totals_neck`, `edges_neck` (count), `kinds_neck`, `stale_neck_mm`, `poses_neck` {pose: [worst target, edges over, worst published]}, `table_neck` (every edge over, worst first, with both ends' vertex, piece, open, weights). Code: `InnerSet` in `region_shape.py`; the region's name comes from the config (any region that is no side's out region gets a set).
**Unchanged:** OLD 200 (pocket 36, A's own 110, border blend 6, carrier 48), NEW 76 (published 36, bridge 8, carrier 32).
**The set:** 3119 edges with both ends in the neck region and no end in a girdle's region: md-md 514, md-raw 46, raw-raw 2559 (1130 points). Stored against the live compose: 0.000 mm. Carrier without a candidate on A: 0 points (A's own is given on every edge).
**Over 2.5x: 16 edges, class `A's own` 16** (neck interior 0, neck ramp 0, seam 0, published 0, bridge 0). All 16 have share 1.00 at both ends; 15 are raw-raw edges of the HEAD piece, 1 lies on the body / head weld row (open boundary, y 1598).
**The 6.75x edge is FOUND:** head piece, rest (-11.2, 1602.8, 23.9) mm: 6.75 at `p4:idle_warden_town@122:l`, 7.06 at `@126:r` (its worst). It was never a girdle edge.
**Worst poses (target / edges over / published):** p4:idle_warden_town@126:r 7.06 / 10 / 2.10; @122:l 6.75 / 8 / 2.02; Jog_Fwd@11:r 5.72 / 5 / 2.06 (dev run); the rest in `poses_neck`.

| # | pose | ratio | published | A's own (unregistered) | class | pieces | y mm | side | rest x, z mm | top weights, end 1 / end 2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | p4:idle_warden_town@126:r | 7.06 | 1.90 | 7.06 (4.00) | A's own | head / head | 1602.8 | side | -11.2, 23.9 | Head 0.78 spine_04 0.13 neck_02 0.09 / Head 0.80 spine_04 0.11 neck_02 0.09 |
| 2 | p4:idle_warden_town@126:r | 4.71 | 1.57 | 4.72 (2.79) | A's own | head / head | 1606.1 | side | -12.8, 22.6 | Head 0.79 spine_04 0.12 neck_02 0.09 / Head 0.82 spine_04 0.10 neck_02 0.08 |
| 3 | sword_heavy@10:l | 4.09 | 1.63 | 4.09 (4.09) | A's own | head / head | 1613.1 | side | 25.9, 12.3 | Head 0.78 spine_04 0.11 neck_02 0.11 / Head 0.75 spine_04 0.13 neck_02 0.12 |
| 4 | sword_heavy@10:l | 3.91 | 1.60 | 3.91 (3.91) | A's own | head / head | 1610.3 | side | 25.5, 13.1 | Head 0.76 spine_04 0.12 neck_02 0.11 / Head 0.74 spine_04 0.14 neck_02 0.12 |
| 5 | p4:shield_charge@0:r | 3.31 | 1.51 | 3.31 (2.26) | A's own | head / head | 1616.2 | side | 25.9, 12.2 | Head 0.80 spine_04 0.10 neck_02 0.10 / Head 0.76 spine_04 0.12 neck_02 0.12 |
| 6 | p4:iron_vow@75:r | 3.27 | 1.54 | 3.24 (2.60) | A's own | head / head | 1619.0 | side | 35.7, 2.7 | Head 0.74 neck_02 0.13 spine_04 0.13 / Head 0.69 neck_02 0.16 spine_04 0.15 |
| 7 | p4:idle_warden_town@126:r | 2.98 | 1.39 | 2.98 (1.90) | A's own | head / head | 1610.2 | side | -14.0, 21.8 | Head 0.80 spine_04 0.11 neck_02 0.09 / Head 0.83 spine_04 0.09 neck_02 0.08 |
| 8 | p4:idle_warden_town@126:r | 2.74 | 0.87 | 2.74 (1.78) | A's own | body+head / body+head (open boundary) | 1597.9 | side | -9.6, 24.7 | Head 0.75 spine_04 0.15 neck_02 0.10 / Head 0.74 spine_04 0.16 neck_02 0.10 |
| 9 | axe_heavy@7:r | 2.72 | 1.47 | 2.72 (2.72) | A's own | head / head | 1618.2 | side | 32.4, 6.0 | Head 0.75 neck_02 0.13 spine_04 0.12 / Head 0.71 neck_02 0.15 spine_04 0.14 |
| 10 | axe_heavy@7:r | 2.60 | 1.57 | 2.60 (2.60) | A's own | head / head | 1618.9 | side | 34.8, 3.5 | Head 0.74 neck_02 0.13 spine_04 0.13 / Head 0.69 neck_02 0.16 spine_04 0.15 |
| 11 | axe_heavy@7:r | 2.58 | 1.55 | 2.58 (2.58) | A's own | head / head | 1618.5 | side | 33.2, 5.1 | Head 0.75 neck_02 0.13 spine_04 0.12 / Head 0.70 neck_02 0.15 spine_04 0.15 |
| 12 | axe_heavy@7:r | 2.57 | 1.30 | 2.57 (2.57) | A's own | head / head | 1617.4 | side | 28.7, 9.6 | Head 0.77 neck_02 0.12 spine_04 0.11 / Head 0.74 neck_02 0.13 spine_04 0.13 |
| 13 | p4:shield_charge@0:r | 2.57 | 1.41 | 2.57 (1.86) | A's own | head / head | 1611.3 | side | 24.0, 14.3 | Head 0.79 spine_04 0.11 neck_02 0.10 / Head 0.76 spine_04 0.12 neck_02 0.11 |
| 14 | p4:idle_warden_town@126:r | 2.53 | 1.28 | 2.53 (1.80) | A's own | head / head | 1602.6 | side | -12.8, 23.0 | Head 0.77 spine_04 0.13 neck_02 0.10 / Head 0.80 spine_04 0.11 neck_02 0.09 |
| 15 | p4:idle_warden_town@126:r | 2.51 | 1.34 | 2.51 (1.77) | A's own | head / head | 1606.2 | side | -14.2, 21.7 | Head 0.78 spine_04 0.12 neck_02 0.10 / Head 0.82 spine_04 0.10 neck_02 0.08 |

Columns: A's own = the reference as the carry reads it (A posed by the neck's part pose, registered at the trunk and Head anchors, blended by the far field); in brackets the same BEFORE the registration (A's skin alone under the transferred turns). Side by the rest normal (top / under over 0.6 of up, front / back over 0.5 of front, else side).

**Plain reading.**
- WHERE: two small patches of the HEAD piece just above its seam row, y 1598-1619 mm, 10-36 mm from the midline: one at x -10 to -14, z +22 to +25 (y 1598-1610: the idle_warden_town edges, the 6.75 / 7.06 one among them), one at x +24 to +36, z +3 to +14 (y 1610-1619: sword_heavy, axe_heavy, shield_charge, iron_vow). Every end carries Head 0.69-0.83 with spine_04 0.09-0.16 and neck_02 0.08-0.16 (never neck_01): these are the head piece's seam-band weights of the earlier diagnosis. The patches are not mirror twins and their normals face sideways so close to the midline: they may be an inner or folded part of the head piece. NOT verified (no picture opened, the piece's triangles not inspected).
- NOT the band found earlier on the body (front y 1517-1545, nape 1536-1548): no body edge of the neck's interior passes 2.5x in any pose. The 514 md-md and 46 md-raw edges give one edge over (the weld row, 2.74).
- Published is 0.87-1.90 on the same edges and poses (2.10 its worst anywhere in the set): B's weights alone do NOT make this stretch. The composed target has it, at share 1, and the target equals A's own ratio to 0.01 on every edge: the carry copies the reference faithfully and the REFERENCE is stretched there. A region fault, of the kind "the reference is wrong here", not a ramp or share fault.
- Of the 16, 6 are stretched as much in A's skin alone (unregistered = registered: sword_heavy, axe_heavy), 10 only reach their ratio after the registration (unregistered 1.77-4.00 against 2.51-7.06: every idle_warden_town, shield_charge and iron_vow edge). So two sources add up: A's own head / neck skin under the transferred turns (already 4.00 on the worst edge) and the anchor registration's field blend on top (4.00 -> 7.06).
- Seam: one edge of 16 lies ON the head piece's seam row (2.74, published 0.87); the other 15 are 1-4 rows above it, inside the head piece, none on an open boundary.
- One line, no more: look at A's own skin and the far field of the Head anchor on these two patches before touching B's weights or the region's rows.

**NOT done:** no fix; no picture; the patches' place on the head piece (outer skin or inner part) not checked; `carried_target.py test` not rerun (nothing it imports was touched); the `under` label and the unregistered column were added after the dev run and are in the full run.

## Relaxed (lead 20's worker)

`Her.relaxed` now also works on a region with no side (no elevation, w = 1, every row open); config neck `"relax": {"ratio": 2.4, "rows": 2}` (2.4, not 2.5: the placement adds up to 0.1 to a carried edge; iron_vow@75:r carried 2.47, composed 2.51). Without the key nothing changes. Test T23 (`carried_target.py test`; the neck set of 2723 edges with no end in a girdle region); T22 is the armpit map's bar (cmd_turned's numbers). T18 now runs with the neck rule off (its stored file predates it).

| pose | worst edge before | worst after | edges over 2.5x before | after | published worst |
|---|---|---|---|---|---|
| p4:idle_warden_town@126:r | 7.06 | 2.01 | 10 | 0 | 2.10 |
| p4:idle_warden_town@122:l | 6.75 | 2.01 | 8 | 0 | 2.02 |
| sword_heavy@10:l | 4.21 | 2.04 | 8 | 0 | 1.63 |
| p4:shield_charge@0:r | 4.26 | 2.19 | 9 | 0 | 1.63 |
| p4:iron_vow@75:r | 3.27 | 2.13 | 4 | 0 | 1.69 |
| axe_heavy@7:r | 3.75 | 2.19 | 11 | 0 | 1.71 |
| Jog_Fwd@11:r | 5.72 | 2.34 | 5 | 0 | 2.06 |

Head-rigid points (Head weight >= 0.999, 16574) and the girdle regions outside the neck: moved by the rule 0.0 m on all 7 poses. Full test: 83 PASS (61 + T22 x15 + T23 x7), ALL PASS.
