Command: blender -b --factory-startup --python tools/body/b_build_blend.py -- godot/art/people/body_p1/body.glb C:/Users/munch/Desktop/survivorsunchained_inputs/armor_src/body_p1_built.blend
Inputs: godot/art/people/body_p1/body.glb, git blob 22ff7d56717cb8fa5dfcd0e76796a2638ee18518 (round_39d)
Output: body_p1_built.blend, 65226583 bytes, sha256 dc5cb7148352234987d0d8c577408760562b4984198bf6d5309fff38ee68f175 (7 objects: Armature 124 bones, 6 Heroine* meshes, no hair)
Check (b_build_blend_check.py): joint set equal, order differs at 105 of 124 slots (exporter's walk); ibm 4.7e-6 by name; positions 0.0007 mm; UV present; strict joint-order bar FAILS
Date: 2026-11-17. Smoke: piece_blender on plate_pauldrons_plain dies at heroine_areola.py:284 (paint, argmax of empty) via piece_blender.py:2688
Joint order: names match, order differs (105 of 124 slots), inverse binds within 4.7e-6 by name; the pipeline maps by name, so not a blocker.
Areola: piece_blender with default env fails at heroine_areola.py:284 (paint, argmax of empty) via piece_blender.py:2688.
Smoke 2 (AREOLA_OUT=0, plate_pauldrons_plain): completes, rc 0; stage has base.glb (124 joints), armor/plate_pauldrons_plain.gltf/.bin/.sockets.json, armor_tuck, armor_index.json.
