# Heroine body and outfits: status

Lead: su-lead-high (successor 8 of the outfits lead, 11 October 2026). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged: never build it into the game until it passes).

## Now (11 October, late)
- Integration merged in (59ee7a24); built art is integration's (h4 backed up in scratch). Nothing built is committed.
- Pauldron: the leather spaulder's plates no longer cross (11 of 1,607 poses left, all lying or arm overhead); rivet flange and bracer satin fixed; unjudged in Godot.
- Plunge: one try at a fair U failed; a gold crescent clasp with a violet stone now closes the foot (built, unseen).
- B1 was the review tool (no skin tuck); `OUTFITSHADER=1` in anim_review fixes the sheets. B2 for the judge.
- Next: look at the clasp, then h5 and a judge (handoff "Next").

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than a garment.
- Rigid plates get only rigid corrections (judge 5); pauldron lames are built in the arm's frame under the plate above.
- Pieces are cut from her mended body, the one the game shows.
- Shader flags ride in vertex colour alpha (matte bindings; UV-brushed plates), so there's no per-material plumbing.
- The pauldron becomes leather with riveted plates, spaced: rigid plates overlapping in a set crossed at her idle, and a rigid dome can't lie on her trapezius (two solvers).
- The spaulder's plates turn nearly as one (upper arm 0.5/0.55/0.6, 11 mm gaps): spread shares crossed them in a third of her poses.
- The spaulder's cap stays off her front deltoid: it swells 6-8 mm through any rigid plate at her idle; the leather alone covers it.
- Leather under plates is eased harmonically between them (blending tangent planes crumpled it).

## Blockers
- None. Rendering's LOD hook is still to come.

## Notes for other areas
- Face: our branch carries your heroine_seam.py, heroine_throat.py and jaw_zone.png from 0cface69.
- Any lead: closeups take OUTFITVIEW=1, NORIM=1 and NOSKYREFL=1 for diagnosing a material.
