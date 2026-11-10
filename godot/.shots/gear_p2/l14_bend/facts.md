# l14 bend on the game skin (LBS + correctives) - facts

Lowest height over her skin (mm), all clips, game skin. Rigid = round 4 (reach_table, h = 2.4 - past). Bent = bend_solve min clear (max 1.0, smooth 0.02).

| part | rigid L | rigid R | bent L | bent R | bent worst clip | alpha p50/p95/max L ; R |
|---|---|---|---|---|---|---|
| cop | -27.2 (cast_bolt@0) | -33.5 (axe_heavy@0) | -15.8 | -12.6 | cast_bolt / crossbow_shoot | 1/1/1 ; 1/1/1 |
| lame1 | -15.3 (cast_bolt@13) | -20.5 (crossbow_shoot@0) | -21.4 | -10.0 | cast_bolt / crossbow_shoot | .91/1/1 ; .55/1/1 |
| lame2 | +0.2 (crossbow_shoot@10) | -3.1 (cast_flick@0) | -20.9 | -23.4 | cast_bolt / sword_fore | .57/1/1 ; .74/1/1 |

low_by_pass_mm: cop L [-28.8,-15.8,-15.8,-15.8], R [-33.7,-12.6x3]; lame1 L [-15.5,-21.4x3], R [-15.5,-10.0x3]; lame2 L [-21.3,-20.9x3], R [-19.9,-23.4x3].
Rigid on plain LBS for comparison: cop past 27.0 / 35.8, lame1 15.7 / 14.5, lame2 1.8 / 1.8 (rigid_lbs/).
Flex rigid (shapes carried): cop L 19.8 max (idle 11.8), cop R 15.9 (idle 1.7); lame1 R 17.7, L 15.6. Laps rigid: cop|lame1 L -21.9 cast_bolt@12 (695 fr), R -26.3 axe_back@0 (825 fr); lame1|lame2 L -8.4 (16), R -9.0 (12).
Flex bent: lame1 R 55.5 / L 51.6 max (idle 27.9 / 27.3); lame2 R 20.2, L 15.2. lame1|lame2 L -8.4 (6 fr), R -8.8 (8 fr). The bent cop is missing from reach_table and flex_check (its varying blend matches no part role): not measured there.
Plate model vs built glb (5 frames, all 16 groups both pieces): max error 0.0001 mm.

VERDICT by number: FAIL (every part goes into her skin, bent too; alpha saturates at max 1.0).
State left: bend OFF by data, out/body_p1 rebuilt rigid round 4.

Commands: native_build.py plate_spaulders_{plain,warden}; gear_fit.py build --only ...; reach_table.py --gear godot/art/gear/out/body_p1 --set plate (--no-shapes for LBS); flex_check.py --pieces plate_spaulders_plain,plate_cuisses_plain. GEAR_BEND_DUMP=<dir> dumps the plate model per bent group.
