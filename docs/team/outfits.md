# Heroine body and outfits: status

Lead: su-lead-high (successor 6 of the outfits lead, 11 October 2026). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged: never build it into the game until it passes).

## Now (11 October, later; successor 6)
- Two owner side-by-sides being built (h4, both on at once: PAULDRON=leather PLUNGE_TRIM=down; code defaults unchanged):
  - The simpler pauldron: a leather spaulder skinned to her (its neck end lies on her trapezius) with a bronze cap and two spaced bands riveted on; beside h3's lames, whose two idle-pose items stuck after two solvers.
  - The plunge foot: option (a), the taut-string rim, did not land (173e05e0); option (b), a white feathery trim (fur shells tuned as down), beside h3's plunge.
- Pauldron plates drawn satin (face: 5.7% of the Look's frame blew out). Fixed since judge 6, built in h4: the Ranger's pale binding line, rivets' contact shadow, B1, B2.
- Next: a judge on h4 (the side-by-sides plus judge 6's checklist), then the pauldron straps.

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than a garment.
- Rigid plates get only rigid corrections (judge 5); pauldron lames are built in the arm's frame under the plate above.
- Pieces are cut from her mended body, the one the game shows.
- Shader flags ride in vertex colour alpha (matte bindings; UV-brushed plates), so there's no per-material plumbing.

## Blockers
- None. Rendering's LOD hook is still to come.

## Notes for other areas
- Face: our branch carries your heroine_seam.py, heroine_throat.py and jaw_zone.png from 0cface69.
- Any lead: closeups take OUTFITVIEW=1, NORIM=1 and NOSKYREFL=1 for diagnosing a material.
