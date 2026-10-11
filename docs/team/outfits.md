# Heroine body and outfits: status

Lead: su-lead-high (successor 7 of the outfits lead, 11 October 2026). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged: never build it into the game until it passes).

## Now (11 October, night)
- Pauldron: the leather spaulder reworked for judge 7 (no crumple between plates, the cap's rim bound and clear all round, cap set on top of her shoulder and lifted, hem on her arm, satin bracers, smooth brushing, bronze rivets). Godot close-ups look clean at 1:1; three small checks left, then h5 and a judge. Not yet the default.
- Plunge: h3's bound plunge stays (trim dropped); its foot is next (one try, else a small arcane clasp).
- Open: B1, B2.

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than a garment.
- Rigid plates get only rigid corrections (judge 5); pauldron lames are built in the arm's frame under the plate above.
- Pieces are cut from her mended body, the one the game shows.
- Shader flags ride in vertex colour alpha (matte bindings; UV-brushed plates), so there's no per-material plumbing.
- The pauldron becomes leather with riveted plates, spaced: rigid plates overlapping in a set crossed at her idle, and a rigid dome can't lie on her trapezius (two solvers).
- The spaulder's cap stays off her front deltoid: it swells 6-8 mm through any rigid plate at her idle; the leather alone covers it.
- Leather under plates is eased harmonically between them (blending tangent planes crumpled it).

## Blockers
- None. Rendering's LOD hook is still to come.

## Notes for other areas
- Face: our branch carries your heroine_seam.py, heroine_throat.py and jaw_zone.png from 0cface69.
- Any lead: closeups take OUTFITVIEW=1, NORIM=1 and NOSKYREFL=1 for diagnosing a material.
