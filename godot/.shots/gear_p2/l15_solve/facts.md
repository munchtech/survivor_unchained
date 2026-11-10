# plate top l15 solver: facts (STOPPED at the 60k no-edit line; nothing built, no code changed)
Blocker 1 (ARMOR REFUSED), where 03e3bcb5 comes from:
- armor_index body_hash: 7de7f07b at b8a9cacdc (armroot blend build, build.py) -> 03e3bcb5 at 4ff1b1d51 (Body 15 G3 chain:
  body_follow_post + plate_fit + pose_tuck + body_channels_post, run from coordinator fce3bb46's scratchpad body15\chain.sh
  = S14\g4\chain.sh + the channels step). That scratch was never backed up (survivorsunchained_inputs\scratch_fce3bb46
  has only face43/face46). No blend for 03e3 exists: armor_src blends are dated 18-24 Oct, the chain ran 26 Oct.
- No repo tool writes 03e3: body_hash is written only by heroine_outfits.armor_tuck_write (in Blender, at tuck time),
  piece_blender, gear_fit (glb sha1), native_recipes/native_spaulder. body_follow_post does NOT write it. So the chain's own
  unrecorded script stamped it.
- The stamp is the tuck-time Blender body, not the glb. Same formula on glb positions (Heroine node, indexed points,
  x1e5 rounded, unique, <i4, sha1; script: scratch l15/glbhash.py): heroine.glb@b8a9cacdc = a4efe2d8 (stamp 7de7f07b),
  @4ff1b1d51 = @HEAD = 66182af6 (stamp 03e3bcb5). The BODY_OUT export's glb post-edits (heroine_outfits.py 10445-10514)
  and heroine_body_post's skin moves explain it. P1 R1's seam feather did not move points. So 03e3 can't be re-derived
  from files, and the gate compares stamps, not geometry.
Recommended general fix (the route the shipped tops took, made one recorded step):
  1. piece_blender on heroine_built_armroot.blend (7de7f07b), outputs to a STAGE art dir, plus its built-on body exported
     as base.glb (the Heroine body object at tuck time, the same gltf settings as heroine_outfits.py:10445; Body() skips
     the skin_head prim; Field pairs points by material name + UV within 2e-6, MATCH_R 20 mm; lost points land on BODY's
     surface).
  2. body_follow_post.py base.glb godot/art/people/heroine.glb STAGE --parts armor (follow_file on the piece only, then
     remap_records on STAGE/armor/armor_tuck|armor_cover). It already carries helper joints, 8 weights, 18 shoulder
     shapes and rigid shells.
  3. Install into godot/art/armor and stamp the row. Better: replace the stamp with a geometric one any tool can check
     from files (the glb positions hash: 66182af6 for the shipped body), stamped on armor_index and the piece's extras
     after the follow.
  4. pose_tuck (wearcheck dumps) as the G3 chain did, cover.py, then gear_fit bind + build --body p1 (godot/art/gear/out/body_p1).
  Check first: base.glb's material names and UVs match heroine.glb's Heroine prims (else Field finds no twins).
Blocker 2 (adorn KeyError 'JOINTS_1'): not started. body_follow_post._weights(G, attrs) (line 96) already reads any count
  of JOINTS_n/WEIGHTS_n, and _append/_sparse_g write them (mirror_piece.py and plate_fit.py import them). Route adorn.py's
  4-weight lists (~144, 963, 976, 1027, 1229) through _weights and write the sets back as the shell has them.
Wear after: not run. pytest: not run (was 127 passed).
