# Handoff: the heroine's body and outfits

From the second outfits lead (su-lead-max), 7 October 2026, handed off at about 292k. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` first, then this page, then `docs/team/outfits.md`. **Never read a whole file**: `heroine_outfits.py` is 4,000 lines. Grep, then `sed -n` the lines you need.

## The owner's words and bar
- "AAA", "never settle", "we are striving for perfection"; edges "perfectly cut and tailored professionally". Sex appeal drives it, "tho not at the cost of looking bad"; full cups with "massive cleavage" are fine; the Reaver stays near-naked with underboob.
- Coverage: "pixel perfect no extra stuff hidden at all. none. not even a few pixels". Holes and see-through are "really distracting and bad". Fit means **tighter, not bigger** (except where the check's 2.4 cm strip is wider than a garment: then just wide enough). There were never genital issues.

## Brief (the coordinator's)
Build `outfits-lead-wip`, run the motion check on all four outfits against the true baselines, keep only what passes at 1:1 in motion. Bind pauldron_l's rim. Keep `--helpers` off until the animation lead (ae2a9884e3e51609c) has verified the helper bones; then rebuild with them and rerun the check (the coordinator relays).

## Setup
- My scratch folder (`SO` below): `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\outfits\`: `setup_wt.ps1`, `cu_bind.txt`, `loops.py`, `dedup.py`, `refilter.py`, `hs/outfits.log` (the WIP build's log) and `hs/cost/sheet_<outfit>.png` (its turntables, not yet looked at).
- A new worktree: `godot/assets` as a junction to its `public/assets` (`git update-index --skip-worktree godot/assets`), then robocopy main's `godot/.godot` and main's `*.import`/`*.uid` sidecars (godot, not through the junction, and public/assets): `SO\setup_wt.ps1` (repoint `$WT`). Never commit the sidecars (line-ending churn).
- `tools/scratch/outfits/*.sh` now find their worktree themselves and take the scratch folder from `OSCR` (e.g. `OSCR=<scratchpad>/outfits bash tools/scratch/outfits/turn_build.sh`). Copy `tools/comfy/out/heroes/heroine_built.blend` (main checkout) to `$OSCR/hs/` first. **The session scratchpad is shared with other agents: keep yours in a subfolder.**
- New: `compare.py <base> <new>` (per outfit: strip and areola frames, any pixel and 6+, worst frames, tucked-skin frames); `xsection.py <heroine.glb> <outfit.gltf> <png> y,y,y` (cross-sections at the crotch, Blender axes).
- True baselines are in the first lead's scratchpad: `.../74e72383-70c7-41d5-8e96-2fad2ed58481/scratchpad/legal/base1/<outfit>/` (read-only; compare against it).

## Done (branch `worktree-agent-a1f120018d8749c97`)
- `count.py`: a lone pixel reading the very tip (red under 30) with no neighbour within 5 mm is dropped as a render artefact. On base1 it removes only the 0.00 cm pixels (Warden 18 to 8 areola frames, Stalker 8 to 6; Arcanist and Reaver unchanged).
- Baselines with that filter (frames: strip any px (6+ px), worst; areola frames; tucked seen 6+): Warden 47 (37), 46 px; 8; 12. Arcanist 603 (362), 247 px (vault_below_10); 7; 22. Stalker 84 (11), 52 px; 6; 148 (1,718 px in chain_haul_left_08: the corset's crotch parts from her and the tucked skin shows). Reaver 31 (17), 59 px; 4 (4 px); 5.
- The remaining 1 px "areola" hits at 0.87 to 0.96 cm (Arcanist and Stalker, identical frames) are the sculpted nipple bump (8 to 9 mm above the paint's centre) coming through the cup.

## Half-done: branch `outfits-lead-wip2` (heroine_outfits.py only; built once in my worktree, not yet checked in motion or seen)
1. **Rims bound** (`weld` now calls `cancelled()`: triangles the weld folded onto the same three points cancel by winding). Before, they broke the rim walk and `bind_edges` left the rim as cut: warden pauldron_l (the jagged line), vambrace_l, sabaton_r, arcanist corset, gloves, stalker bracer_r, reaver bootfur_r. All now bound; **look at them at 1:1** (close-up list: `scratchpad/outfits/cu_bind.txt`, for `closeups.sh`). Still unbound: `ranger.pauldron1` (3 broken loops, 123 to 138 mm jumps: another fault; `DUMP=ranger.pauldron1 TEMP=<folder>` on a dry build, then `scratchpad/outfits/loops.py` and `dedup.py`), `ranger.glove_l` (2 small), `reaver.cape` (one 24 mm step).
2. From the first lead: Reaver band rows from her exact section (`section()`); `COVER` lines after every build; `UNBOUND` lines with the reason.
3. Gussets (Warden, Reaver; the Arcanist's `crotch_bridge`): 1 mm under her, `hides=True, follow=True`, begun 6 mm up the cleft; back strings `hides=True, flare=(gusset width, 0.03)`; the Arcanist's V foot 0.0095 to 0.0145 half-width in both `w` and `exact()`.
4. Each nipple's bump (proud of `P_FILLED`, within 1.2 cm of `NIPPLE`) tucked fully under any covering piece (grep `bump =`).
- **COVER at rest got worse:** Warden strip 1 of 244 points bare, Arcanist 2 (both at [-0.008, 0.024, 0.925]; before 0 bare, 7.4 and 4.4 mm margins); Reaver 0 bare but 3.5 mm (was 7.5). **Why** (`roof.py`, `xsection.py`): the top of the slot between her thighs is only 4 to 8 mm wide (at |x| = 4 mm the first skin seen from below is 15 to 59 mm lower). A flat gusset 1 mm under the midline crosses the slot's walls at |x| = 6 mm, and the walls' rounded shoulders below it (strip points: |N_x| < 0.7) are bare. Hung 6 mm low, it covered them along their normals but let skin through in motion.
- **My plan for it:** make each gusset a conforming `piece()` over the strip region (|x| < 1.4 cm, |N_x| < 0.8, the strip's depth plus 1 cm either end, `slot=False`, lift 1 mm, bound, hiding), with the flared strings overlapping it; prove 0 bare and at least 2 mm margin with a dry build (`dry_build.sh <tag> --only warden`, 2.5 min), then build and run the full check (`NOIMPORT=1 OSCR=... bash tools/scratch/outfits/baseline.sh <tag> "reaver warden"` and the other pair in parallel, then `compare.py`).

## Next, in order
1. The gusset as above, then the full check against base1; keep what passes at 1:1 (look at `crops/` and `clean.sh` frames). Then the Stalker's chain_haul gap, the Warden's 1 px rim at 45° in chain_haul (2.03 to 2.19 cm), the Reaver's 1 to 4 px areola at 45°.
2. Tailoring: the new bindings at 1:1; the pauldron's crumple at the armpit and its brushing (`heroine_outfit.gdshader` line ~127: level streaks 0.55 mm apart read as scanlines); the Reaver band's Z fold; the Arcanist's boot cuffs; the Warden's cup slivers; tattoos (0.2 mm pieces that tuck her skin: make them paint or stop them hiding).
3. Distance appeal with the rendering lead. When animation sends the helper check: rebuild with `--helpers`, rerun the check.

## Gotchas
- The worktree guard refuses shell commands with variables in loops, heredocs near git, or `sed -i` on a glob: write a script file and run it. `heroine_outfits.py` has CRLF endings (the Edit tool copes; Python string replaces need `\r\n`).
- `DUMP=<piece,...>` writes npz files to `$TEMP`: set `TEMP` to a folder for that one command (turn.py keeps its state in `~/.su_turns`, so it is unaffected).
- `BOUND x n of m edge loops` now counts only bound loops.

## Collaborators
Animation lead ae2a9884e3e51609c (helpers, weights; you share the rig). Face lead abe65bc929823a791. Rendering lead a7afb4d33cdd5efba (owed: one TAA out-of-gamut pixel, Warden vault, chest view, frame 10). Reports go to the main session.
