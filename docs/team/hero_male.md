# Male hero: status

Lead ac39445bca5508eaf (12 October), branch `worktree-agent-ac39445bca5508eaf`. Predecessors: ab82cbe99e2937ddd, ae2de192cce8298ca.

## The plan (12 October): the heroine's lessons, a straight route
The owner: "Begin work on Hero, using the lessons we learned making Heroine to hopefully do it in a fraction of the time and effort and tokens", and (12 Oct) "you can totally make a new one from scratch if ours is lame. but remember sex appeal. muscular defined, attractive". The bar is unchanged; the saving comes from reuse, never from quality.

**Reuse as-is:** `heroine_skin.gdshader` (relief, stubble/scalp/brow layers already in), `heroine_eye.gdshader` + iris recolour, the hair shader and `HairSway.cs` (after `face/hair-swing` merges), the strand atlas, `heroine_outfit.gdshader` + `outfit_materials.json`, `heroine_rig.py` (helper bones; already takes "hers or the hero's"), `face_shapes.py`, `blend_relink.py`, `lookdev.gd BODY=hero`, his `him/` clips.
**A body parameter, not a copy:** `heroine_hair.py` (object names, hairline, CENTRE), `heroine_lashes.py` (lit lash cards), `heroine_seam.py` and the `under_jaw` cut (face branch), `heroine_outfits.py` (via `hero_male_outfits.py`; the outfits lead's branch stays untouched), `heroine_lod.py` (later).
**New for him:** brow cards (she has painted brows only), beard cards that carry the head's shape keys (2-3 styles), stubble wired through `People.HisShadow`, the base garment, `BeardStyle` and `heroes.male` data.

**Route and judge points** (each a fresh `su-lead-max` judge on one sheet per question, with numbers made first):
- J0 body bar (sex appeal, muscular and defined, attractive, rugged 1.98 m) against the heroine and path A's base: keep and polish, or rebuild.
- J1 head finish: brows, stubble, three beards, lit lashes, skin checks (far neck, under the jaw, moonlight; one tone scalp to chest).
- J2 base garment + mesh audit (doubled/reversed triangles, non-manifold fans), checked in motion.
- J3 each of the four outfits (tucked skin, bound rims, tight fit, motion clips).
- J4 hair on the merged swing code; then the Look step's data and wiring.
- Full-resolution face/front/side/back sheets to the main session after each passing judge.

**Token estimate (honest):** the body and head rebuild about 1.5-2M (3-4 lead sessions, 4-6 judges); head finish 0.5M; base garment and four outfits 1.5-2M; hair and the Look 0.5M. About 4-5M in all, against the heroine's many times that, because the shader, rig helpers, hair system, outfit generator and judging method all exist.

## Current state (12 October): REBUILDING his body (judge j0)
- **Judge j0 (owner's bar: sex appeal, muscular and defined, attractive, rugged 1.98 m): REBUILD, path A, donor variant.** The TRELLIS body read as a stage bodybuilder (traps to the ears, lat spread, swayback, balloon right lat), the face gaunt and 45-55, the skin orange clay, a neck graft ridge. Verdict and targets: `docs/hero_male/verdict_j0.md`; its sheets were the old body's (scratch, not kept). Shoot and sheet helpers: `tools/scratch/hero_male/` (paths inside point at this session's scratchpad: change `O=`). The owner's 12 Oct words replace "the body stays".
- **j0's targets:** athletic heavyweight, 8-10% fat (looks 110-118 kg); upper arm ≈ neck ≈ calf; shoulder girth ≈ 1.6x waist; thigh ≈ 1.75x knee; arms close in idle; gentle trap slope; back with a lat fan, lower-trap diamond, scapula knots, erector columns, sacral dimples; firm square glutes; neutral pelvis; no neck seam; face 30-35, wider squarer jaw, strong chin, cheeks half as hollow, heavy straight brow, fuller lips, clean mirrored paint; her skin pipeline, a warmer slightly darker tone, no baked shading, flat nipples. First sheet: him beside her, same light and scale, front/side/back/3-4.
- **Built so far: `tools/assets/hero_male.py`** (new; replaces `hero_male_body.py` + the graft in `hero_male_head.py` once it carries the head):
  - MakeHuman man (MPFB, CC0) at MACROS/BUILD/NECK/FACE, 1.98 m, stood in a T by LBS on his own weights, Catmull-Clark once (107k triangles), UAL skeleton folded onto his joints (52 bones, `Head` from MH `head`).
  - Donor = the old `hero.glb` (copy at `tools/comfy/out/heroes/hero_donor.glb`), laid on his bones per bone (stretch along the bone only). Volume transfer is in the code but OFF (`HM_GAIN` 0): measured, the MH man already matches or passes the donor's girth where it counts.
  - Detail: Cycles bakes the donor (with its relief) and a smoothed donor to his UVs; the turn between them is the relief (`hero_tex/hero_relief.png`), masked to stomach, flanks, arms, front/outer thighs, calves, and to where both bakes hit.
  - Measures now: upper arm 44.7, forearm 28.3, neck 52.9 (suspect: the slice may catch the trap slope), calf 44.1, thigh 66.4, knee 38.7, waist 81.7, chest 126.4 cm; thigh/knee 1.72.
  - `HM_STOP=shape` (measures only, ~1 min), `HM_STOP=body` (exports a body-only `godot/art/people/hero.glb` with MakeHuman's skin and the relief for lookdev).
- **Look (lead's own working check, not judged):** upright and well proportioned in `him/idle_warden`; a clear V. NOT at the bar yet: definition weak, the donor relief carries TRELLIS's streaky noise on the legs and arms and a band across the lower stomach; deltoids bulge upward (the T-pose LBS at the shoulder); the face is MakeHuman's with the buzz-cut paint; no head split, shapes, paint or masks yet.
- **Uncommitted built art (unjudged, keep):** `godot/art/people/hero.glb` (the v2 body), `godot/art/anim/hero.res` + `tools/anim/data/hero_skeleton.json` (his 73 clips rebuilt on the new skeleton, 872 s). `git checkout` them to go back to the old body.
- **lookdev.gd:** `BODY=hero` now also loads `art/anim/hero.res` as library `him`; shoot with clip `him/idle_warden` and `NECK=0` (UAL's `Idle` hunches the MH skeleton; NeckPitch 22 was for the old one).

## Next (exact)
1. **Definition, cleanly.** Decide between (a) a cleaner donor detail (larger smoothing for B, a de-noise of the relief by a bilateral or a low-pass along the muscle direction, the masks tighter to the judge's list) and (b) authored definition: displacement along masks on the subdivided mesh (abdominal grid, linea alba, serratus, obliques, pec/delt edges, back landmarks). One honest try at (a); if the streaks stay, a `su-lead-max` solver on (b).
2. **Shoulders:** the T-pose LBS lifts the deltoid; try the MH rig's own rest (A-pose) as his rest instead (the clips are retargeted per skeleton, so it is allowed), or correct the shoulder with MH's shoulder targets.
3. **Head stage in `hero_male.py`:** split the head at SPLIT (shared boundary points, normals from the whole mesh), slider/expression shape keys (from `hero_male_head.py` SLIDERS/EXPRESSIONS/base_delta/eye_follow, deltas carried through the subdivision by evaluating the subsurf per key), parts (eyes, lashes, teeth, tongue), head 4K paint, `hero_shadow.png` masks (`scalp()`, `beard()`, brows), export names as before (`Hero`, `HeroHead`, `HeroEyes`... and the `mh` UV for `hero_male_face.py`).
4. **Skin:** body paint repacked to 4K from `young_caucasian_male` (CC0), toned warmer and a little darker in her colour family, its shading taken out; then a new Krea face paint (`hero_male_face.py`, GPU turn) for a man of thirty to thirty-five.
5. **Judge j1** with j0's targets, him beside her (`b1\shoot.sh` + `sheet.py` make the sheets). Then `heroine_rig.apply` helpers, `People.Hero` retune (NeckPitch 0), provenance ledger entry.

## The rebuild in full (path A, now under way; MakeHuman's CC0 body, a 1.98 m rugged build)
1. **His body, `hero_male_body.py` rewritten.**
   - **The man:** a MakeHuman man by MPFB, from the system assets only (CC0):
     - gender 1, age about 0.59 (32), muscle 1.0, weight about 0.6;
     - `heroes.py`'s male detail as the start (V-shape, chest, lats, shoulders, arms, thighs), plus a wrestler's neck and traps, forearms, calves and big hands;
     - scaled so his crown is at 1.98 m;
     - his face's `FACE` targets on the same human, so head and body are one MakeHuman, with no graft and no seam.
   - **The skeleton:** MakeHuman's `game_engine` rig and its own weights (CC0), folded onto UAL the `build_heroine` way: UAL's bones turned onto his joints, keeping their own frames.
     - The bones match by name: all 52 of MakeHuman's weighted bones are in UAL. Only `Root`/`root` and `head`/`Head` differ, by case.
     - UAL's 12 extra bones are unweighted leaves.
     - This answers MODELS_TO_MAKE open question 3: yes, the fold holds.
   - **Our own sculpt pass for definition,** in Blender by script:
     - subdivide;
     - displace, along authored masks, the separations a rugged man shows (abdominal grid, obliques, serratus, the edges of the pectorals and deltoids, forearm and hand veins);
     - bake that to a 4K relief on MakeHuman's own UVs.
2. **His skin.**
   - **Paint:** a MakeHuman system skin (`young_caucasian_male`, CC0, 2K), brought to 4K. Our own 3D colour layers go on top: redness at the knuckles, elbows, knees and ears, darker joints, a faint vein tint.
   - **Shader:** the skin shader as now (relief, pores, stubble), with `rough=0.62, shine=0.32`.
   - **Community skins:** MPFB's user-data skins are community uploads with mixed licences. Use none without checking its `.mhmat` licence.
3. **His head, `hero_male_head.py`:** the graft code goes and his own head is split off at the neck, the heroine's way (shape keys stay on the head).
   - **Kept:** the face shapes, sliders (to import `face_shapes.py` when the face lead's list lands) and expressions; the cranium smoothing; the scalp, beard and brow masks; the ear mask; finding the face paint by MakeHuman's layout; the nose-shading guard.
   - **Rejudged:** the head's size on a 1.98 m frame (`HEAD_SCALE` existed only to fit the sculpt).
4. **His face paint:** Krea 2 again on the new head (path C, under Krea's cap), its tone matched to the new skin. The old paint's tone was matched to the tainted body's paint.
5. **The base garment** (braies or a loincloth): the first piece of `hero_male_outfits.py`, always worn, so he is never bare.
6. **Into the game.**
   - **`hero.glb`:** replaced.
   - **People.Hero:** retuned (tone, HerPose values, skin values).
   - **Animation lead:** re-dumps `hero_skeleton.json` and rebuilds `hero.res` (`build.py --body hero`).
   - **Approval:** full-resolution lookdev sheets (face, front, side, back) go to the owner.
   - **Legal:** the replacement goes in the provenance ledger.
   - **Clean-up:** local caches of the old body are deleted (`hero_male_body.blend`, `hero_male_built.blend`, `hero_tex/`). The owner's own files are never touched.
7. **Then, as briefed:** hair and beards on the final head, his four outfits cut from the new body, and the Look step.

**Optional path B,** if the owner wants a physique closer to the old one: his own drawing, or his paint-over of our render, through TRELLIS 2 (MIT, local). Then `wrap_sculpt.py` wraps MakeHuman onto it, keeping MakeHuman's topology, UVs and rig. It must never wrap onto `ComfyUI_00008.glb` or anything shaped from it.

## If the rebuild goes ahead: what carries over, what's lost
- **Carries over:**
  - **The head:** MakeHuman, CC0, as above.
  - **The paint pipeline:** the face-paint tool and the MakeHuman-layout lookup.
  - **The skin shader**, and its relief, stubble and brow layers.
  - **The game code:** People.Hero, his eyes, lookdev's `BODY=hero`, `him:` outfits and `OwnClips.Him`.
  - **The clip library:** `him/`, 68 clips, worktree-agent-a435f4dd0ac80df75@72ab9a8. The bone names don't change, so it's rebuilt, not remade.
  - **The UI and face agreements.**
  - **Hair and outfits:** not started, so nothing is lost there.
- **Partly carries over:** `hero_male_skin.py`. Its 3D field (`broad`, `one_tone`) is kept if the new paint needs blending. Its fleck and streak cleaning was only for TRELLIS's paint and is retired.
- **Lost:**
  - the sculpt's body, its 110k mesh, unwrap, 4K paint and 4K relief;
  - AccuRIG's weights and joints;
  - the head's graft and neck fitting;
  - this session's neck and seam work;
  - the old sheets (`docs/hero_male/face3.jpg`, `body3.jpg`);
  - the exact look of his sculpted physique, which the sculpt pass must earn back.

## Collaborators
- **UI design (a69858664f1d3dd29):** the male Look fields are agreed:
  - `heroes.male` in looks.json, with `beards`;
  - a `BeardStyle` string;
  - `HairStyle` from his cuts.

  Tell them when `heroes.male` and his builder land.
- **Heroine face (ade92e8285938438f):** import `face_shapes.py` (SLIDERS, REACH, slider_keys, SCULPTS) and skip the Neck group. Check `jaw_width` at ±2 and `face_shape` on a man. The final list is to follow.
- **Animation (a435f4dd0ac80df75):** his library is done; it will need a rebuild after step 6.
- **Legal (aa12c130ddf4b904c):** the content and sources questions are answered. Send renders per outfit as they land.

## Notes
- Scratch helpers (this session's scratchpad, not the repo): `ld.py` (Godot lookdev), `sheet.py`, `albedo.py` (unlit Blender), `probe.py`.
- Merging the integration branch on Windows: if git lists untracked blockers, move only the files it names, never a directory line.
