# Handoff: performance lead

For a fresh successor. Read `docs/team/README.md`, `RESUME.md`, `OWNER_NOTES.md`, then this page, then `docs/team/performance.md`. Older method and numbers: `docs/PERF_AUDIT.md`; the round before this one is in git history of this page (680f2a0d).

Written by agent ad57a6dd0798688d7, 2026-10-06, wound down early (the owner ran low on usage). Before it: a0eb8c612c94d4aa5.

## The owner's words

- "the pixel blur while running is that intentional or something we can fix?", "we are blurry when moving in active action gameplay." She sent zoomed crops of her head while running: smeared and blocky.
- "the filter to see through trees and stuff is also a little pedestrian in its pixelation."
- "we are striving for perfection." Her detail is never traded for frames.

## The brief (main session)

1. Find the true cause of her blur; measure motion vectors per material, TAA history and jitter, the camera's judder.
2. Make her crisp in motion without bringing back shimmer on grass and specular. One A/B batch with `--perf-flip` and frame times: (a) correct motion vectors for vertex-animated materials, (b) TAA off with MSAA 4x and a light post AA, (c) FSR2 at native. Send before/after crops of her sprinting at 1080 and 1440, plus grass and crowd in motion, with a recommendation. Choose an AA that the coming hair pass can build on.
3. Replace the see-through dither with a designed one: a soft, feathered, round cut-out round her, smooth and stable in motion, no screen-door, working under the chosen AA. Arena art (paused) owns the trees: note the change for them.

## Found: the true cause (measured)

- **The fight steps at 60 Hz with no interpolation** (`WorldScene.Step`); the owner plays at 2560x1440, **164 Hz**, quality High, native (her settings.json). Drawn from the last step, she stood still for a frame or two and then jumped a step, while the camera follows smoothly.
  - `--probe` at a run, `--fixed-fps 164`: her chest shook **3.3 px rms frame to frame (worst 4.9)**. At 60 Hz it doesn't happen, which is why no shot ever showed it (every shot tool runs `--fixed-fps 60`).
  - Knock-on effects: TAA rejects history on her when her speed changes every frame (its disocclusion test compares velocities), so her hashed-alpha hair shows raw: the "blocky"; her hair's sway (HairSway, per frame) got jerked each step, so its uniform-driven offsets jumped and its motion vectors were wrong by the jump: the "smear".
- **Fixed (bb86717b): `Interp`** draws her, the camera's target, the HUD under her, the crowd, projectiles and moving pickups between the last two steps. Judder **0.02-0.05 px**. Tests 762 green. Smoke shot looks right.
- **Godot 4.5's motion vectors (read from its source):** the vertex shader runs a second time with the previous TIME, model matrix, skinning and multimesh data. So TIME-driven motion (grass and kit wind, the hair's breath of air, fur) is correct. What is wrong:
  - per-frame **uniforms**: hair `sway`/`head`/`chain`, grass `centre`/`pusher` (much smaller now that she moves smoothly);
  - the **crowd's VAT MultiMesh slots**: filled in order each frame, so every death or spawn shifted later bodies (and all corpses) a slot, and each got its neighbour's place as "last frame": wrong vectors in a horde every frame. Fix written, not run (below).
- Godot TAA (`taa_resolve.glsl`): Catmull-Rom history, 1/16 feedback, AABB clip sized by velocity, velocity-change disocclusion, no sharpening.

## In progress: branch `perf-seethrough-wip` @ 4b95fa43 (compiles; never run)

- **See-through:** `shaders/kit.gdshader` opens a round window round her: measured on screen in metres at her distance, clear to 1.45 m, feathered to 2.5 m, only what stands nearer the camera than she does and above her ankles. The piece is cut in its own (opaque) pass; the feathered rim is drawn again translucent by a next pass (`KitLook.Rim`, the same code with `REVEAL`, blended; copies far from her line of sight are culled in its vertex stage). It opens only in the camera's own view (global `view_from`, set in `Game._Process`), so trees keep their whole shadows. There is a TEMPORARY `--see-through old` switch (view_from.w = 2) for before/after pictures: remove it once shot.
- **Crowd:** `VatCrowd` keeps each body in its own slot by key (`CrowdView.KeyOf`: the same for the living and its corpse); freed slots are emptied and kept a frame before reuse.
- **Risks to check first:** shader compile errors; the rim's seam where the opaque pass hands over (SSAO isn't on transparents); under TAA/FSR2 the rim has no motion vectors of its own, so tree texture inside the rim may smear a little; the cost of the next pass (flip it).

## Next

1. Merge `perf-seethrough-wip` into your branch, build, and run batch 1 in one Godot turn: `scratchpad/perf5/batch1.ps1` with `runs1.txt` (scratchpad is `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad`). It does `--import` first (needed: newer assets are missing from this worktree's `.godot`), then her running at 164 Hz at 1440 and 1080 for TAA (with and without interp), SMAA, FSR2 and MSAA; Godot's motion-vector view; crowd frames; still-camera shimmer; the house (`waystation --at 9,25.6`) and pines (`verge --at -137,14.5`) see-through, old and new; and dense-fight `--perf-flip aa:smaa` and `aa:fsr2`. `crops.py her|sharp|shimmer` makes the crops and numbers. Look once.
2. Recommend the AA. My expectation, to be checked against the shots: with the stepping gone, keep a temporal AA (TAA, or FSR2 at native if it's sharper and cheap) as the foundation for hair. Hair cards with hashed/dithered alpha need temporal resolve. Give hair exact vectors next: previous-uniform pairs in the hair shader, or move the sway onto bones. MSAA + SMAA is crisp but leaves hashed hair noisy and Medium (no MSAA, closed by the owner) aliased.
3. Send the main session the crops and frame times with that recommendation and a strict 1:1 self-critique. Then show arena art the see-through.

## Gotchas

- Worktree setup: `godot/assets` is a junction to `public/assets` (skip-worktree); `override.cfg` sets the perf user folder; `.godot` and generated `.import` files were copied from a0eb8c's worktree (`scratchpad/perf5/copy_imports.py`). Don't commit `*.import`/`*.uid`.
- Don't build while a batch runs: every launch loads the DLL from `.godot/mono/temp/bin/Debug`.
- A shot saves the previous frame's image; `Shots.Her` is this frame's place (off by one frame, fine for crops).
- Isolation: git and bash must stay inside this worktree; PowerShell's .NET calls use a different current directory (use full paths).

## Collaborators

Main session (merges, relays the owner); arena art (paused; owns the trees' look); the face lead (hair; her import settings stay lossless); the writer.

HANDOFF READY: docs/handoff/performance.md on worktree-agent-ad57a6dd0798688d7 (see the commit below)
