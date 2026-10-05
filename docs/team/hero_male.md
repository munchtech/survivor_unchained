# Male hero: status

Agent ab82cbe99e2937ddd, branch `worktree-agent-ab82cbe99e2937ddd` (took over from ae2de192cce8298ca).

## Current state: his current body stays, polished
- **Legal has cleared both bodies to stay.** The owner confirmed TRELLIS 2 and Krea 2 Turbo, both run locally. The MakeHuman rebuild below is a fallback only.
- **His new `hero.glb` is committed** (sheets: `docs/hero_male/face4.jpg`, `body4.jpg`). It beats e7709bd in every view:
  - one skin tone from his scalp to his chest, with no seam at his nape or under his jaw;
  - his Krea face no longer olive or green-cast;
  - his skull rounded;
  - his ears clean;
  - the white collarbone lines and blotches gone;
  - his skin matte, with roughness 0.62, sheen 0.3 and extra roughness edge on (`People.HisSkin`, the shader's new `edge_rough`).
- **Still only behind `--body hero`** in the game, until his outfits exist. His own `him/` clips play (merged from animation).
- **`People.HisShadow`** wires his stubble (scalp and beard ground) and a brow dye, from `head_tex/hero_shadow.png`. The brow dye is off: his painted brows have no hairs, so a dyed brow reads as a smudge of colour.

## Next (exact)
1. **Hair, brows and beards (`tools/assets/hero_male_hair.py`):**
   - hair cards in the heroine's way;
   - brow cards over his painted brows, with the painted brows lifted to a shadow through the mask, then `brow_dye` turned on;
   - beards as cards from his beard ground, with the head's shape keys;
   - stubble through `HisShadow`.
2. **The base garment,** then his four outfits (`hero_male_outfits.py`).
3. **The Look step:** `heroes.male` and `BeardStyle`, with the UI lead.
4. **Later:** a body skin layer (redness at the knuckles, knees and elbows; the body still reads a little like clay).

## Fallback: the rebuild (path A, MakeHuman's CC0 body, a 1.98 m rugged build)
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
