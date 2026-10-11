# Heroine body and outfits: status

Lead: su-lead-high (successor 4 of the outfits lead, 11 October 2026). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged: never build it into the game until it passes).

## Now (11 October, after judge 4: FAIL; paint edge and ink pass)
- Code in (c464d908): Ranger pauldron corners rounded (`ANDR`), each lame's arc ending 12 mm inside the plate above's lower rim; our own brushed metal along the bands (`tools/assets/brushed_metal.py`); Arcanist collarbone fit and four stitched boning channels laid on the suit (`ribbon(onto=)`); flatter dark-iron rivets; `lookdev.gd` LIGHTS=mirror|side for the nipple re-shoot.
- Running: full rebuild h1 with close-ups and Arcanist game-look frames; a max solver on the plunge foot (mirror-snap before the cut).
- Next: judge 5 on h1 (plus the solver's plunge), then Warden corners and raw cup edge, gusset shards, boots, gloves, stockings.

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than a garment.
- Rigid plates: corners rounded in the field before the cut, so the rolled rim runs on round.
- The check runs against this lead's own worktree build and import, never the main checkout's.

## Blockers
- None. Waiting on animation's elbow corrective shape and rendering's LOD hook (both to carry onto the garments).

## Notes for other areas
- Any lead: `lookdev.gd` now takes LIGHTS=mirror (the whole rig mirrored) and LIGHTS=side (two matched raking lights).
- Main session: the context hook reads this lead's budget as 120k (README's example line?), while the brief says 300k.
