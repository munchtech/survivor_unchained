# Gate T, round 1 (10 Nov, lead 20): judge CLOSE. Not sent to the owner

The target is the per-pose composed surface (`carried_target.py` `Her.compose`). All runs are on body-p1b after 1c23d317a: the map in Her on lay 5, the gate2 relax, and the neck relax. Sheets are in `tools/body/out/shoulder/sheets/`: `gate_l20_a_half.jpg` (8 rows) and `gate_l20_b_half.jpg` (6 rows), columns B published | carried | A, plus `armpit_map_l20_half.jpg` (fill | map | A). Logs `*_l20*` are in `tools/body/out/shoulder/`.

## Table (published / target / A where measured)
| row | number | bar | state |
|---|---|---|---|
| Chest fold overhead (abd150 / abd170 / flex170), valley max deg | published 23.0 / 27.1 / 26.6, target 5.0 / 5.1 / 3.0, A 5.8 / 6.5 / 3.2 | at A's (T19) | MET |
| Gate2's two carried edges (6017-6018, 5932-5933) | 3.63 -> 1.44 / 1.54 / 1.48 | T17 limits untouched | MET (gate2 `relax`) |
| At or under 90 deg elevation, against `target_a_l18` | 0.0 on the 6 dev poses (T18) | bit for bit | MET |
| Armpit map, 15 named poses | turned 0; overhead worst <= A's own + 0.15; transition <= fill + 0.15 (T22) | as written | MET (lay 5 `_h`) |
| Armpit map, all 141 poses (`turned_l20_all.log`) | 5 poses with real map share have turned triangles: crossbow_shoot@0:r (w 1, 1), @2:r (w 1, 1), cast_flick@8:r (w 1, 1), cast_bolt@6:l (w 0.96, 3), heroic_leap@6:r (w 0.82, 3); heroic_leap@0:l / @30:l are fill +0.18 / +0.16 | turned 0 on every frame | NOT MET |
| Map worst overall | heroic_leap@18:r 3.61 (A's own 4.35), @19 3.43 (4.16) | <= A's own + 0.15 | met. The reference moves with the lay |
| Shoulder list, edges over 2.5x (`edges_l20.log`) | OLD 293 (pocket 130, A's own 110, carrier 48, border 5); NEW 76 (published 36 = Jog, bridge 8, carrier 32) | judge fix 4: under 2.5x beyond A's own | OPEN |
| Neck set, edges over 2.5x | 16 (up to 7.06x, head-piece patches) -> 0 (T23) | 0 | MET (neck `relax`, ratio 2.4) |
| Neck + stump weight fit (`neck_fit.md`) | skin vs target 0.55 / 2.36 / 12.95 mm (published 2.59 / 11.79 / 60.43); seam 0.0; face bit for bit; VERDICT 2 met | three conditions | MET (nothing published) |
| A1 neck rule on the fit | neck_01 <= 40 deg any axis (flex >= 60, extend 40, side 50, twist >= 60), split 20 / 30 / 50; 7 p4 clips 0 frames over | confirmed | SENT to main |
| Shift against A per band (`shift_l20.log`), worst in95 mm | fold_front 16.0, fold_back 6.8, deltoid 15.5, trap 31.9, breast 12.6 (median in95 <= 3.0) | volume kept | trap 33-53 mm on big-neck poses (warden_town@126, iron_vow@72 / 75), the same on lead 19's target: an anchor-reading question, not checked |
| Silhouette against A, region p95 mm | <= 28.0 (front 24.1, side 28.0, top 10.1) | no baseline | `silhouette_pub.json` is empty; no published column |
| Jog_Fwd (breast top) | published breast-top edges up to 7.7-7.9x (Jog_Fwd@11:r, @14:l); gate shut (elevation 43-56, clavicle keyed 35-40 deg) | judge: FIX before the fit | NOT MET |
| bends check, `heroine.glb` | HARD FAILS none (`bends_l20/summary.txt`) | | MET |
| P2 spaulder, stance-referenced cap top (`ride_travel.md`) | NEW floor p95 / max 21.0 / 23.5 (l), 19.4 / 21.7 (r) mm | 5 mm | SENT (articulated spaulder stands) |
| `pops` | does not run on the carried provider (needs live clips) | | not measured |

## Judge (su-lead-max, max effort, 74k): CLOSE
The rows:
- PASS: add0, cast_bolt@0, warden_town@122, abd150, abd170, flex170, crossbow@10, warden_town@126, iron_vow@75, the armpit map.
- CLOSE:
  - Jog_Fwd@11:r: the breast top is published.
  - abd120: a crack-like dark line at the front armpit. It is A's own pinch, "being A's doesn't pass it".
  - heroic_leap@9:r: a dark streaked sliver in the armpit.
  - heroic_leap@19:r: faint streaks in the hollow.
  - iron_vow@72:l: a hard-edged flat face at the front of the cap. It is A's crease, carried.
- No carried/published border is visible anywhere.

The fixes, ranked:
1. **De-pinch A before carrying it** (girdle). Find A's pinches (edge angle under about 160 deg, or compressed edges) and replace the carried offset there with a volume-keeping smoothed one. The front armpit at 100-140 deg becomes a soft groove, with the angle raised from 141 to at least 165. This also fixes iron_vow@72:l. "A is the floor for the shape, not for its skinning faults."
2. **Extend the map.** Re-lay for the arm-behind poses (heroic_leap @6-@19) and the frames between. The hollow becomes one smooth bowl between the pec and lat ridges, with a minimum-width guard. Add the 5 turned poses to the named set, and require turned 0 on every frame of the fit list.
3. **Breast-top gate.** Open it on lift relative to the ribcage with the clavicle included, or on the published breast-top stretch itself (open past about 1.8x), so Jog's 40 deg clavicle opens it. The shape is A's breast top lifting with the pec's clavicle head, at most 2.5x.
4. **Stretch.** Once the shape is set, slide vertices along the surface per pose so the carrier's 48 and the pocket's 130 fall under 2.5x, adding no stretched edges beyond A's own.
5. **cast_bolt@3:r:** a short dark tick on the ribcage below the armpit, in the fill and the map. If it is the band's border, widen that blend.

The judge's word on Jog_Fwd: "fix before the weights fit, not just written down: the weights copy the target, so 7.7x would ship in the run cycle at the cleavage."
