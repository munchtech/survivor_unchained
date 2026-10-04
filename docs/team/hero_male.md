# Male hero: status

Agent ae2de192cce8298ca, branch `worktree-agent-ae2de192cce8298ca`. Paused for the owner's usage limit, with the drive at 99%.

## The brief (from the main session)
Make the man the player can be the heroine's equal: AAA, with soul, rugged and attractive. Build him from the owner's AccuRIG actor (`C:\Users\munch\Desktop\ComfyUI_00008-reduced\`) in phases, each checked in full-resolution renders:
1. Inspect the actor.
2. Make him playable: animation, skin, eyes, a head with expressions, hair cards with physics, and a beard.
3. Hook him into the game: the Look step, save and load, and lookdev.
4. Cut his four callings' outfits from his own body, in a male outfit tool. Don't edit `heroine_outfits.py`.

## What the actor is
- **The source.** The owner made Krea 2 turnarounds of a bald bodybuilder (`Krea2_turbo_00237-240`). TRELLIS 2 turned them into `ComfyUI_00008.glb`: 700k triangles, with 4K paint, ORM and normal maps. A reduced copy (600k) was rigged in AccuRIG with a full CC_Base skeleton of 101 bones, posed in a T-pose.
- **Missing.** The FBX has no paint, its UVs no longer fit the paint, and it has no expressions: the ExpressionFrameMap is AccuRIG's empty default.
- **Quality.** The body sculpt is good: defined muscle, hands, feet and ears. The face is crude: the eyes and lips are moulded shut and painted on. The paint is flat, with a dark patch on the throat and a smooth "doll" crotch.

## Done (tools committed; outputs not committed because of the disk)
- **`tools/assets/hero_male_body.py`** builds his body (about 85 s).
  - It welds AccuRIG's split points, reduces him to 110k symmetric triangles and unwraps him afresh.
  - It bakes his 4K paint and 4K normal map from the full sculpt.
  - It puts him on the UAL skeleton the build_heroine way, at 1.98 m (she is 1.87 m).
  - Checked in Blender: the bake keeps every muscle. With his arms down the shoulders deform acceptably, with a slight crease at the rear deltoid.
- **`tools/assets/hero_male_head.py`** builds his head. It is `heroine_head.py` adapted:
  - a MakeHuman man's head shaped by `FACE`: square jaw, cheekbones, heavy brow, deep-set eyes;
  - placed on his face (scale 1.018, 3.3 mm from his sculpt) and sewn to his own neck between `SPLIT` and `CUT` (checked: a clean join);
  - the painted-on buzz cut cleared from his scalp;
  - 65 shape keys: the heroine's sliders, plus `chin_cleft` and `brow_ridge`, and her expressions;
  - eyes, brows, lashes, teeth and tongue.
  - It writes `godot/art/people/hero.glb` and `head_tex/hero_*.jpg`. These are local and not committed yet (large).
- **`tools/assets/hero_male_face.py`** is `heroine_face.py` with his prompt: a rugged, clean-shaven warrior with grey eyes. The flat drawings are made. The Krea paint was stopped before it ran.

## Next
1. Run `hero_male_face.py`, then re-run `hero_male_head.py`; check the face at full resolution.
2. Then build the rest:
   - his iris (a `heroine_eyes.py` variant);
   - in `heroine_skin.gdshader`, a default-off macro normal map (he needs his baked normals);
   - in the same shader, a stubble and shaved-scalp shadow layer;
   - in `People.cs`, Hero, HisHair, HisFace and HisOutfit; `Loadouts.HisBody = "man"`;
   - lookdev via `BODY=hero`.
3. Hair cards and beards (a `heroine_hair.py` variant), then the four outfits.
4. Commit `hero.glb` once there is disk space.

## Rebuild
1. `blender -b --python tools/assets/hero_male_body.py -- <fbx> public/assets/people/UAL1.glb C:/Users/munch/Desktop/ComfyUI_00008.glb tools/comfy/out/heroes/hero_male_body.blend`
2. `blender -b tools/comfy/out/heroes/hero_male_body.blend --python tools/assets/hero_male_head.py -- tools/comfy/out/heroes/hero_male_built.blend godot/art/people`

## Agreed with others
- **Animation (a1e3002b800ee55ac)** will build his own library with `build.py --body hero`: `hero.res` with the prefix `him/`, and `HisClips` mirroring `HerClips`. They need his skeleton dumped by `anim_skeleton.gd` once `hero.glb` is pushed, so ping them. Until then her clips work as a stopgap if HisPose offsets the pelvis.
- **UI design (ac76f400913a109cd)**: sent the proposal. It is `Body = "man"`, a `BeardStyle` string, and face sliders in her dictionary. Not yet answered.

## Gotchas
- **Fresh worktree.** Junction `godot/assets` to `public/assets`, and copy the `.import` and `.uid` files from the main checkout. The Godot import dirties many `.import` files: never commit those.
- **MakeHuman skins.** Every MakeHuman skin, male or female, has a buzz cut painted on its scalp; `scalp()` in the head tool clears it.
- **Scratch file names.** Don't name a scratch script `inspect.py`: it shadows Python's own module.
