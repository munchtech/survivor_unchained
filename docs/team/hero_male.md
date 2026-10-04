# Male hero: status

Agent ab82cbe99e2937ddd, branch `worktree-agent-ab82cbe99e2937ddd` (took over from ae2de192cce8298ca; read `docs/handoff/hero_male.md`).

## Current state (paused for the owner, 2026-10-04)
- **In the game, gated** behind `--body hero`, as before. The committed `hero.glb` is still the predecessor's (e7709bd). My rebuilt head is not committed yet: its face tone is unfinished.
- **His head tool, reworked this session** (`tools/assets/hero_male_head.py`):
  - **Skull rounded:** less `head-square`, plus `head-oval`, and Taubin smoothing over the cranium only, so the crown's facets are gone.
  - **Body paint and relief cleaned** by the new `tools/assets/hero_male_skin.py`, judged in 3D, not texture space:
    - the sculpt's white flecks and its hair's dark streaks are removed;
    - the neck is evened where the sculpt's hair lay;
    - the relief's stray slopes on tiny islands are flattened, and the hair strands moulded into his neck are blurred out. These caused the "hard collarbone highlights": they were relief, not paint.
  - **Seams:** the neck, graft and head are brought to one tone (`one_tone`), so there's no line at his nape or under his jaw.
  - **Ears:** MakeHuman's own `ears` group keeps scalp clearing and face paint off them. This fixes the white fleck and the stepped patches.
  - **Face paint kept to his face:** off his scalp and the temples above his ears, where Krea painted pale stubble. It's found through MakeHuman's UV layout (`face_paint_uv.npz`, written by `hero_male_face.py`), so repacking the head never misplaces it.
  - **Brows marked** in `hero_shadow.png`'s blue channel, so the shader can dye them to his hair colour (not wired yet).
  - **Nose shading kept to the nostrils:** red flecks from heroine_face_fixes on his cheek are given back.
  - **Tangents exported** with him.
- **Skin values:** `rough=0.62, shine=0.32` reads right in lookdev. They're not yet in People.cs or lookdev.gd.

## Next (exact)
1. **Fix the last build.**
   - It fails in `heroine_face_fixes.lips`, because no red lip is found: `one_tone` (with the region weights just added to `hero_male_skin.broad`) moved his lips' hue.
   - Fix: run `one_tone` after `heroine_face_fixes.fix()`, on the fixed paint, or keep the lips (`lips` group) out of it.
   - Then judge his face against his neck unlit (scratch `albedo.py`). His Krea face is olive beside the tan neck.
2. Render lit sheets in Godot (front, 3/4, side, back, chest, full body). Commit `hero.glb` only once it's better everywhere than e7709bd.
3. Put his skin values in People.Hero and lookdev.gd. Wire the brow dye and stubble (`People.HisShadow`).
4. Merge the animation lead's `worktree-agent-a435f4dd0ac80df75@72ab9a8`: his own `him/` library and `OwnClips.Him` in People.Hero.
5. Hair and beards, the base garment, the four outfits, then the Look step.

## Key decisions
- **Body paint is cleaned in 3D** (centimetre cells through him). His unwrap's islands are too small to judge a texel by its neighbours in the texture.
- **One skin tone from neck to scalp,** with his face keeping only a little of its own broad colour.
- **No new committed art until it's better than the last everywhere,** at full resolution.

## Collaborators
- **UI design (a69858664f1d3dd29) agreed the male Look fields:**
  - `heroes.male` in looks.json, the same shape as hers plus `beards` [{id, name, words}];
  - `BeardStyle` (string) on CharacterData, CreationChoice and PersonSpec;
  - `HairStyle` from his `cuts`; `Face`, `Eyes` and `Paint` as hers;
  - cameos in `art/ui/create/male/`.
  Tell them when `heroes.male` and his builder land.
- **Heroine face (ade92e8285938438f):** import `face_shapes.py` (SLIDERS, REACH, slider_keys, SCULPTS). Don't copy it. Skip the Neck group. Check jaw_width ±2 and face_shape on a man. Final list to follow.
- **Animation:** his library is done. See Next 4.
- **Legal (aa12c130ddf4b904c):** answered the content and sources questions. Send renders per outfit as they land.

## Notes
- Scratch helpers: `ld.py` (Godot lookdev), `sheet.py`, `albedo.py` (unlit Blender), `probe.py`, `front_proj.py`. They live in this session's scratchpad, not the repo.
- The rebuilt-but-uncommitted head is in the worktree (`godot/art/people/hero.glb`, `tools/comfy/out/heroes/hero_male_built.blend`).
