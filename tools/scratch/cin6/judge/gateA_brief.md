# Judge: the AAA ship gate over the Prologue cinematics (cinematics 3), effort max

Context budget: 200k

You are a fresh judge for Survivor Unchained, a dark-fantasy ARPG (Godot). Return a written verdict only; edit nothing. Worktree: C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92 (frames in godot/.shots/). Open each image once. Keep the verdict under 80 lines.

## The gate (the owner, 18 October)
For each frame: **"would this frame ship in a AAA game as it stands?"**, judged as a player at 1:1 on the whole picture. A NO fails the shot regardless of any checklist. The owner, watching these cinematics today: "that quality is nowhere near what we are supposed to be pushing for." Calibrate on the owner's three frames first (all NO): godot/.shots/o1_lying_neck_adams_apple.webp (her lying, camera over a stretched masculine throat, blown highlights on the cups), o2_hunched_at_log.webp (head collapsed onto her chest, gray unlit back of the neck, a pauldron that reads as floating, the braid through her cup), o3_spin_profile.webp (a snap spin at the log; flat waxy skin, mouth hanging open). Judge at the frame's own size; nothing enlarged.

## Frames
One still per shot, from a real-play run of the current build (godot/.shots/playc2_<cine>_s<shot>_1.png, 1920x1080). Shot notes: godot/data/cinematics/<cine>.json, each shot's "note" (grep `"id": "<shot>"` and read only the note line if a frame's intent is unclear). YOUR SET: C01 (14 stills: playc2_c01_s0_1 ... s12_1; ls playc2_c01_s*_1.png) and C02 (12 stills, playc2_c02_s*_1.png).

Known and already being fixed elsewhere (don't count against a shot, but say if it is the ONLY thing failing it): her neck shape/Adam's apple, her temple hairline, the braid's dark tab under her ear (a touch-up lead has them). C01 s3, s6 and s10 are being restaged now (o1-o3); judge them anyway.

## For each shot, one line
`<cine> s<id>: YES | NO - <the main reasons, most visible first> - cause: STAGING (camera, framing, blocking, timing, the shot's own lights) | ART (her skin, face, hair, outfit materials) | ANIM (a clip's pose or motion) | ENV (terrain, trees, water, sky, props) - fix: <the concrete change if STAGING; else what the other area must do, or CUT if the shot can't be saved and the scene reads without it>`.

Then a short summary, grouped by owner area: STAGING (cinematics' own, with fixes), ART, ANIM, ENV, each listing the frame ids with one line each, so they can be routed or cut. Then: how many YES, which NOs are cinematics' own (STAGING) with their fixes, and the 3-5 non-staging causes that fail the most shots (so the owner can decide where to spend). Be honest and strict: the bar is a shipped AAA game's cinematic, as a player sees it.

Also answer, from the close-ups of her face in your set: is her flat, waxy skin her material or the shots' light? Say what in the frames tells you (e.g. the same flatness under different keys, specular sheen without pore breakup, no subsurface warmth at the edges of shadows), in 3-4 lines.
