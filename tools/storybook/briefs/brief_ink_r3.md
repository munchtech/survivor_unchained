Context budget: 200k
Item: sb3-p5-drowned

You are a code solver for the Storybook 3 lead (agent a46800cd8f93a7ecb; your final message returns to your lead; do NOT message main). Work in `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\storybook-2` (branch storybook-2). `godot/assets` is a junction: never `git stash`, `git reset --hard`, `git checkout .`. Another helper commits `godot/`, `docs/` and `tools/storybook/sb_*` at the same time: commit only your own paths (`git commit <paths>`), never `git add -A`. End commit messages with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. No team onboarding. GPU: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take gpu "storybook3: ink r3"` (exit 1 = busy: `--wait 600`), give it back the moment each batch ends; free ComfyUI models when done (POST /free). Never kill processes by name. Look at pictures only as half-size copies (`python tools/half.py`) or small crops, sparingly.

## Context
SB00's ink test plates are built by `tools/storybook/ink_post.py`, `ink_layers.py`, `ink_build.py`, `ink_comfy.py`, and round 2's `ink_r2.py` (read these, not history). Output `tools/storybook/out/ink_layers/<plate>/` + `layers.json`; state picks in `tools/storybook/ink_picks.json` (the wiring reads it). Keep everything not named below as it is.

## 1. p5 drowned, round 3 (the lead's verdict on round 2)
Round 2's pasted figures read as zombies in modern T-shirts, sweatpants and shoes, flat mid-value slate cut-outs on the bank, the same 7 figures repeated: far from the plate's hand. Round 1's inpaint drew hooded living villagers. Narrow-mask inpaint fails with Krea (pale blobs); broad regions work. So, one-hand route:
- Build an init: the clean plate (round 2's seed-31 refill) with the drowned roughed in as layout: dark figure masses (near-black navy rags) standing IN the ditch water on both sides of the road, water to the shins, 12-17 of them at varied heights, spacing and turns, nearer ones bigger, each with a small pale face and pale hands (your round-2 figure cut-outs, darkened to navy with only face/hands kept pale, are a fine source; vary their flips and scales so repeats don't show).
- Then ONE broad-mask Krea img2img over both ditch bands (one mask a ditch or one band covering both, feathered; EXCLUDE the overturned cart and the road's centre), at denoise 0.5, 0.6 and 0.7 x 3 seeds, with p5's own prefix/style text (from its ink_jobs prompt) and: "drowned corpses of medieval peasants standing upright in the flooded ditches along the road, water to the shins; soaked torn linen shifts and wool tunics in rags clinging to thin bodies, barefoot; bare heads, long wet hair plastered flat and hanging over the face in strands with river weed; pale dead faces and hands catching the moonlight; arms hanging slack; heads tilted, every face turned toward the road; motionless, waiting". Nothing modern: no shirts with sleeves cut like T-shirts, no trousers, no shoes, no hoods.
- Composite back inside the mask, post with the shared ink post, and BAKE the drowned into the road layer (they don't appear or disappear; the pull-back reveals them). Drop the `drowned` state from `layers.json` and from `ink_picks.json` (set `"p5": {}`), keeping the road layer's name. Keep 0 unfilled px at every key and the rest check (compare against the new posted whole).
- Sheet: one row per candidate (9), p5's lower half at rest, 1600 px wide, plus a 1920x1080 1:1 crop of the best two at the plate's final wide key. Ship the candidate YOU judge best into the road layer (criteria: reads as drowned dead at 1:1 at the wide key, drawn in the plate's woodcut hand, medieval, no repeats, no blobs), name the others, and the lead will confirm or re-pick from the sheet (keep the others re-buildable by one command line, say which).

## 2. p6 walk: one figure
The wiring alternates `walk1` (a different man in a red-lit coat, wrong for a hooded traveler) and `walk2`. Replace both with the `stand` pick (`traveler_stand_s47.png`): `walk1` = the stand drawing as is (lit by the fire on one side), `walk2` = the stand drawing as an unlit silhouette (your round-2 walk2 recipe: near-black navy, faint slate rim on the river side) at the walk2 spot by the water. Save `traveler_walk1.png`, `traveler_walk2.png`; update `layers.json` and `ink_picks.json` (`walk1`, `walk2`).

## 3. p7: build the blue rim
None of the head_up candidates turns toward the lamp (all face left, away from it). Build `traveler_blue_rim.png` (`P7_RIM = True`) and set `ink_picks.json` p7 to `{"blue_rim": "traveler_blue_rim.png"}` (drop head_up). The rim should sit on the hood and shoulder edge facing the lamp (upper right), soft, cage blue.

## 4. Provenance
Log round 2's six figure images, the seed-31 refill and this round's pictures in `tools/storybook/ink_provenance.md` (sidecars exist per picture).

## Report (under 35 lines)
Sheet and crop paths, which candidate you shipped and why, the checks, GPU minutes, token use, anything that resisted.
