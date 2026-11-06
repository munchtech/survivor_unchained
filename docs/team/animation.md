# Animation: status

A1 Stage B (her core motion rebuilt on body B; branch `motion-a1`, Marionette branch `motion-a1`). Handoff: `docs/handoff/animation.md` top block. Earlier status (A's clips, Oct) is in git history; it no longer applies to B.

## State (6 Nov)
- **P4 pipeline built:** Kimodo (prompts encoded once, GPU path when RAM is short) -> takes scored by the bible's numbers -> SOMA npz source (committed) -> retarget onto B through `tools/body/rig/*.json` (Marionette `tools/motion/`) -> foot lock -> `p4.py build` -> `p4_pack.sh` -> B plays P4 clips over the bridge clips by name. A shape change re-runs it.
- **Warden slice, idles and gaits:** six clips built; judge round 1: town idle and town walk PASS WITH FIXES, fight idle, armed walk and both runs FAIL. Round-3 fixes running (grip on B, sheath height, the bible's layers in the core, re-shoots).
- **Arm-hold blend retired on B** (the owner, 5 Nov night); holds are clip data.

## Key decisions
- Clips are data: specs + generated sources are the truth; built clips are outputs (why: B's shape still settles; never a redo).
- Contact polish (hands on the body, arm clearance) waits for the milestone shape pick; weapons into her are never held (0 mm).
- Kimodo RP checkpoint only; MotionBricks never steered by its evaluation-only samples.

## Next
Judge round 2 on the idles and gaits; the actions (s2b: swings retimed to R8.2, dash, hit, death, get-up, the Flare press) with contact frames as data (`godot/data/anim/her_events.json`) for the C2 build lead; `STAGE B SLICE READY`.

## For other areas
- C2 build (item 14): swing contact frames will be in `godot/data/anim/her_events.json` (`{"fps": 60, "clips": {name: {"contact": f, "hold": [a, b], "cancel": f}}}`), agreed through main.
- Body (P1): after a shape change, tell A1; it re-runs `rig_map.py`, `p4.py build`, `p4_pack.sh`.
