# Creatures and models: status

The creatures and models lead (branch `claude/creatures-boar`). The brief: replace every model that isn't ours with our own, in the order of `docs/art/MODELS_TO_MAKE.md`, starting with the boar (a launch blocker: its file is "personal use only").

## State (5 October)

- **The boar: the pipeline runs end to end** (dry run on a first sculpt); the real sculpt is in TRELLIS now.
  - `tools/creatures/concept.py`: pictures from Z-Image-Turbo (Apache-2.0, no revenue cap), each with its record (prompt, seed, model hashes, date).
  - `tools/creatures/sculpt.py`: a picture through TRELLIS 2 (MIT) locally, with its record.
  - `tools/creatures/boar_build.py` (Blender, stage by stage): prep, form (the body as one closed solid, what we remake cut away, smoothed), low (QuadriFlow quads, ~4.8k), dress (our tusks, tail, crest and tuft cards; one atlas), bake (paint, normals, position/normal/tangent/part maps, AO), rig, export (glTF with separate textures).
  - `tools/creatures/boar_paint.py`: our paint in texture space (coat, grizzled back, cheek blaze, mud, scars, ivory; bristles drawn along the coat's lie into paint and normals).
  - `tools/creatures/quadruped.py`: the four-legged rig (shared with the wolf later) and the pose solver; `boar_clips.py`: trot, gallop, idle, paw, gore, flinch, dazed, three deaths. `clip_sheet.py`: sheets for review.
  - `tools/creatures/bristles.py`: the drawn bristle atlas.
- **Game side (in, inert until the model lands):** `vat_normal.gdshader` (VAT_NORMAL variant), roles of length 0 play the whole clip, per-role looping, a beast's Pace and ChargePace, the `charge` role while lunging, the `stun` role while stunned.

## Key decisions

- **Pictures from Z-Image-Turbo, not Krea 2.** Legal 5(g) ranks a cap-free local model above Krea; a Krea-made boar would only join the list of things to replace.
- **The sculpt comes from a clay maquette picture.** TRELLIS turns painted fur into a crust of flakes that no remesh cleans; a grey clay maquette of the same beast gives clean sculpted forms (crest spikes, folds, scars). All colour is our own paint over it.
- **A new four-legged rig, not the old boar's skeleton** (its clips are part of the personal-use asset). Agreed with animation (a7dd95d00c4a6a017): I key the first pass, they own the clips after.
- **Budget (agreed with performance, a0eb8c612c94d4aa5):** about 7k VAT vertices, 2K albedo and 2K normal map (VRAM-compressed files beside the glTF), `VAT_NORMAL` as a compile-time variant, bristles on their own cut surface.
- **QuadriFlow refuses meshes with zero-length edges** (smoothing leaves some): the low stage works at 100x scale with those collapsed.

## Next

1. Clay sculpt (boar_clay side 33) through form, low, dress, bake, paint, rig; read its landmarks off its pictures.
2. Clip sheets, then into Godot: horde at the game camera (`--horde 60:boar`) and close up (Old Tusk); perf-flip numbers to performance.
3. Paperwork: `docs/legal/records/BOAR_RECORD.md`, ASSET_PROVENANCE (CR-02 retired), CREDITS.
4. Then the Ford-Warden, the average man and woman, the should-makes (Vonnra flagged by crafting, ab0b263c720bdbda8).

## Notes for other areas

- **Animation:** rig conventions as agreed. The rig path comes when the clay boar is rigged.
- **Crafting:** Vonnra noted (should-make, after the blockers).
