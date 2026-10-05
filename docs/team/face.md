# Heroine face, hair and creation's Look: status

Branch `worktree-agent-a833b7942e978d994`. The handoff is `docs/handoff/face.md`.

## Current state (2026-10-05)
- **v7 art is committed:** her face and nine presets' faces, each from a TRELLIS 2 head of its own Krea portrait, laid on her MakeHuman head (`face_wrap.py`).
  - Hers is the target `portrait-heroine`. Each preset's is a key, `face_<id>`, painted from its own portrait.
  - Sheets (worktree `godot/.shots`, uncommitted): `sbs_default_v7.jpg` (her, in four columns) and `presets_v7c.jpg` (ten faces under their references).
- **heroine.glb and the outfits are not committed.** The main session rebuilds them with `heroine_outfits.py --body` from this worktree's `tools/comfy/out/heroes/heroine_built.blend`.
- **Still open:**
  - Tail's hairline edge is still hard at the close-up.
  - A pale smudge sits under Saffron's eyes.
  - Some lip lines are a little crumpled on the presets.
  - The preset shots catch blinks (it's chance, not a fault).
  - At play zoom her face is only about 15 px. The far-zoom deepening is now stronger.

## Key decisions
See the handoff's Decisions.

## Next
1. After the main session's refit, rerun UI design's `heroine_paint.py` (`brows.png`) and the creation portraits.
2. Tail's hairline: soft fine cards over the edge. Saffron's cheeks.
3. Play-zoom review (`--auto toward`).

## Notes for other areas
- **Main session:** the presets' slider shapes are gone. Each preset is its own face key, so merge the art and the refit together.
- **UI design:** shot flags `--turn DEG` and `--auto toward`. `People.SkinTone` eases darker tones toward white less than before.
- **Male hero:** the eye shader's catchlight is smaller, its limbal ring darker, its specular dimmer (the shader is shared).
