# P2 l16 bar solver: facts (WIP, bar NOT built; context ran out)
Done (adorn.py, commits 460b9cb38 + next):
- adorn carries morph targets: deltas ride as `_T<nn>P/N` pseudo-attributes (copied/dropped/compacted with their verts), new geometry carried from the base shell's closest point (carry_source/carry_deltas), written back sparse. plate_top_plain Model load+save: 0 mismatches (all attributes + 18 targets byte-equal).
- pose_check skips (with reason) when poses.npz lacks the followed shell's helper joints (was KeyError upperarm_twist_02_l).
- Staged test (ARMOR_STAGE=scratchpad l16/stage, NOT installed): `adorn.py plate_top_etched` on the current plain: rc 0, all 7 meshes carry 18 targets. Its index row showed no `finish` key in the first fields: unverified.
Tongue facts (plate_top_plain, for the bar tool):
- top.steel verts 9792..11624 (1833 verts, tris 12016..13915, pieces 13/14/15): 2 plate/roll components (739+872 verts) + 3 rivets (60/81/81); all on ONE row: joints [4,3,74,73] = spine_03 .737, spine_02 .216, breast_r .028, breast_l .019 (= gore socket row). Spans x -0.032..0.030, y 1.337..1.369, z 0.105..0.143 (glTF: y up, +z front).
- lod1.steel: 2 comps (149+151) near the gore; shadow: 2 comps (57+39), 96 verts on the gore row.
- cups' inner rims: piece 1 x max -0.028, piece 2 x min 0.026. COLOR_0 g (piece) on tongue 64486, a 0/65535; TEXCOORD_1 x = edge dist (<=0.05), TEXCOORD_2 const [0,1]. Targets sparse.
Not done: tools/armor/top_bar.py, PIPELINE P2b row, gilded re-adorn, finish test change (step 3), chain, pytest.
