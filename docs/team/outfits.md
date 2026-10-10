# Heroine body and outfits: status

Lead: su-lead-high (third lead, 10 October 2026; wound down by the owner). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged in full: never build it into the game until it passes).

## Now (paused)
- Gussets as skin-tight pieces and every rim bound: strip frames fell (Warden 47 to 6, Arcanist 603 to 29, Reaver 31 to 13); areolas 0 to 1 px; 0 bare at rest. Judge 1 failed g2 on tucked skin seen in motion (worst: the Ranger's pant leg and corset in chain_haul/chain_strike; a bump of skin at the gusset-to-string junction; slits at the Warden cups' inner edges and the Reaver band) and on binding corners (Warden pauldrons, Arcanist plunge, Ranger lames).
- Weights are ruled out as the cause (two trials, 5-10%).

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than the garment (the Arcanist's V foot: 1.9 to 2.9 cm).
- Gussets and strings tuck her skin and follow it, as stretched cloth does.
- The check runs against this lead's own worktree build and import, never the main checkout's.
- Unchecked work stays on a WIP branch: the coordinator's refits build `heroine_outfits.py` from integration.

## Next
1. A max solver on tucked skin in motion (rule out a rig fold first).
2. The binding sweep: smooth rims, closed loops, rounded corners.
3. Tailoring (judge 1's list in the handoff); the Ranger's right knee piece (24 mm through at knee 90, from animation).

## Blockers
- None. `--helpers` stays off until animation's helper bones pass their judge.

## Notes for other areas
- Animation (ae2a9884e3e51609c): `--helpers` stays off until your garment-against-skin weight check; garments keep the weights of the skin under them (gussets now take each line's own).
- Rendering (a7afb4d33cdd5efba): one TAA out-of-gamut pixel at a gold edge against the background (Warden vault, chest view, frame 10, near (591, 323)).
- Face (abe65bc929823a791): her sculpted nipple bumps sit 8 to 9 mm above the paint's areola centres; the outfits now tuck the bump fully under covering pieces.
- Any lead: `tools/scratch/outfits/` scripts take `OSCR` (a scratch folder) and find their worktree themselves.
