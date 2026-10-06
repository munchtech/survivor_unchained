# Handoff: the heroine's body and outfits

From the main session (the coordinator), which owned this area until 6 October 2026. From now on it's a lead of its own, spawned as `su-lead-max`. Read `docs/team/README.md`, `docs/team/RESUME.md` and `docs/team/OWNER_NOTES.md` first, then this page.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection".
- Sex appeal and the male gaze are a driving factor, "tho not at the cost of looking bad". The tone is 18+.
- Full cups with "massive cleavage" are fine. The reaver stays near-naked with underboob.
- "perfect seems that look perfectly cut and tailored professionally". Edges and stitching should be crisp and tailored.
- On coverage: "if you need to hide things they need to be pixel perfect no extra stuff hidden at all. none. not even a few pixels", and "even on the nipple issues they need to be pixel perfect showing as much as we possibly can". Holes, see-through or missing chunks are "really distracting and bad".
- There were never genital issues. Fit means **tighter, not bigger**: "so we don't need to make it smaller, if anything its getting tighter?"
- Distance: "at anything other than max zoom keep boobs and butts hd". Merge pieces by material for performance, but don't trade her detail.
- Per-outfit notes from the owner's markups are in memory (`costume-design-direction`) and summarised below.

## The four outfits (tools/assets/heroine_outfits.py)
- **Warden:** formed plate cups (plunge, gold-bound, riveted), straps over the shoulders and a back strap, a war belt with a steel plate skirt, and beneath it a thong with a 3.4 cm gusset. Plate at the shoulders, forearms, knees and shins. Her right cup was once called "immaculate"; the left must match.
- **Arcanist:** a plum leather suit (a narrow V and a thong behind), sheer stockings that must never show holes, and boots. Open: the boot cuffs as level bands.
- **Stalker (ranger):** a forest-green corset, strapless and hugging both breasts, running down to cover her crotch. It's high-cut over her right hip and buttock: in front the cut runs from just shy of the crotch along her abs and round her side at the lower ribs, and behind it frames her right cheek into a thong. Her left leg wears a light yellow-green pant leg that must never read as skin. Centred lacing with skin down every lace, gold pauldron, bracer and gloves, and two leather bands on her right thigh.
- **Reaver:** near-naked, a leather band across her breasts (underboob), a loincloth panel and G-string with a 3.4 cm gusset, a fur half-cape, tattoos and bands. The band is now pulled tight (lift 1.5 mm, edges pressed on, her skin's own weights) at the same size.

## How it's built
- **Build:** `bash $TEMP/hs/turn_build.sh`. It runs in turns: Blender with `heroine_outfits.py -- godot/art/people/x --body godot/art/people/heroine.glb` on `tools/comfy/out/heroes/heroine_built.blend`, then the Godot import, then the sheets. `AFTER="cmd"` runs a command while holding the Godot turn.
- **Close-ups:** `bash $TEMP/hs/closeups.sh $TEMP/hs/cups.txt`, one line per shot: "outfit angle camz dist targetz fov name". `tools_scenes/lookdev.gd` takes `OUTFIT`, `ORBIT`, `FRAMES` and `NOJIGGLE`.
- **The breast form:** `breast_ellipsoid` and `breast_form` make a snug radial envelope from her skin (filled within 3 cm of the nipple). Plate cups sit on it (`plate_cups`), with an outline set by where the cup leaves her filled form.
- **Edges:** `bind_edges` resamples edges to faired lines on the surface. A piece's edges keep her skin's own weights, eased over 3 cm, so skin never draws away from under an edge. `steady_on_breasts` removes arm weights inside a piece; bandeaus are exempt (`UNSTEADIED`).
- **Skin under garments** is never cut; it's tucked:
  - `heroine_skin.gdshader`'s `vertex()` moves skin in by `tuck × h`, with `tuck` 10 mm;
  - `h` comes from a vertex colour channel per outfit (warden r, arcanist g, reaver b, ranger a), graded 1/3 and 2/3 over two rings from a piece's edge, and scaled by how close the piece lies (0.8 at most, none at 5 mm clear); a nipple's proud skin gets 1;
  - `People.TuckSkin` sets the channel. `lookdev.gd` mirrors it.
- **Gussets:** `crotch_bridge` and the thong and G-string gussets are 3.4 cm wide. Crotch fronts are 1.5 cm either side; what must be covered is 2.4 cm across.

## The legal motion check (the coverage proof)
- Tools are in `tools/legal/motioncheck/`; the per-outfit run script is in the scratchpad's `legal3/run_outfit.sh <outfit> <tag>`.
- It runs about 45 clips in 5 views with jiggle on. Areolas and a narrow midline strip get coded tints; `count.py` gives margins per breast and rim edge, plus any tucked skin in view.
- Bars:
  - the areola never shows (6 px is a flag, but the owner's bar is pixel-perfect, so chase smaller);
  - the strip never shows;
  - no tucked skin in view.
- Results on the current build:
  - Warden, Arcanist and Stalker pass at 6 px.
  - The Reaver now passes, with no areola in 2,180 frames. Sub-6 px traces remain at her right breast's outer and upper-outer edge in vault_back and chain_haul (45° view), and the strip shows 41 px in vault_back from below.
  - The Warden has 1–4 px of rim in chain_haul, single-pixel nipple-tip pokes, and strip slivers lying on her back.
  - The Arcanist shows the strip beside its gusset in bull_rush.
  - These are the next coverage targets: tighten, never enlarge.
- The legal lead is paused. Running the check yourself is fine; the 5-view clips read the main checkout's import, so don't rebuild there during a run.

## Refits after face changes
When the face lead changes her head or body (a new `heroine_built.blend` in its worktree):
1. Copy that blend over the main checkout's `tools/comfy/out/heroes/heroine_built.blend`, keeping a backup.
2. Merge the face branch.
3. Run `turn_build.sh`.
4. Revert `godot/project.godot` and the regenerated `.import` files (`git checkout --pathspec-from-file`).
5. Run `dotnet test`, then commit `heroine.glb` and `heroine_outfit_*.bin` and `.gltf`.

This is mechanical; the coordinator may do it. Current body: face v11 on v10b's refit (6e1b272e to 19dca97e).

## Open, worst first
1. The coverage targets above: the Reaver's right outer edge and the strip in vault_back, the Warden's chain_haul rim and nipple-tip pixels, the Arcanist's strip. Chase pixel-perfect: no exposure, and no extra coverage.
2. Tailoring polish against "perfectly cut and tailored": the arcanist's boot cuffs as level bands; any kinks at bindings; the warden's cup slivers at the top in motion.
3. Distance appeal: keep her figure and the outfits' appeal crisp at play zoom (the rendering lead is fixing motion clarity).
4. The pale flake on her upper chest, once reported from a sculpt fold; the face lead couldn't find it on v11. Confirm.
5. The deferred artists' kit (OWNER_NOTES): garment control bones on clasps, straps and laces. Only when the owner says.

## Gotchas
- Never use bare `git stash` (shared across worktrees).
- Untracked `.uid` and `.import` files block merges; move them aside (`$TEMP/hs/uid_backup`).
- Godot node names use `_` where the build uses `.`.
- A `.gltf` re-imports only when its JSON changes; the build deletes the outfits' `.md5` and `.scn` to force it.
- Windows permanently deletes long paths it can't recycle, so never move deep folders to the Recycle Bin.
- Heavy work takes turns (`tools/turn.py`: `blender` for the build, `godot` for import and shots).
