# Heroine face, hair and creation's Look: status

Agent a6007bf07fd45ab0d, branch `worktree-agent-a6007bf07fd45ab0d` (took over from a833b7942e978d994 at v7).
The handoff is `docs/handoff/face.md`.

## Current state (2026-10-05)
- **v8** answers the main session's review of v7 (the batch: `godot/.shots/sbs_default_v8.jpg`, `presets_v8.jpg`, uncommitted).
- **heroine.glb and the outfits are not committed.** The main session rebuilds them with `heroine_outfits.py --body` from this worktree's `tools/comfy/out/heroes/heroine_built.blend`, and merges the art and the refit together.

## Key decisions (why)
- **The wrap keeps her inside inside** (`face_wrap.py`): points no ray leaves (her mouth's walls, nostrils, where her lips meet) are carried along, not laid on TRELLIS's skin, and set back 1.5 mm behind her outside. v7's presets had their mouth's walls laid on their cheeks: Saffron's "smudges", holes in every preset's paint, Sunborn's jaw seam and a ridge along every preset's jaw.
- **Eyes at least 0.89 of hers by the lids' ring** (was 0.86): measured through the pupil, Fey's came out 0.84 at 0.86.
- **Her head's skin matched to her face and her body** (`heroine_head.py` `matched_base`): a harmonic colour field over her head's points. MakeHuman's paler, greyer skin was the band across her neck.
- **Preset skins from their portraits** (each portrait's skin against hers, as a tone on her paint): Vixen and Moonlit fair; Doe, Wildling and Hard-won rose; Saffron warm; Sunborn brown, with Brown lightened to `#ba7f5e` (Sunborn on Deep was four to six times darker than her portrait).
- **Her hairline blended, not hashed** (`heroine_hair_soft.gdshader`): her scalp's cap and the fine hairs at her hairline. Hashed alpha does not move, so the TAA kept its dots: a speckled band with a hard edge. Her scalp's shade is even (no stubs) and starts 4 mm under her hairline.
- **Shots hold her eyes open** (`--open-eyes`): v7's shut eyes were blinks caught.

## Next
1. The main session's review of v8; then its refit and merge, then UI design (its new lead, aa1f430bd64b8d1ce) reruns `heroine_paint.py` (`brows.png`) and the creation portraits: message them when her head lands.

## Notes for other areas
- **Everyone taking pictures of her:** `--open-eyes` (lids up, eyes ahead), `--unshaded` (paint without light), `--eyecycle paint,#rrggbb,...` (her irises dyed in turn, one a picture).
- **Male hero:** the eye shader (shared) has `iris_light`, and its catchlight moved to sit with the key light's highlight.
- **Main session:** her body's paint is padded between its islands now (no red bleeding into her seams as it shrinks).
