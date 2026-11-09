# performance.md history

Moved 9 Nov 2026 from docs/handoff/performance.md, nothing edited.

## Measured (164 Hz; share of pixels changing >8/255 between consecutive frames, hair / face)

| | Look pony 1080 | Look long +40 | her detail running 1440 / 1080 |
|---|---|---|---|
| TAA + MSAA, hashed (old default) | 0.02 / 0.05 | 0.03 / 0.51 | 9.58 / 9.07 (50–60 px ghost) |
| TAA + MSAA, blended, no DOF | 0.00 / 0.02 | 0.00 / 0.13 | |
| TAA + MSAA, "two" 0.5 + A2C, no DOF (new Look) | 0.00 / 0.02 | 0.00 / 0.18 | |
| FSR 2, blended, no eraser | 0.43 / 0.68 | | 11.73 / 11.42 |
| FSR 2, blended, whole hair erased (c10; dotted strands running) | 0.24 / 0.23 | 0.78 / 0.97 | 11.77 / 11.44 |
| FSR 2, "two" 0.5, eraser from 0.5 (new play) | 0.25 / 0.22 | 0.74 / 0.65 | 11.69 / 11.40 |
| same + bias 0.5 | 0.08 / 0.17 | 0.13 / 0.59 | (no gain in play) |

Fight (arena, 60 horde, 1440): ground flicker TAA 1.09–1.13 (0% hot) vs FSR 2 2.21–3.54 (1–2.8% hot): fine fizz on ground and litter, judged low severity.

## Where things are

- Scripts: my scratchpad `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\perf9\` (batch.ps1 takes the godot turn; shoot.py; `runs_c10`–`c13.txt`; `mk_c1x.py` write runs and `sheets_c1x.py`; look_noise, crops sharp, mres, flick, look_where). Sheets in `perf9\c10\`–`c13\`. Judges' crops and measuring scripts: `judge_c10\`, `judge_c11\`, `judge_c12\`, `judge_c13b\` beside it. Frames: this worktree's `godot/.shots`.
- Repoint the scripts to a new worktree with a copy of `setup9.py` (same scratchpad).

## Gotchas

- Worktree setup: delete the `godot/assets` placeholder file, make it a junction (`New-Item -ItemType Junction`) to the worktree's `public/assets`, `git update-index --skip-worktree godot/assets`; copy `godot/override.cfg` (perf user folder); robocopy `godot/.godot` from a worktree that has imported; copy `.import`/`.uid` (setup9.py); `dotnet build` in `godot/` after every C# change (the game runs the built assembly). The editor import crashed (access violation) at 94 s once; the game ran fine on the cache; use `-NoImport`. Never commit `.import`/`.uid` churn.
- **Never merge a WIP branch whole**: a6a04's WIP commit had replaced the `godot/assets` symlink with 850 copied asset files. Apply its code with `git diff A^ A -- paths | git apply -3`.
- batch.ps1's give-back sometimes leaves the godot entry listed; check `turn.py show` and give it back by its exact listed name.
- `--auto` is needed for fights (else the Blessing picker pauses); the autopilot's 1440 run path is not repeatable (two bias runs went off course).
- Engine facts (Godot 4.5.1 source in scratchpad `0b33992d-...\scratchpad\godot_src\`): FSR 2's reactive mask is the colour's alpha (clamped 0.9); the transparent pass writes no motion vectors; `blend_mul` alpha = src × dst (so the eraser works); alpha antialiasing cuts at the scissor first, then ramps at scissor + edge with a +25%/mip boost.

## Collaborators

Main session (reports, owner decisions; relays to the face lead, who owns the hair's look and mesh, eyes and lashes). Outfits and animation leads share the godot turn.

HANDOFF READY: docs/handoff/performance.md on worktree-agent-a4e0c353e61cca6dc (successor of a3123dd8bb0182789)
