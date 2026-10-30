Context budget: 150k
Item: sb3-p6-end

You are a code solver for the Storybook 3 lead (agent a46800cd8f93a7ecb; your final message returns to your lead; do NOT message main). Work in `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\storybook-2` (branch storybook-2). `godot/assets` is a junction: never `git stash`, `git reset --hard`, `git checkout .`. Commit only your own paths, never `git add -A`, never the stat-only modified `.import` files. End commit messages with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. No team onboarding. GPU (only if you inpaint): `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take gpu "storybook3: p6 seam"`, given back at once, ComfyUI models freed after. Never kill processes by name. Pictures: half-size copies or small 1:1 crops only.

## Context
SB00's ink plate p6 ("The traveler", storybook 71-81.5 s) is built by `tools/storybook/ink_layers.py` / `ink_build.py` / `ink_r2.py` into `tools/storybook/out/ink_layers/p6/` (+ `layers.json`), state picks in `tools/storybook/ink_picks.json`, wired into the player by `tools/storybook/sb_wire_ink.py`, and shot by `bash tools/storybook/sb3_shoot.sh <round>` (frames at 1920x1080 in `tools/storybook/out/sb3_frames/<round>/`). Look at round r3's `sb_sb00_80.50.png` (p6's last key, camera x 3550 zoom 1.25) for both faults.

## Fix
1. **The traveler vanishes at the end.** In the r3 frame at 80.5 s the walk2 silhouette stands half against the dark far bank and tree reflection and looks see-through. The beat is "out of the fire's warm ring into the cold dusk": the last image of p6 is a small dark hooded figure clearly silhouetted against the pale river. Move walk2's spot (and the slide's end) so the whole figure, hood to feet, sits against the pale water surface in the final frame at the last key, with clear pale water on both sides, feet on the near shore stones or at the water's edge; make sure the silhouette is fully opaque (check its alpha and the crossfade's end value) and keep its scale plausible for that distance. Keep the step bob and slide timings otherwise.
2. **A hard vertical seam in the far hill.** At about frame x 740, y 270-560 (1920x1080, the r3 80.5 s frame) a straight vertical edge cuts the hill and tree mass: a layer boundary (the far layer's cut or fill edge, or the near layer's), visible at 1:1. Find which layer and fix it at the source (extend/feather the fill so no straight edge exists anywhere a camera key shows it; re-run the plate's checks: rest diff < 2/255, 0 unfilled px at every key). Check the other p6 keys for any other straight edge while you're there (numerically: long straight alpha or value discontinuities in the composited frames).

Then `bash tools/storybook/sb3_shoot.sh r4` (it takes and gives back the godot turn itself; ~5 min). Look once at a half-size copy of the 80.5 s frame to confirm both fixes.

## Report (under 20 lines)
What each fault was and the fix, the checks, the r4 output folder, commits, token use.
