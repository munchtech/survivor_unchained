# Heroine face, hair and creation's Look: status

Branch `worktree-agent-a2d632df7c7f21ec0`, not merged (unjudged skin and the Look rig mixed in). Handoff: `docs/handoff/face.md` (successor 9's "Start here" first).

## Current state (12 October)
- **Hair swing:** run, stop, get_up, get_up_back and throw (ponytail, long) passed hair judge hj2. The throw braid is fixed: the spine colliders now span her back. Death fails. Its root cause is the chain solver (no bending resistance, length corrections turning into velocity, a hold that pulls into her back), plus a shader that moves the hair but never turns it. A new solver is ported (solvers 2 and 3, WIP); the shader rotation is next, then a judge over all clips, then a hair-only branch for merge.
- **Skin (round r8, unjudged):** ears re-toned from the render; their chroma and hue now hold on all ten faces. Sunborn's under-jaw chroma still fails (+46%). The neck-length sheet v2 is built (today, -1, -2, -3 cm, a notch tick on each). Next: judge j7, then the sheet for the owner.

## Key decisions (why)
- Ears are corrected from the render, not the paint. The paints already matched; the miss comes from lighting and tone, so the loop closes on what shows.
- The spine colliders are capsules across her back. Her back is wide and flat, and balls down her spine left her sides open.
- Hair ships on its own branch: only judged work goes to integration.

## Notes for other areas
- **Animation:** hold every hair re-shoot until the face lead names the hair merge; then re-shoot every clip that shows her hair.
- **Rendering:** the Look's edge lamp now defaults to 1.3 m (GameFront `edgeUp`). It goes to your notes once judged.
- **Dev switch:** `--preset ID --eyes ID` now sets a face in `--quick` play.
