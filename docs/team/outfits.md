# Heroine body and outfits: status

Lead: su-lead-high (fifth lead, 11 October 2026; handed off at its budget). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged in full: never build it into the game until it passes).

## Now (paused, 11 October, after judge 3: FAIL)
- g9 built (unjudged in full): rigid pauldrons (Warden domes pass), plunge as one U (fails), Ranger boots constructed (sole cup, welt, stacked heel; right direction, read as rubber), skin paint fixed (the build blend had lost the graft and head images). Animation's thigh fix took ranger chain_strike tucked6 from 25 frames/9884 px to 2/53 and removed the vault thigh hole.
- Next: the judge 3 list in the handoff (plunge on the flattened pattern, Ranger pauldron gash and UVs, Warden corners and raw cup edge, Arcanist front and gusset, left-breast bump, boots).

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
