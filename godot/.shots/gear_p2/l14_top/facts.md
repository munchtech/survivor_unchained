# plate top l14 helper: facts (WIP, NOT BUILT)
Causes found:
- Gore: a 34 mm tongue cut from her skin (corner+14 to corner-20 mm, tapering to a 5 mm tip), hinged ~25 deg on the worn rest (bridge rule): seen as a curled sliver.
- Etch: the tier's steel is key `steel` = finish `enamel` (navy paint, metal_finishes.json); the ground is `blacksteel` (dark metal) and the vine is the navy shell: navy on near-black, plus 1 mm lines / 1.3 mm stem / 4.2x2.6 mm leaves at ~1.3-1.8 px/mm. Plain reads silver only because its row has finish plainsteel.
Changes (code + recipe data, commit "plate top: ... WIP"):
- piece_blender.gore_plate `bar` mode (plain piece.json gore: top 16, drop -2 mm, thick 3.5, roll 4.0/1.1 mm, camber 1.5 mm): straight chord rows between her skin at the cups' innermost rim, bowed forward, never behind skin; square ends clipped on the cups; 2 end rivets at mid-height; gore socket on the bar's face. piece_blender row writes piece.json `finish`; adorn variant rows take their own piece's finish, never the base's.
- etched: finish plainsteel (bare steel + black ink), sky 0.6, band 13.4-22.0 mm, lines 10.6-12.4 / 23.0-24.6 mm, stem 2.0, leaf 4.0x3.4, wave 26, leaf every crest; NEW adorn.motif_film: an upright blackened fleur 22x18 mm off the inner line at each rim's lowest point (lower cup, ~110 mm from the apex; the upper rim is 39 mm from it).
BLOCKERS:
1. Blender build REFUSED: built on body 7de7f07b (heroine_built_armroot.blend) and bdd0db65 (heroine_built_armB.blend); shipped body 03e3bcb5. The tops were last made by Body 15's follow, not piece_blender: no source blend for 03e3 known.
2. adorn.py plate_top_etched fails on the tip too: append() KeyError 'JOINTS_1' (the followed base shell has 8 weights).
Nothing written to godot/art/armor or out/body_p1. Wear before: godot/.shots/gear_p2/l14_top/wear_before (log ../l14_top_wear_before.log, was still running). After: not run. pytest: not run.
