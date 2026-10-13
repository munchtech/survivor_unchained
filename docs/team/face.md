# Heroine face, hair and creation's Look: status

Ship branch `face/ship` @ 096c7a8c (one squash on integration 02fb2a8b; 886 tests pass): MERGE REQUESTED 13 October. Work branch `worktree-agent-a2d632df7c7f21ec0`. Handoff: `docs/handoff/face.md` (successor 19's "Start here").

## Current state (13 October)
- **Face ship:** every part passed its judges (s1, rj1-rj7). Last item, the turned jaw's orange-brown wedge at the Look, was the skin shader's warm shade tint on her jaw's underside (not the ear map, not the paint); fixed by `shade_thin` 0.75 (rj7 PASS). Residual, not blocking: moonlit and fey's under-jaw a touch deep at 2x (lightness, a later fill pass).
- **Next (owner said yes):** the smile pass (upper teeth, mouth interior, open-smile corner wedges, the at-rest lip fix for five faces carried into the smile shapes; the soft version ships unless the new one clearly wins). Then hair: hard pale scalp edge at the hairline, pale scalp slivers above the ear, strands reading as cracks over the ear and scratches across the cheek, the review tool rendering her bald.

## Key decisions (why)
- Her chin is raised 12 degrees at the Look: the idle bowed her head, and from above her lower face read short.
- The warm shade tint stays (it keeps her shade from the night sky's blue) but thins where she faces down: a cap on its saturation took the fill's warmth from the front view too.
- Lip WIP (sculpt, recolour) stays off the ship: the owner turned down fuller lips; the smile pass revisits the five faces.

## Notes for other areas
- **Everyone (from face/ship):** her head and skin shader carry new uniforms (key/soft/edge/sky tone, shade tint and `shade_thin`, ear shade map, teeth `seep`); `body_lift` and her head's tones apply only under the Look's rig (`People.HerLookRig`), so play and cinematics keep integration's face tones. Picture switches: `--head-rig off`, `--ear-ao off`, `--skin-set PART:uniform=v`.
- **Animation:** the greatsword pommel at the close-up camera and the cinematic hand on the hilt are yours (coordinator). The review tool renders her bald on the face branch (face fixes it in the hair round).
- **Body/outfits:** the faceted chest in the cinematic close is yours.
