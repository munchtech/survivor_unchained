# Heroine body and outfits: status

Lead: none (successor 29 finished its fixed list on 18 October 2026). Handoff: `docs/handoff/outfits.md` "Paused here". Branch: `worktree-agent-a5ca10091b08dc429`.

## Now (18 October): fixed list done, merge request sent
- G3L2 glove merged with F1. Triage at 1:1 closed 7 of 8 old items. The owner closed the stockings item; the Arcanist's made boots PASS; at the Look rig, the Ranger's leather roughness floor PASSES and the Warden's steel is closed as known at the round cap.
- Next body build: the fingers (DIP joint toward the knuckle, a flatter proximal section; numbers in the handoff), bundled so refits and legal run once.

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than a garment.
- Thick sheets under thin bindings poke through where the edge turns: skive the sheet first (EDGE_SKIVE).
- The leotard is one piece (route (a)): no separate gusset edge anywhere in view.
- Rigid plates get only rigid corrections (judge 5). Since the helpers, one-blend pieces are put back on one blend after the split (`rigid_again`), with leather riveted on a plate's blend riding it.
- Pieces are cut from her mended body, the one the game shows.
- Shader flags ride in vertex colour alpha (matte bindings; UV-brushed plates), so there's no per-material plumbing.
- The pauldron becomes a leather spaulder with riveted bronze plates (judge 8: design passes). Its leather ends inside the bands' ends: past them, its corner hung off her arm through two solvers.
- The clasp is gold, 100 degrees round the foot. Held at 58 mm it climbed the U and read as a lining.
- A pale line seen only under lookdev's rim light is a sub-mm ridge: test with `NORIM=1` before a geometry hunt.

## Blockers
- None. Rendering's LOD hook is still to come.

## Notes for other areas
- **Face:** under lookdev's back rim light, a thin pale line runs across the front and top of her left shoulder, from the leather's neck end toward her neck. It vanishes with `NORIM=1` or `LIGHTS=side`, so it is a sub-millimetre ridge. It is very likely the edge of your shoulder-and-neck graft (Mesh_1 in heroine.glb, from heroine_head.py). Evidence: the outfits scratchpad's `o\lt\cmp.png` and `o\solve1\result.md`.
- **Animation:** her body has folded slivers at the top of each armpit: glTF x ±0.15-0.17, y 1.43-1.45, dihedrals 77-180 degrees beside 36-45 mm joining edges. `mend_folds` leaves 9 folded. They are not visible from above.
- **Male hero:** `heroine_outfits.py` is still built for her body alone. Any body parameter must keep `rigid_again()` and the helpers' split after the pieces are made.
- Any lead: close-ups take OUTFITVIEW=1, NORIM=1 and NOSKYREFL=1 for diagnosing a material.
