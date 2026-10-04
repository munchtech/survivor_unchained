# Handoff: male hero lead

From agent ae2de192cce8298ca (about 470k tokens), branch `worktree-agent-ae2de192cce8298ca`.

## The owner's bar, in their words
- "AAA standard", "strive for excellent, above and beyond - not just good enough".
- "I don't want to polish, I want to create perfection." Remake rather than polish.
- "Do we have soul?" Unique to this world, not generic.
- Sex appeal drives the heroine, "tho not at the cost of looking bad". The tone values appeal for both sexes; he must be rugged and attractive.
- Check everything at full resolution: the owner reads renders closely.

## The brief (from the main session, verbatim in spirit)
Make the man the player can be the heroine's equal, from the owner's AccuRIG actor at `C:\Users\munch\Desktop\ComfyUI_00008-reduced\` (`autorig_actor.fbx`). The heroine's pipeline is the template. Phases, each checked in renders at full resolution:
1. Inspect the actor (done).
2. Make him playable:
   - animation (with the animation lead);
   - skin on the game's skin shader, his eyes, a head with expressions;
   - hair cards with physics, in the heroine's way, and a beard option.
3. Hook him into the game:
   - the male choice in character creation (with the UI design lead, who builds the Look step for both);
   - save and load;
   - lookdev renders.
4. Cut his four callings' outfits (warden, arcanist, ranger/stalker, reaver) from his own body, as hers are.
   - The bar: tailored, exact straight lines, real stitching, belts and straps that move as made, no holes.
   - They are male counterparts in spirit, not copies.
   - Build them in a male outfit tool of your own: read `tools/assets/heroine_outfits.py` but never edit it (it belongs to the main session, which reviews).
5. How to work:
   - Don't stop to ask; keep tests green; use British spelling.
   - Commit and push at milestones with render sheets.
   - Keep the status in `docs/team/hero_male.md`; hand off past about 500k context.

## Done
- **Body: `tools/assets/hero_male_body.py`.**
  - Reduces AccuRIG's mesh (welded first) to 110k triangles and unwraps it.
  - Bakes 4K paint and 4K normals from the TRELLIS sculpt `C:\Users\munch\Desktop\ComfyUI_00008.glb`.
  - Puts him on the UAL skeleton the build_heroine way: 1.98 m, T-pose rest, 65 bones, pelvis at 1.118.
- **Head: `tools/assets/hero_male_head.py`.** This is `heroine_head.py` adapted:
  - A MakeHuman man's head shaped by `FACE`, at `HEAD_SCALE` 1.06.
  - Sewn into his own neck between `SPLIT` and `CUT`.
  - MakeHuman's painted buzz cut and stubble cleared from the scalp and beard ground.
  - Writes `head_tex/hero_shadow.png` (red: beard ground; green: scalp) for the stubble shader.
  - 65 shape keys: the heroine's sliders plus `chin_cleft` and `brow_ridge`, and her expressions.
  - Writes `godot/art/people/hero.glb` with WebP paint (15 MB).
- **Face paint: `tools/assets/hero_male_face.py`.** This is `heroine_face.py` with:
  - his prompt: a handsome, rugged man in his late twenties, steel-grey eyes, clean-shaven;
  - a gentler delighting (`sg = DRAW/10`; the heroine's DRAW/25 lifted out his brows and left MakeHuman's face);
  - `REUSE=1`, which lays the existing paintings back on without running Krea.
- **Shader: `godot/shaders/heroine_skin.gdshader`.** Both additions are default-off; the heroine is untouched.
  - A baked `relief` normal map (`has_relief`), whiteout-blended with the pores.
  - A shaved shadow from `shadow_mask`, with `beard_shadow`, `scalp_shadow` and `shadow_colour`, broken into stubs. Not wired from People yet.
- **Game code.**
  - `People.Hero(look)`. `HerPart` takes `who`; his default eyes are flint grey; his skin keeps his own tone (`HisTone`) with the relief.
  - `HerPose`: `ArmsIn -5`, `HipTilt 0`, and a new `NeckPitch` of 22°, because UAL clips threw his head back.
  - `Loadouts.HisBody = "man"`. A man's outfit list gets `him:<calling>` appended, and the kit's `Build` skips `him:` parts.
  - `People.Build` uses the hero only with `--body hero`, until his outfits exist; otherwise men stay the kit man.
- **Lookdev: `godot/tools_scenes/lookdev.gd`.**
  - `BODY=hero` loads `hero.glb`, plus his hair and outfits once they exist.
  - It sets his relief, tone and flint eyes, his pose settings, `NECK=` to override the pitch, and no jiggle.
  - The clip name is `Idle` (not `Idle_Loop`).
- **Checked.** In Godot lookdev the idle is fine, with the head level after the neck fix, and his Krea face shows.
- **Still to fix in renders:**
  - the skin reads a little shiny and plastic: try `SKIN=rough=0.6,shine=0.35`, then put his values in `Skin(..., own)`;
  - a white fleck at the top of one ear;
  - the skull is a little boxy at the top-back: ease `head-square` and `head-scale-vert-decr` in `FACE`;
  - the collarbone highlights are a little hard.

## In progress when handed off
The head was being rebuilt at `HEAD_SCALE` 1.06 with eyes a little more open (`X-eye-height2-decr` 0.15), and the Krea face paint was being re-run on it.
1. Then rebuild the head again so it lays the new `face_paint.png`, and render with lookdev.
2. If the paint is off, move `tools/assets/hero_male_face/face_paint.png` aside before rebuilding for new drawings. The head lays any face paint it finds, and the drawings are made from the head as built.
3. Earlier paintings are kept in `tools/comfy/out/heroes/hero_face_paint_v1.png` and `_v2.png`.

## Next, in order
1. **Finish the face.** Tune his skin values, commit `hero.glb` and the code, and send render sheets.
2. **Hair: `tools/assets/hero_male_hair.py`.** Copy `heroine_hair.py`: it can't be imported, because it reads objects at module level.
   - Object names: `HeroHead`, `Hero`, `HeroEyes`.
   - The hairline and `CENTRE` are his (eye height from `HeroEyes`).
   - Styles: crop, swept-back, long warrior hair, an undercut with a top knot or tail, and bald.
   - Reuse the strand atlas `head_tex/hair_strands.png`.
   - Export as `hero_hair_<style>.gltf`, with chains for the long styles.
   - Hook `HisHair` in People.cs, mirroring `HerHair` and `HairSway`.
3. **Beards** in the same tool, as short cards from the beard ground (`beard()` in the head tool; the mask is `hero_shadow.png`): short and full. Give the beard mesh the head's expression and jaw shape keys, each vertex following its root's nearest head point, so `HerFace` and mouth shapes move it. Stubble is the shader layer; wire `People.HisShadow(beard, scalp)` and the shadow colour from the hair colour.
4. **Outfits: `tools/assets/hero_male_outfits.py`.** Read `heroine_outfits.py`: cut from his body, a skin-hide channel in vertex colours, `outfit_materials.json` and `heroine_outfit.gdshader`.
   - Warden: plate and mail.
   - Arcanist: robe and leathers.
   - Ranger/stalker: leathers and a hood.
   - Reaver: near-bare, harness and furs, with the male appeal.
   - Then switch men to the hero by default: drop the `--body hero` gate in `People.Build`.
5. **The rest.**
   - Wire the Look step for men with the UI lead: sliders, beard style and hair.
   - `HisClips` (`him/` prefix) from the animation lead.
   - Save and load his fields.
   - Body clean-up: a smooth doll crotch, which needs a base garment such as braies or a loincloth; a dark patch on the throat (now under the graft, painted from skin); a crease at the rear deltoid with the arms down.

## Decisions
- **His height: 1.98 m** (she is 1.87 m), the usual male-to-female ratio.
- **A MakeHuman head**, as hers is: the sculpt's eyes and lips are moulded shut.
- **The head 6% larger than the sculpt's.** His trapezius muscles and neck made the sculpt's head look small.
- **Clean-shaven face paint**, with stubble and beards as options.
- **His eyes are flint (`Lore.Eyes`) by recolour**, reusing her iris texture.
- **Men stay the kit man until his outfits exist**, so he is never shown naked in play.

## Collaborators
- **Animation (a1e3002b800ee55ac).** Builds his own library: `build.py --body hero` gives `hero.res`, clips prefixed `him/`, with `HisClips` mirroring `HerClips`. Told when `hero.glb` was pushed (6df994d). Until then her clips work if the pelvis is offset; `HerPose` does that, plus `NeckPitch`.
- **UI design (ac76f400913a109cd).** Sent a proposal: `Body = "man"`, a `BeardStyle` string, his sliders in her dictionary. No answer yet. The integration branch has their Look step for her (`Face`, `Eyes`, `Paint`). `LoadoutTests` asserts a man has no `Face` or `Eyes`; update it when his are wired.
- **Heroine face lead (abfa9bb430ec2391e).** Is drafting 47 face sliders (`tools/assets/face_shapes.py`, commit 187606e on their branch) and will send the final list. Mirror them for him: a `REACH` table, + and - shape keys from MakeHuman targets.

## Gotchas
- **Fresh worktree.** Junction `godot/assets` to `public/assets` and set it to assume-unchanged. Copy the `.import` and `.uid` files from the main checkout. Never commit the `.import` files the Godot import dirties.
- **Clips are named without `_Loop`.** `lookdev.gd`'s clip list uses `Idle`.
- **`HerPose` adds the pelvis offset even with no clip playing**, so he floats about 0.2 m if a clip fails to load.
- **Scratch file names.** Don't name a scratch script `inspect.py`: it shadows Python's own module.
- **Bash refusals.** The isolation check refuses complex heredoc and `cd` mixes in Bash. Write patch scripts to the scratchpad and run them with python.
- **MakeHuman skins have a buzz cut and stubble painted on**; the head tool clears both.
- **Krea queue.** The Krea face paint goes through the ComfyUI queue, which is often busy with cinematics' LTX jobs. `comfy.run` waits.

## Files to read first
1. `docs/team/README.md`, then `docs/team/hero_male.md`.
2. `tools/assets/hero_male_body.py`, `hero_male_head.py` (search for `SPLIT_Z`, `scalp(`, `beard(`) and `hero_male_face.py`.
3. `godot/src/Actors/People.cs` (search for `Hero(`, `HerPart`, `HisTone`, `HisEyes`) and `HerPose.cs`.
4. For the next steps: `tools/assets/heroine_hair.py` and `tools/assets/heroine_outfits.py`.
