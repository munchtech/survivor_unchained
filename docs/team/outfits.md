# Heroine body and outfits: status

Lead: none (paused 11 October 2026; successor 9 handed off). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged: never build it into the game until it passes).

## Now (11 October, evening): PAUSED by the owner, no successor
- h5 judged (judge 8, `O2\h5\verdict8.md`): FAIL as rendered, both designs pass. The leather spaulder beats h3's lames, and the clasp stays gold. B1 and B2 PASS with the game's shader.
- After h5, unjudged: the clasp's fixes are done (horns on the binding, tapered, seated 1 mm with the cloth cut under it). The spaulder's fixes are partial, with two regressions. The ordered list is in the handoff's "Next".
- Built art is uncommitted in the worktree on purpose (h5, plus the clasp8 Arcanist).

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than a garment.
- Rigid plates get only rigid corrections (judge 5); pauldron lames are built in the arm's frame under the plate above.
- Pieces are cut from her mended body, the one the game shows.
- Shader flags ride in vertex colour alpha (matte bindings; UV-brushed plates), so there's no per-material plumbing.
- The pauldron becomes leather with riveted plates, spaced: rigid plates overlapping in a set crossed at her idle, and a rigid dome can't lie on her trapezius (two solvers).
- The spaulder's plates turn nearly as one (upper arm 0.5/0.55/0.6, 11 mm gaps): spread shares crossed them in a third of her poses.
- A rigid piece close on cloth must be checked in Godot's idle: the clasp at 0.4 mm took the cloth's lumps through it; the cloth under it is now cut away and it sits at 1 mm.
- The spaulder's cap stays off her front deltoid: it swells 6-8 mm through any rigid plate at her idle; the leather alone covers it.
- Leather under plates is eased harmonically between them (blending tangent planes crumpled it).

## Blockers
- None. Rendering's LOD hook is still to come.

## Notes for other areas
- Face: our branch carries your heroine_seam.py, heroine_throat.py and jaw_zone.png from 0cface69.
- Any lead: closeups take OUTFITVIEW=1, NORIM=1 and NOSKYREFL=1 for diagnosing a material.
