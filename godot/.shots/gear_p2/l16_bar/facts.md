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

## Bar BUILT and installed (P2 l16 solver 2, 10 Nov): `tools/armor/top_bar.py`
- Installed from the HEAD tongue: top.steel -1833 / +1952 verts (-1900 / +3544 tris; pieces 14 plate 1280, 13 roll 2184, 15 rivets 80 tris, appended last); lod1.steel -747 / +428 (-614 / +716 tris, no rivets); shadow -96 / +92 (-184 / +124). Every other vertex, triangle soup and mesh byte-identical (asserted before the write).
- Gates: bar 65.65 x 17.80 mm (rolled edge incl.); min bar->cups 5.27 mm (left 5.27, right 5.34; clear 4.5 holds for the WHOLE bar, rolled edge's 1.2 mm reach included); skin standoff min 0.56 mm along z, 0.47 mm nearest (lift 0.5); within link_m of both cups.
- Rows y 1.3528..1.3668 (corner 1.3508 - drop, + top); x_in 28.5 mm (installed rims). End law: per row as far out as the whole bar stays clear + 0.3 mm off the cups AND no cup within 30 mm in front of it (+z): the bar's own normal is steep, so gore_plate's ray-along-normal "under" test slid the ends 12+ mm behind the cups (73 mm wide).
- Targets: one delta per target, the mean of the tongue's POSITION deltas (top.steel, 1833 pts; 0.4..2.6 mm), zero NORMAL deltas (a rigid translation turns no normals); same delta in all three meshes; a re-run keeps the bar's one value exactly.
- Attributes: the tongue's row bytes (JOINTS_0/1, WEIGHTS_0/1); TEXCOORD_0 = affine fit of the tongue's own uvs per kind (plate/roll/rivet); TEXCOORD_1.x = edge distance (plate 0.05, roll inside the cut, rivet radius), .y = the tongue's median per kind; TEXCOORD_2 = the tongue's [0,1]; COLOR_0 = the tongue's median per kind (g 64486, a 0 plate / 65535 roll+rivets).
- Gore socket -> [0.0, 1.35611, 0.13327], normal [0.0, -0.926, 0.377].
- FLAG for the lead: the chord law (her skin at +-x_in per row) puts the bar in the cleavage, rising steeply forward with height (skin at x 28.5: z 113 -> 142 mm over the 14 mm rows) while the cups' inner rims stand at z 145-148: the bar face points mostly DOWN (normal above) and sits up to ~30 mm behind the cup rims at its lower edge. It is the law as briefed; whether it reads at 1:1 is a picture question (judge).
- Tests: `pytest tools/armor/test_top_bar.py` 5 passed (gates, other meshes identical, one weld group linked to both cups by worn_rest.clusters + link_m, 18 targets one value, re-run byte-identical).
