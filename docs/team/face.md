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

## Big expressions (open 0.6+, laugh, snarl, pucker): fix when a scene first uses them
Closed as known (face 28, 17 October, the coordinator agreed). No screen or scene shows them yet. The Look has no expression preview, and HerFaceLife drives only blinks and lids. The cinematics' face cues go no higher than mouth_open 0.25, smile 0.15 and frown 0.2. Measured: at that range, on every face and at the jaw and mouth sliders' ends, no lower tooth or gum point comes within 1 mm of her chin skin. The lead of the first scene that opens her mouth wider (shouts, love scenes) picks these up, judged at that scene's camera at 1:1:
1. Own's chin dot at open 1.0: the lower gum's front 0.85 mm through her chin.
2. The back lower teeth read mustard or khaki (open 0.6, laugh).
3. A throat crescent under the chin as the jaw opens (worst on Saffron).
4. A chocolate band on the inner lower lip (Saffron and Sunborn; faint on fair skin) at snarl, laugh and open.
5. Hard-won's snarl teeth read as a grille in the night close-up.
6. Dirty corners at laugh 0.8.
7. Bright broken lower-teeth dashes at open 1.0.
8. A grey cheek streak from the corner at open 1.0 (own, Fey).
9. A chalky rim on own's upper lip at pucker.
- **Verdict and sheets** (1:1, 16 Oct): `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\007ccb1a-862a-405f-908e-2b7c3e433488\scratchpad\f27\j1\verdict.md`. The shoot script is `..\f27\tri.ps1`.
- **Item 1's start:** `gum_low()` in `tools/assets/heroine_mouth_inner.py`, kept but NOT hooked. It pushes the lower teeth and gum back in the teeth's mouth_open key, to keep 2 mm behind her chin. It also scales the mouth_height slider's teeth key by how far her skin follows the slider at each height. Run it alone with `gum_low_file(glb, out)` (about 90 s). The unjudged build is `..\f27\chin\g1.glb` (on the pre-G3 body), with its log in `dbg.txt`. Caution: its push reaches 7.6 mm at open 1.0, driven by the mouth_height Low slider (Sunborn, own). It applies to every face, so the front teeth may look sunk. Judge that before hooking it, or move the Low case into a corrective key.
- Also closed: hooking `heroine_mouth_seal.py`, since nothing it fixes shows at 1:1.
