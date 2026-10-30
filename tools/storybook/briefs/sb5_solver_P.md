You are a medium solver for the Storybook 5 lead. You own plates p1 and p5 of SB00 (the ink lore intro). Both get new sources from ChatGPT, which the lead has picked. Your final message returns to the lead. First read `tools/storybook/briefs/sb5_solver_common.md` and follow it. Two other solvers have finished, so you're the only one editing now, but leave their p0/p2/p3/p3d/p4/p6/p7/p7u work alone. The r9 frames are `tools/storybook/out/sb3_frames/r9/sb_sb00_<t>.png`.

Sources (ChatGPT, the owner's account; copy them into `tools/storybook/out/sb5/` first): `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\afafb81e-73db-4471-9550-8c24bff6c27c\scratchpad\storybook5\chatgpt\out\`.
- **p5: `p5_E2.png`** (1536x1024; fallback `p5_E1.png`). It's an edit of `p5_R1.png`, the source of the current p5, and registers at shift 0. It has three cressets on single posts, the fourth light as p7's round strap-basket lamp on a chain from the black sky, and the nearest drowned with pale dead faces.
- **p1 door: `p1_D2.png` (open) and `p1_D2_shut.png` (shut)**, both 1677x938, registered at shift 0. Open: a rune lintel, the doorway lit gold from deep inside, a huge chain down the rock at left, a torch column far up right. Shut: a rectangular slab in the opening, gold seams, a chain across the slab bolted to the jambs. Fallback pair: `p1_D1.png` / `p1_D1_shut.png` (2031x774).

Add both to `tools/storybook/ink_provenance.md` in the existing ChatGPT entries' format: OpenAI ChatGPT image output, owner's account, 29 Oct 2026, no credit needed, the prompts are in the storybook5 scratch `prompts.md`, and how we re-drew them.

## p5 (56-71 s): rebuild from E2 and restage without the close
1. Re-carve E2 through the same route that made the current p5 from R1 (`ink_recarve.py`: f1 flatten, Krea img2img 0.40 at the carve size, the night post; `ink_rc_build.py` for the layers). Two cautions:
   - **Don't re-apply `ink_rc_fix.py`'s p5 "cages" inpaint.** That inpaint is likely where the toy goblet baskets came from.
   - **Check the re-carve keeps three things:** the cressets (single straight posts; no legs, no goblets), the hanging basket lamp and its chain, and the dead faces. If Krea redraws any of them (at 0.50+ the dead turned into villagers before), composite those regions back from a lighter pass, or from the flattened source run through `ink_post`.
2. **Glows:** cold light from each cresset onto the snow around its post, the lamp's white-blue core, a broken vertical reflection, and rings under the lamp.
3. **Staging: CUT the close** (the judge: "the wide pushed past its detail", 2.35x). p5 opens on the wide no tighter than ~1.3x zoom, as long as the carving is never shown above ~1.2x its own px. A slow push toward the fourth light runs to ~63.5 s, then the pull back to the whole ford road by ~69 s (the line "Now the drowned stand along the ford road" starts ~63.5).
4. The wagon and the drowned stay as in E2. Remove any hat.

## p1 (2.5-15.5 s): the forge, then a HARD CUT to the new door plate
1. **Keep the forge part of the current p1** (the smiths at the anvil, the legion, 2.5 s to about 7.5 s). The judge: the torch procession at 4.0 s (x 1290-1520, y 520-700) stands among the legionaries at a sixth of their height, with flames bigger than its bodies. Mask the procession layer below the ledge line while the forge is in frame, or bring it in only once the camera has passed the ledge.
2. **Hard cut at about 7.5 s** (pick the moment between the subtitle lines; check the cue times in sb00.json) to a new door plate built from D2. Make it either a separate plate (`p1d`, in PLATE_ORDER and COVERS so the cues keep their absolute times) or a hard switch inside p1, whichever is cleaner in `sb_wire_ink.py`.
   - Run it through the shared post (`ink_post`, and a light Krea re-carve only if it's needed to match the film's hand; ChatGPT's own carving may already pass).
   - Show it at no more than ~1.2x its own px. Keep the lintel's top at least 40 px below the letterbox in every frame.
   - The camera: a slow push or slight drift, nothing more.
3. **The shut:** the slab slides in from behind the right jamb and lands at 13.8 s absolute (plate t 11.3 now), on the drum hit that's already wired.
   - Build the slab layer from D2_shut's slab with the chain painted off it (inpaint or clone).
   - Put a foreground layer of the right jamb (cut from the open plate) in front of it, so the slab really comes from behind the jamb.
   - The open doorway's gold dims as the gap narrows, to thin seams.
   - **On the drum hit**, hard-switch to the full D2_shut picture (the chain across the slab snaps into place on the beat; no crossfade), and keep its gold seams with a slow, small flicker that dies down by 15.5 s.
   - If the slab won't sit cleanly behind the jamb, fall back to: the open plate, then a short push, then the hard switch to shut on the drum. Tell the lead which one you used.
4. Keep the old doorway layers (curve, curve_glow, slab) out of the new door beat.

## Shoot
Round `r10p`: FROM=0 TO=17 TIMES="2.6 4.0 6.5 7.4 7.8 10.5 12.5 13.6 14.0 15.0" and round `r10p5`: FROM=56 TO=71.5 TIMES="56.5 59 62 63.5 66 69.5 71", under the shoot lock.

Context budget: 200k
