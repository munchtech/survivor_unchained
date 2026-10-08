# Heroine body and outfits: status

Lead: su-lead-max (second lead, 7 October 2026; handed off at about 292k). Handoff: `docs/handoff/outfits.md`. Branches: `worktree-agent-a1f120018d8749c97` (finished: the check's artefact filter and tools; merge it), `outfits-lead-wip2` (heroine_outfits.py in progress: built once, not checked; never merge or build it into the game until checked).

## Now
- Every piece's rim can now be bound: the weld left folded duplicate triangles that broke the walk round a rim, so the Warden's left pauldron (the jagged line), left vambrace, right sabaton, the Arcanist's corset and gloves, the Stalker's right bracer and the Reaver's right boot fur were left as raw cuts. Built on the WIP branch; not yet seen at 1:1.
- The motion check no longer counts lone tip pixels (render artefacts). True baselines, recounted: strip frames (6+ px) Warden 37, Arcanist 362, Stalker 11, Reaver 17; areola 1 to 4 px in a few frames each.
- The gussets moved 1 mm under her (as planned) bare 1 to 2 strip points at rest, because the top of the slot between her thighs is only 4 to 8 mm wide. Next: gussets as conforming pieces over the strip region (handoff).

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than the garment (the Arcanist's V foot: 1.9 to 2.9 cm).
- Gussets and strings tuck her skin and follow it, as stretched cloth does.
- The check runs against this lead's own worktree build and import, never the main checkout's.
- Unchecked work stays on a WIP branch: the coordinator's refits build `heroine_outfits.py` from integration.

## Next
1. Conforming gussets, dry-built to 0 bare at rest, then the full motion check against base1; keep what passes at 1:1.
2. The new bindings at 1:1; `ranger.pauldron1` still unbound; the pauldron's armpit crumple and scanline brushing; tattoos.
3. Distance appeal; the `--helpers` rebuild when animation sends its weight check.

## Blockers
- None.

## Notes for other areas
- Animation (ae2a9884e3e51609c): `--helpers` stays off until your garment-against-skin weight check; garments keep the weights of the skin under them (gussets now take each line's own).
- Rendering (a7afb4d33cdd5efba): one TAA out-of-gamut pixel at a gold edge against the background (Warden vault, chest view, frame 10, near (591, 323)).
- Face (abe65bc929823a791): her sculpted nipple bumps sit 8 to 9 mm above the paint's areola centres; the outfits now tuck the bump fully under covering pieces.
- Any lead: `tools/scratch/outfits/` scripts take `OSCR` (a scratch folder) and find their worktree themselves.
