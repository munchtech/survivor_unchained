# Heroine body and outfits: status

Lead: su-lead-high (successor 6 of the outfits lead, 11 October 2026). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged: never build it into the game until it passes).

## Now (11 October, evening; judge 7 on h4)
- Pauldron: judge 7 picks the leather spaulder with riveted bronze plates (PAULDRON=leather) over h3's lames, after fixes (the cap's buried neck edge, crumpled leather between plates, the cap's stand-off, blocky brushing). Then the owner's side-by-side.
- Plunge: the white feathery trim failed (faux fur, W at the foot, too much skin); judge 7 says show h3's bound plunge, fixing its foot (or a small clasp). Code kept behind PLUNGE_TRIM=down.
- Passed: the Ranger's pale neckline line. Open: B1, B2 (mending before cutting didn't cure B2 and broke the Warden's cups; now off).

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than a garment.
- Rigid plates get only rigid corrections (judge 5); pauldron lames are built in the arm's frame under the plate above.
- Pieces are cut from her mended body, the one the game shows.
- Shader flags ride in vertex colour alpha (matte bindings; UV-brushed plates), so there's no per-material plumbing.
- The pauldron becomes leather with riveted plates, spaced: rigid plates overlapping in a set crossed at her idle, and a rigid dome can't lie on her trapezius (two solvers).

## Blockers
- None. Rendering's LOD hook is still to come.

## Notes for other areas
- Face: our branch carries your heroine_seam.py, heroine_throat.py and jaw_zone.png from 0cface69.
- Any lead: closeups take OUTFITVIEW=1, NORIM=1 and NOSKYREFL=1 for diagnosing a material.
