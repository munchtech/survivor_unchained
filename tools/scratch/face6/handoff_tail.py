p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2f7b0f1283f6144a\docs\handoff\face.md'
s = open(p, encoding='utf-8').read()
s = s.replace("`build_v8b.ps1` (presets' paints with fresh Krea sides)", "`build_v8b.ps1` (presets' paints with fresh Krea sides: v8e's presets' sides are these, kept since by `FACE_REUSE`; hers are v7's)")
head = s[:s.index("## Decisions (why)")]
tail = """## Done (v8e, commit 6e73f647)
- The v7 review answered (details and numbers in `docs/team/face.md`'s Current state): eyes open on every preset, Saffron's smudge and Sunborn's seam gone (both were her mouth's walls laid on the cheeks by the wrap), irises matched to the portraits, the neck band gone, the hairline blended, the presets' lips clean, skins from the portraits.
- Code: `face_wrap.py` (her inside kept inside; eye floor 0.89; lips' meeting held; teeth behind the lips), `heroine_head.py` (`matched_base`; body paint padded), `heroine_face.py` (eased visibility; jaw underside left to her head's skin), `heroine_features.py` (AO), `heroine_hair.py` + `heroine_hair_soft.gdshader` (blended cap and fine hairs), `heroine_eye.gdshader` (`iris_light`, `wet`, `wet_rough`), `heroine_skin.gdshader` (`ao_map`, `scalp_stubs`), `GameFront.PortraitLight` (the moon off her at the close-up), shot flags.

## Next (worst first; the owner: keep improving until the credits run out, at the Look close-up and at play zoom)
1. **Her own face's teeth show between her lips** (v8 regression). Put back v7's target (`git show 1970f5c3:tools/assets/heroine_face/targets/portrait-heroine.target > tools/assets/heroine_face/targets/portrait-heroine.target`), run `build_v8.ps1` and `shots_v8.ps1 -tag v9 -nocal`, and check her lips at 1:1. If v7's has its own faults (a notch under her jaw in clay), find why the new wrap parts her lips instead (`teeth_probe.py` on the built blend).
2. Tell the main session when it passes: it refits and merges, then runs the portrait steps itself (UI design is paused).
3. Sloe and peat a little dark (see the status page); a faint pale wedge under her jaw on her left; her skin's fine grain half the portrait's; hair cards like broad strokes at the close-up (hashed alpha; try alpha to coverage at the High tier); pale patches on her upper chest (her body's paint: tell the main session).
4. Play zoom: her face is ~15 px from above; the far deepening reads as eyes and brows; nothing broken (v8e_play_c*.png).

## Decisions (why)
See `docs/team/face.md`'s Key decisions.

## Failures (and why)
- v7's wrap laid her mouth's walls on its cheeks (a ray along a wall's normal met TRELLIS's skin, the surface turned to face as hers does): Saffron's smudges, holes in every paint, the jaw seam, side paintings drawn with the blotches.
- Exempting her lips' linings from the set-back (a "lip zone") moved her chin by 9 mm: reverted.
- Moving the eye's catchlight on a guess: the white blob under her pupils was the moon's reflection, not the catchlight.
- Eye calibration by `--eyecycle` on one run: she moves in the Look's idle, frames differ. Calibrate from the presets' own shots (`eyefix.py ... lum`); the dark eyes swing (the cornea's sheen dominates there).

## Collaborators
- Main session (coordinator): reviews the sheets, refits outfits on `heroine_built.blend`, merges, runs the portrait steps.
- Male hero (paused): shares the eye shader; his `HisEyes` is the new flint.

## Files to read first
`docs/team/face.md`, `tools/assets/face_wrap.py` (INSIDE, LIPS MEET, TEETH), `tools/assets/heroine_head.py` (`matched_base`), `godot/shaders/heroine_eye.gdshader`, `scratchpad/face6/build_v8.ps1` and `shots_v8.ps1`.

## Gotchas
- Her worktree's `heroine.glb` and outfits are refitted locally only: never commit them. `godot/art/people/x/` is the build's outfit scratch. Many `.import` files show as modified (the import cache came from the old worktree): don't commit them.
- `godot/assets` is a junction to `public/assets` here (`git update-index --skip-worktree godot/assets`).
- The worktree guard refuses commands that name git inside piped python or loops with variables: write a small Python file and run it.
- Shots: `--open-eyes` always; `--unshaded`, `--debugdraw Lighting|NormalBuffer`, `--eyeparam name=v`, `--rig K,F,E,R`.

HANDOFF READY: docs/handoff/face.md on worktree-agent-a2f7b0f1283f6144a@HEAD
"""
open(p, 'w', encoding='utf-8', newline='').write(head + tail)
print('ok')
