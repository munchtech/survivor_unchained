# plate top l15 build solver: facts (stopped at the 120k budget; tools landed, NOTHING installed)
Tools (commits 897df3550, da0bcdc6e):
- tools/armor/piece_ship.py <id> [<variant>..]: piece_blender with ARMOR_STAGE (piece into .shots/armor2/ship/<id>/<time>/armor,
  built-on body exported at tuck time as base.glb), piece_lod, adorn --post, fan_fill, snapshot pre/ (variants adorn it),
  body_follow_post base.glb heroine.glb stage --parts armor, refuse under FOLLOW_MIN=0.95 twins, install with
  body_hash = people label (03e3bcb5..), body_glb = glb_body_hash(heroine.glb) (66182af6 verified), built_on.
  --check lists rows whose body_glb is not the shipped glb's (today: 10 rows, none stamped yet).
- piece_blender ARMOR_STAGE mode (no refusal, no tuck_rekey_shipped in stage; trim_strip read from godot/art/armor).
- adorn.py: weight_sets/joints_weights/top4(d, sets): every JOINTS_n/WEIGHTS_n set read and written (dense, append,
  new_mesh, save, pose, base rows); ARMOR_STAGE; REFUSES meshes with morph targets (its writer keeps none: a followed
  piece's 18 shoulder shapes would be dropped silently) -> variants must be adorned before the follow (piece_ship does).
- tests: tools/armor/test_piece_ship.py (5: glb stamp, install stamps, follow ratio, 8-weight adorn append, 4-weight unchanged).
  pytest tools/armor: 132 passed. PIPELINE.md row P2a.
BLOCKER (new, the solver's flagged risk, real): ship plate_top_plain built fine (LOD 20152 -> 4632/1800) but the follow
  refused: base.glb 40619 welded pts vs heroine.glb 36460; twins 19906 (49%), rest move max 22.86 mm.
  base.glb == heroine.glb@b8a9cacdc in topology (40619 twins, 100%; moves <= 8.64 mm = the glb post-steps).
  b8a9 -> HEAD heroine.glb is ALSO 49% (same numbers): the shipped body is a re-meshed body (pos within 0.01 mm 42%,
  within 5 mm 87%; UV twins 55% / 51% per prim), not "blend body + post-steps". So the armroot blend is a topology
  generation behind; the G3 chain must have followed from an intermediate BASE glb (lost with the scratch).
  Stage kept: .shots/armor2/ship/plate_top_plain/20261110_095119 (base.glb, heroine_b8a9.glb, follow.log, pre/).
Options for the lead (my pick first):
  a. find the body blend/glb whose topology IS the shipped one (36460 pts; grep the body lane's chain for the step that
     re-meshed after b8a9cacdc, e.g. git log -- godot/art/people/heroine.glb between b8a9cacdc and 4ff1b1d51) and point
     build.py SRC at it: then piece_ship's follow is near-100% twins. One body-lane question, no new code.
  b. accept closest-surface correspondence for lost points: lower FOLLOW_MIN (flag --min) and gate instead on the piece's
     own numbers (piece moved max 10.47 mm, off neighbours 3.67 mm here = risky tearing): needs a judge's look; not my pick.
Not run: etched/gilded ships (wait on the plain one), pose_tuck/cover/gear_fit bind/build --body p1, gear_wear after.
Wear before: l14's wear_before log is EMPTY (0 bytes, never finished). Nearest before: godot/.shots/gear_p2/l12_wear/tops.log
  (skin under, close ex/play ex/over 2mm/close frame/play frame): plain 0/155, 0/2268, 76/2568, 0/155, 0/1789;
  etched 0/78, 0/2026, 76/2221, 0/78, 0/1433; gilded 0/155, 0/2272, 144/2572, 0/155, 0/1709.
