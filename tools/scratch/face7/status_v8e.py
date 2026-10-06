p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528\docs\team\face.md'
s = open(p, encoding='utf-8').read()
old = s[s.index("## Current state"):s.index("## Key decisions")]
new = """## Current state (2026-10-05)
- **v8e** (committed art; sheets `godot/.shots/sbs_default_v8e.jpg`, `presets_v8e.jpg`, uncommitted) answers the main session's v7 list: every preset's eyes open (0.89 to 1.05 of hers through the pupil, Blender; 0.88 to 1.08 by MediaPipe in the shots), no smudge on Saffron, no seam on Sunborn and her skin a brown of her portrait's lightness, irises within 3% of their portraits' lightness against the skin (frost blue-grey, not white; both of Moonlit's eyes alike), the neck band gone (AO under her jaw, skin matched), the hairline blended, the presets' lips clean.
- **Open, worst first:**
  1. Her own (default) face shows the tips of her upper teeth between her closed lips at the close-up: a v8 regression (v7's lips met). Fix: put back v7's `portrait-heroine.target` (from commit 1970f5c3; v7's own wrap had none of her inside on her skin), or find why her lips part (`teeth_probe.py`); then `build_v8.ps1` and shots.
  2. Sloe and peat eyes a little darker than their portraits (the dark range is not linear: v8d 3x too light, v8e 2x too dark; try the geometric mean of the two dyes).
  3. A faint pale wedge under her jaw on her left.
  4. Her skin pinker and smoother than her portrait under the Look's warm light (fine grain 0.02 against the portrait's 0.045).
  5. Hair cards read as broad strokes at the close-up (hashed alpha; lock tints).
  6. Pale patches on her upper chest (her body's paint, not the face's).
- **heroine.glb and the outfits are not committed.** The main session rebuilds them with `heroine_outfits.py --body` from this worktree's `tools/comfy/out/heroes/heroine_built.blend`, and merges the art and the refit together.

"""
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
