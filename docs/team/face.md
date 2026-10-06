# Heroine face, hair and creation's Look: status

Agent a2f7b0f1283f6144a, branch `worktree-agent-a2f7b0f1283f6144a` (took over from a6007bf07fd45ab0d at v8e).
The handoff is `docs/handoff/face.md`.

## Current state (2026-10-05)
- **v9** (merged): her lips meet again (v7's `portrait-heroine.target`).
- **Portraits** (merged): each face's portrait is its own face, skin and eyes (`creation_portraits.py` passes `faceShape`); Sunborn, Moonlit and Saffron have theirs.
- **v9b, half done** (this branch; code only, no refit needed yet): the white slivers along her lips at a turn are gone (her skin's sheen occluded by her AO; they were the rim light on her lips' inner linings, not teeth: `teeth_probe2.py` sees no tooth from ±30 degrees or ±20 up and down, any face). Her body's normals joined along her middle where they split (`heroine_head.py`, 797 corners). **The dark band down her throat under a side light is still there**: neither the join nor rounding her throat's normals (tried, reverted) moved it. It comes with the key alone, not its shadow; a clay render under a side light (`side_light.py`) shows her upper chest's normals broken into faceted shards, which are the "pale patches on her upper chest" in the Look, not her body's paint.
- **v10 in hand:** her paint's fine detail from the view that sees it best (`heroine_face.py`, committed, not yet laid on the faces): her mid-scale grain 0.87 of her portrait's (0.65 at v9) at the size her face is at the Look.
- **Open, worst first:** v10's grain on all ten faces; preset tones (Sunborn 1.13/1.37/1.70 lighter than her portrait in r/g/b under a white rig; her own 12% redder than hers); hair cards as broad strokes (no clumps between a strand and a card); her catchlight a blob the size of her pupil; brows faint and grey; sloe and peat dark; a pale wedge under her jaw at a turn.
- **heroine.glb and the outfits are not committed.** The main session rebuilds them with `heroine_outfits.py --body` from this worktree's `tools/comfy/out/heroes/heroine_built.blend`, and merges the art and the refit together.

## Key decisions (why)
- **Her normals joined along her middle** (`heroine_head.py`, where hers differ from the joined smooth ones by over 8 degrees within 2 cm of it): her body's halves meet unjoined there and her own normals were split (26 degrees at a point). (It did not cure the throat band.)
- **No sheen where her AO is deep** (`heroine_skin.gdshader`): the rim light's reflection on her lips' linings showed as white slivers at a turn.
- **Fine detail from one view, broad colour from all** (`heroine_face.py`): blended as one, her front's grain was averaged with the side paintings' over her cheeks and cut by `match`: her paint held half her photograph's grain.
- **The wrap keeps her inside inside** (`face_wrap.py`): points no ray leaves (her mouth's walls, nostrils) are carried along, not laid on TRELLIS's skin, and set back 1.5 mm behind her outside. v7's presets had their mouth's walls laid on their cheeks: Saffron's "smudges", holes in every preset's paint, Sunborn's jaw seam and a ridge along every preset's jaw.
- **Eyes at least 0.89 of hers by the lids' ring** (was 0.86): measured through the pupil, Fey's came out 0.84 at 0.86.
- **Her head's skin matched to her face and her body** (`heroine_head.py` `matched_base`): a harmonic colour field over her head's points. MakeHuman's paler, greyer skin was the band across her neck.
- **Preset skins from their portraits** (each portrait's skin against hers, as a tone on her paint): Vixen and Moonlit fair; Doe, Wildling and Hard-won rose; Saffron warm; Sunborn brown, with Brown lightened to `#ba7f5e` (Sunborn on Deep was four to six times darker than her portrait).
- **Her hairline blended, not hashed** (`heroine_hair_soft.gdshader`): her scalp's cap and the fine hairs at her hairline. Hashed alpha does not move, so the TAA kept its dots: a speckled band with a hard edge. Her scalp's shade is even (no stubs) and starts 4 mm under her hairline.
- **Shots hold her eyes open** (`--open-eyes`): v7's shut eyes were blinks caught.
- **The moon off her face at the Look's close-up** (`GameFront.PortraitLight`, from p > 0.5; back on in `EndCreate`): it was a fourth light, cold and flat, and its reflection a pupil-sized white blob on each iris.
- **Her head's AO baked** (`heroine_ao.png`, `ao_light` 0.55): the neck under her jaw was lit like her cheeks.
- **Paint edges eased, her jaw's underside left to her head's own skin** (`heroine_face.py`): triangle-at-a-time visibility drew a pale stair under her jaw.
- **Where her lips meet held hard to where TRELLIS's meet** (`face_wrap.py`, inner-lip landmarks at weight 5; the log's `LIPS MEET`): with her lips' linings carried, not laid on its skin, her lips parted a hair and the tips of her teeth showed.
- **Her own face is v7's wrap** (`portrait-heroine.target` from 1970f5c3): even held so, v8's wrap left her lips half a millimetre apart at her middle and her teeth showed; v7's own wrap laid none of her inside on her skin (only the presets' did). The presets keep v8's wraps (each key is its target less hers, so their faces do not move with hers).

## Next
1. The main session's review of v8; then its refit and merge. It runs the portrait steps itself (`heroine_paint.py brows`, `creation_portraits.py`, the Look shots: UI design is paused), which also fill creation's missing Sunborn, Moonlit and Saffron portraits. Message the main session, not UI design.

## Notes for other areas
- **Everyone taking pictures of her:** `--open-eyes` (lids up, eyes ahead), `--unshaded` (paint without light), `--debugdraw Lighting` (any of Godot's views), `--eyeparam name=v,...` (her eye shader's numbers), `--eyecycle paint,#rrggbb,...` (her irises dyed in turn), `--skinparam name=v|#rrggbb,...` (her skin shader's), `--rig-white` (the Look's lights all white), `--no-taa`, `--mipbias B`.
- **Male hero:** the eye shader (shared) has `iris_light` (0.3: irises showed two and a half times too light against the skin) and `wet`/`wet_rough` (the cornea's sheen). The eye colours in looks.json are dyed for it, and his own `HisEyes` is the new flint.
- **UI design (when back):** the eye colour beads are darker now (looks.json `eyes`), as the irises render; the Brown skin is lighter.
- **Main session:** her body's paint is padded between its islands now (no red bleeding into her seams as it shrinks).
