# Handoff: the heroine's body and outfits

From the first outfits lead (su-lead-max), 6 October 2026, wound down for usage. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` first, then this page, then `docs/team/outfits.md`.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection"; edges "perfectly cut and tailored professionally".
- Sex appeal drives it, "tho not at the cost of looking bad"; 18+. Full cups with "massive cleavage" are fine; the Reaver stays near-naked with underboob.
- Coverage: "pixel perfect no extra stuff hidden at all. none. not even a few pixels"; "showing as much as we possibly can". Holes and see-through are "really distracting and bad". Fit means **tighter, not bigger**. There were never genital issues.
- Distance: "at anything other than max zoom keep boobs and butts hd".
- Per-outfit notes are in memory (`costume-design-direction`).

## Brief (the coordinator's)
The old handoff's "Open" list, worst first: pixel-perfect coverage (tighten, never enlarge), proven by the motion check; then tailoring (the Arcanist's boot cuffs as level bands, kinks at bindings, the Warden's cup slivers in motion); then distance appeal (with the rendering lead); then confirm the chest flake. Added by the coordinator: the Warden's pauldron rim shows a jagged white sparkle line at the Look close-up (face lead's sheet `docs/team/face_sheets/v12_breast_speckle.jpg`).

## Working setup (works; reuse it)
- Worktree `agent-afb34c385770877d3`, branch `worktree-agent-afb34c385770877d3`. Its Godot import is a copy of main's `godot/.godot` plus main's `*.import`/`*.uid` sidecars (godot and public/assets), so nothing re-imports; `godot/assets` is a junction to the worktree's `public/assets`, hidden with `git update-index --skip-worktree`. The sidecars show as line-ending churn: never commit them; stage explicit paths only.
- Scripts in `tools/scratch/outfits/` (repoint paths): `turn_build.sh` (build in turns: Blender then Godot import and sheets), `dry_build.sh` (build into a scratch folder: logs, no worktree change), `closeups.sh`, `run_outfit.sh <outfit> <tag> [clips]` (the check against the worktree), `calib.sh`, `clean.sh` (the check's frames rendered clean, to read a flagged frame), `bisect.sh` and `sparkle.sh` (render switches), `bindiff.py`, `nrmcheck.py`, `glbread.py`/`tips4.py`/`tunnel.py`/`roof.py` (offline body analysis).
- The build takes 6 min in Blender. It reproduces heroine.glb byte for byte; the outfits differ only by UV float noise and 30 gold-trim triangles. A full check of one outfit is 6 min plus the count.

## The motion check was blind; fixed (4934a39e, then this branch)
- From face v10 her skin shader has its own light(); the check appended its codes inside it, the shader failed, and every count read 0. Codes now go at the end of fragment(), and lamps can't tint coded pixels.
- Its nipple search took a lump low on her right breast on the v11 body. Areolas are now found from her paint (centres level within 0.2 cm; the log warns if not).
- `DUMP=1` dumps each frame's posed body and outfit; `posed.py <dump> <view> <channel> <coded png>` casts rays through the coded pixels: skin hit first with a garment 1 to 4 mm behind means through it, and nothing behind means past its edge.
- `count.py` still counts render artefacts: pure (0, 0, 255) pixels (red under 30 is impossible for real skin at her mesh spacing). Add an isolation filter.

## True baselines (v11 body, corrected check, before any fix)
- **Reaver:** areola 1 to 4 px on her right breast at 45° in vault_back, chain_haul, bull_rush (to 0.96 cm from centre). Strip up to 59 px (chain_haul), 53 (side), 28 to 32 (vault_back from below), 5 to 17 (chain_strike), 1 to 9 (death_back).
- **Warden:** its "nipple-tip pokes" are not real: they were MSAA artefacts on steel (fixed). A 1 px rim at 45° in chain_haul (2.03 to 2.19 cm). Strip 46 and 29 (chain_haul), 6 to 21 (chain_strike), 15 to 25 (death_back from above), 8 to 10 (sit_log), 8 to 13 (vault_back below).
- **Arcanist:** strip in 362 frames, up to 41 px (axe and axes clips, from below and at 45°). A 1 px nipple poke at the cup's outline in five frames (also in the Stalker's).
- **Stalker:** strip in 11 frames; the same 1 px nipple poke.
- At rest, all strips are covered, with 4.4 to 7.5 mm to bare skin: every strip exposure happens in motion.

## Causes found
- **Reaver band:** each row lay on the convex hull of a 2 cm slice of her chest, so the rows above her nipple stood 5 to 20 mm off her upper breast; side cameras saw in behind it.
- **Strips:** gussets and back strings are ribbons, which never tuck the skin under them and take one averaged weight across their width. Skin pokes 1 to 4 mm through them as her thighs move (chain_haul), or slips out beside the back string (2.2 cm, against a 2.4 cm strip) in vault_back. The Warden's and Reaver's gussets hang about 6 mm under her (`roof_path` lowers 3 mm, then the ribbon lifts 3 mm more). The Arcanist's V is 1.9 cm wide at her crotch, narrower than the strip.
- **Nipple pokes (Arcanist, Stalker):** under a raised cup the nipple tip is tucked only partly (proximity tuck); in motion it reaches the outline by 1 px.
- **Sparkles:** MSAA shades silhouette samples with values carried past the triangle: a normal of no length or facing away, attributes out of range. Fixed in `heroine_outfit.gdshader` (5 to 0 in a test set). One TAA out-of-gamut pixel remains (chest view, a gold edge against the background): that's the rendering lead's.
- **Warden left pauldron:** the build log says "BOUND warden.pauldron_l 2 edge loops" with no binding made. Both loops were rejected in `bind_edges`, so its rim is a raw jagged cut, which is the jagged white line on the face lead's sheet. Its inner edge also crumples at the armpit, and its brushed streaks read as scanlines up close.

## In progress: branch `outfits-lead-wip` (heroine_outfits.py only; built once, then edited: build and check before merging)
- `bandeau()`: rows from her exact section at their own height (`section()`). Offline, the band now sits within 1 mm of her over the areolas.
- A coverage report after every build (`COVER ...` lines): the check's strip and areolas at rest, skin tucked as drawn, bare count and margin. Moved after the hide pass; not yet run there.
- `ribbon(hides=, follow=, flare=)` added but not yet used by any call. Next: gussets `hides=True, follow=True` and lift about 1 mm (roof_path lift 1 mm, ribbon lift 0); back strings `hides=True, flare=(gusset width, 0.03)`; the Arcanist's V and `exact()` half-width 0.0095 to about 0.0145.
- `bind_edges` prints `UNBOUND` with the reason for each rejected loop (for pauldron_l).
- Not started: the nipple bump under any covering piece tucked fully (h = 1) in the hide pass.

## Next, in order
1. Merge `outfits-lead-wip`, apply the ribbon calls above, build, read `COVER` and `UNBOUND`, and fix pauldron_l's loops. Import, then the full check of all four outfits. Iterate to zero, then the Warden's 1 px rim.
2. Tailoring: the pauldron (bound rim, the crumple at the armpit, finer brushing); the Reaver band's binding folds into a Z where the cleavage bridge meets each breast; the Arcanist's boot cuffs; the Warden's cup slivers. Tattoos are 0.2 mm pieces that tuck her skin under them (their edge ring shows): make them paint, or stop them hiding.
3. Distance appeal, with the rendering lead.
4. The chest flake: closed (not seen at 1:1 on v11 or v12 by the face lead or this lead; face handoff a54bfa4f).

## Gotchas
- The isolation guard refuses shell commands with computed command names or variables in loops: put scripts in files and run `bash file`.
- A Godot import re-imports any `.import` whose bytes changed (LF against CRLF counts).
- `OUTFIT=warden_steel` in lookdev attaches one material's mesh; `HIDE` can't reach outfit pieces.
- The animation lead's helper bones (heroine_rig.py, HerJoints.cs; worktree-agent-a9a80800a7dae2519@20bd5dc1) are inert unless the build is passed `--helpers`, so merging them changes nothing. Never pass `--helpers` until their successor sends the garment-against-skin weight check (docs/handoff/animation.md).

## Collaborators
Face lead aed215ba3ca60cc29 (sculpt; v12 skin shader: no grain below the collarbones, SSS 0.1). Animation lead (wound down; its successor owes the garment-against-skin weight check). Rendering lead a20bdef993e00f26b (AA, distance appeal; owed the TAA pixel). The main session does refits.
