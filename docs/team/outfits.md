# Heroine body and outfits: status

Lead: su-lead-high (successor 4 of the outfits lead, 11 October 2026). Handoff: `docs/handoff/outfits.md`. Branch: `worktree-agent-a5ca10091b08dc429` (pushed; code only, unjudged: never build it into the game until it passes).

## Now (paused 11 October, handed off; judge 5 on h1: FAIL)
- Passed judge 5: the Arcanist stomach in the game look, its boning channels, nipples equal both sides, collarbone, skin paint on all four outfits.
- Open: the Ranger pauldron (two solvers ran out of context; a plan in the handoff, for the main session), rivets, Reaver and Ranger top bindings, the plunge foot (fold fitted, unjudged), animation's judge 11 items B1, B2, B4.
- Built in the worktree: h2 (animation's elbow corrective merged), unjudged.

## Key decisions
- Coverage fixes tighten, never enlarge, except where the 2.4 cm strip is wider than a garment.
- Rigid plates: corners rounded in the field before the cut, so the rolled rim runs on round.
- The check runs against this lead's own worktree build and import, never the main checkout's.

## Blockers
- The Ranger pauldron needs the main session (two solvers out of context). Rendering's LOD hook still to come.

## Notes for other areas
- Any lead: `lookdev.gd` now takes LIGHTS=mirror (the whole rig mirrored) and LIGHTS=side (two matched raking lights).
- Main session: the context hook reads this lead's budget as 120k (README's example line?), while the brief says 300k.
