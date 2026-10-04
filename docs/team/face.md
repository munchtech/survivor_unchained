# Heroine face, hair and creation's Look: status

Agent ade92e8285938438f, branch `worktree-agent-ade92e8285938438f` (took over from abfa9bb430ec2391e).
Read first: `docs/handoff/face.md` (the predecessor's handoff) and `docs/FACE_RESEARCH.md` (the science).

## The owner's asks (2026-10-04)
- "weird hair strands in her neck", and a ragged hairline;
- "all of the pre made faces are kinda ugly"; generate beautiful ones with the local AI;
- forehead and other features not editable; "chin can't get any narrower";
- "the customizations don't do enough"; "look up beauty science and proportions and fix that stuff".

## Current state
- **Her head is rebuilt from `face_shapes.py`:**
  - `heroine_head.py` reads it: FACE (the landmark-fitted face), the sliders and the sculpts.
  - 45 sliders are shape keys either way, with their reach; the eyes follow their sockets.
  - Her neck's two sliders move bones (`HerPose.NeckWidth` and `NeckLength`), so collars follow.
  - The default face: the mean of four fits to her AI references, then nudged toward the research (larger eyes, higher brows, slimmer jaw and chin).
- **Her face is repainted** (`heroine_face.py`, Krea, seed 11). The prompt now uses the references' beauty framing: fine auburn brows, lighter freckles (MakeHuman's are closed out of the drawing first), lips with a tint.
  - It paints nothing above her hairline, where one painting drew swept-back hair.
  - `FACE_LAY_ONLY=1` lays a chosen set of views without painting again.
- **Hair** (`heroine_hair.py`, all five styles):
  - A real hairline (`face_shapes.HAIRLINE`): rounded at her temples, down in front of her ears, round them, slightly uneven. The old one left her temples bald.
  - Her ears are found by their own keys, and no hair grows on them.
  - Roots thin out toward the hairline. Fine hairs, then baby hairs (faint, by vertex alpha) lie over its edge.
  - The cap's fade is longer and uneven.
  - Hair keeps 1.6 cm clear of her neck: it lay on her neck like scratches, and pulled into it as her head turned.
  - Gathered hair goes up round her ears, not over them.
  - The hair carries her head's slider keys, so it follows a higher forehead or a broader face.
- **Game:**
  - `People.HerSliders` holds the 47 slider ids.
  - `looks.json` sliders are written by `tools/assets/face_looks.py`: 8 groups of at most 8, as UI design asked (Head, Brows, Eyes, Nose, Cheeks, Mouth, Jaw, "Ears and neck").
- **Presets, in progress:**
  - Nine new references are being painted by `face_refs.py` (highborn, vixen, doe, sunborn, moonlit, saffron, wildling, hardwon, fey).
  - `face_presets.py` fits each to sliders. It takes off what every fit shares (photo against render) and draws the difference out 1.6 times.

## Key decisions
- **Presets are slider settings fitted to AI references, drawn out:** the raw fits differ from her face by only about 0.2. Next, each preset gets its own face paint (see Next).
- **Neck by bones, not keys:** what she wears at her throat is weighted to the same bones, so it follows without refitting the outfits.
- **One hairline for hair and paint** (`face_shapes.HAIRLINE`), so they can't disagree.

## Next
1. Check in game at full resolution (FaceSheet): her face, every slider at both ends, the hairline, and her neck turned.
2. The main session runs heroine_outfits.py --body on the new heroine_built.blend.
3. Presets: pick a seed for each, fit, check in game; skin and eyes per preset (UI design added the fields).
4. Each preset's own face paint: heroine_face.py on the preset-shaped head, heroine_head.py laying each paint (heroine_head_<id>.jpg), and the game choosing it by preset. That needs the preset id carried into the character's look.
5. Tell UI design to rerun heroine_paint.py and creation_portraits.py; tell the male hero lead the final slider set.

## Notes for other areas
- **Main session:** the new head is in `tools/comfy/out/heroes/heroine_built.blend` in my worktree (hair saved in it). It needs `heroine_outfits.py --body`, and I'll message before pushing art. Her neck's shape is unchanged; neck_width and neck_length move bones only.
- **UI design (a69858664f1d3dd29):** the groups are written. Brows are painted in, auburn. The run order is in my message.
- **Male hero (ab82cbe99e2937ddd):** import `face_shapes` (SLIDERS, REACH, slider_keys); its MACROS and FACE are hers. The neck is by bones.
- **Scratch:** `scratchpad/face2/` holds `fs.ps1` (FaceSheet), `shot.ps1` (game shots), `anchors.ps1`, `montage.py`, `overlay.py`, `hair_dbg.py`, `paint_seeds.ps1`, `cmp_presets.py`, and `refs/` and `an_her/` (anchors on her face).
