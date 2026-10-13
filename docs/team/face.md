# Heroine face, hair and creation's Look: status

Branch `worktree-agent-a2d632df7c7f21ec0`, not merged (unjudged skin and the Look rig mixed in). Handoff: `docs/handoff/face.md` (successor 9's "Start here" first).

## Current state (12 October, late)
- **Hair swing:** hair judge hj4 passed 15 of 18 clip sheets. Run, stop, death and get_up_back pass in every style, plus throw ponytail and long and get_up long. While she's down, the hair now settles into a procedural drape, and the swing blends back as she rises. Still failing: get_up ponytail and braid (the held drape lies down the front of her throat) and the throw braid's kink. A fix pass is running. The hair-only branch's files are prepared; it ships once a judge passes every clip.
- **Skin:** judge j7 passed her chin raised 12 degrees at the Look (her lower face now matches the portraits), the ear helix tones and the 1.3 m edge lamp. It failed the owner's neck discoloration on the fair faces. The root cause is found: the body tone was fitted where the warm fill lit it, so the key light alone left her grey. The refit is in progress (r10, r11), then judge j8.
- **For the owner, once judged:** the neck-length sheet v3 (ticks from her skeleton, ratios measured). Also Sunborn's warm under-jaw: accept it as firelight, or one try at browner shade.

## Key decisions (why)
- Her chin is raised 12 degrees at the Look: the idle bowed her head, and from above her lower face read short.
- Ears are corrected from the render, not the paint. The paints already matched; the miss comes from lighting and tone, so the loop closes on what shows.
- The spine colliders are capsules across her back. Her back is wide and flat, and balls down her spine left her sides open.
- Hair ships on its own branch: only judged work goes to integration.

## Notes for other areas
- **Animation:** hold every hair re-shoot until the face lead names the hair merge; then re-shoot every clip that shows her hair.
- **Rendering:** the Look's edge lamp now defaults to 1.3 m (GameFront `edgeUp`). It goes to your notes once judged.
- **Dev switch:** `--preset ID --eyes ID` now sets a face in `--quick` play.
