# Heroine body and outfits: status

Lead: su-lead-high (successor 5 of the outfits lead, 11 October 2026). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged: never build it into the game until it passes).

## Now (11 October; judge 6 on h3: FAIL, fixes committed, h4 not built)
- The Ranger pauldron, rebuilt as bands round the arm (third solver), passed most of judge 6. Left: lame 1's back corner and the dome's medial stand-off at the game's idle pose (a solver is on them), and leather straps at the lame ends.
- Passed judge 6: the Reaver binding, the rivet shape, B4, and every judge 5 pass. Fixed since, not yet built: the Ranger's pale binding line, the dome's brushing, the rivets' contact shadow, B1 (elbow), B2 (breast fold).
- The Arcanist plunge foot: one more solver (taut-string rim); if it doesn't land, a feathery trim, judged side by side for the owner.

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
