# Live look viewer

The game itself, started once and kept open, that re-shoots an NPC package the way Marionette's
`tools/npc/game_frame.py` does, without a fresh Godot boot per frame. Every refresh is a full,
deterministic replay of what game_frame runs (same switches, same scene, same clock), so a viewer
frame and a game_frame frame of the same package match to the noise floor (numbers below).

Code: `godot/src/Game/LookViewer.cs` (the node), `godot/logic/Viewer/*` (pure parts: request
settings, fingerprint, change watch, request queue, switch table), `tools/look_viewer/look.py` (CLI),
tests `godot/tests/LookViewerTests.cs`.

## Run it

    python tools/look_viewer/look.py start                 # builds, boots the main checkout, waits for the heartbeat
    python tools/look_viewer/look.py capture PKG --out DIR [--cams play,chest] [--id ID] [game_frame's flags]
    python tools/look_viewer/look.py status                # status.json plus its age
    python tools/look_viewer/look.py stop                  # asks it to quit; kills only its own PID after 30 s

`--game ROOT` shoots another checkout (a worktree); `--size WxH` (default 1920x1080) is fixed for the
viewer's life (a request at another size is refused: restart with `--size`). capture exits 0 done,
1 failed, 2 bad use, 3 viewer not running or STALE (`--stale-ok` to shoot anyway).
PKG is a package folder, `live`, or a game package name (`godot/art/npc/NAME`).

## The drop folder

`C:\Users\munch\Desktop\survivorsunchained_inputs\look_viewer\` (env `LOOK_DROP` overrides):

| path | what |
|---|---|
| `live/` | the live package (manifest.json + body.glb + pieces...); any settled change replays it |
| `live.json` | its settings (same keys as a request); a change replays too |
| `live_out/` | the live package's frames: `CAM.png`, `CAM_dump.json`, `CAM.json` |
| `requests/ID.json` | a capture request; answered by `ID.done.json` (frames, out) or `ID.failed.json` (error) |
| `OUT/ID/CAM.png` | a request's frames (OUT = the request's `out`, default `captures/`) |
| `status.json` | heartbeat, rewritten every second (fields below) |
| `stop` | written by `look.py stop`: the viewer gives its turn back and quits |
| `viewer_log.txt`, `viewer.pid` | the game's log; its PID |

A change counts only after the files stood still 300 ms (a glb still being written is never loaded).
In the window: F5 replays the live package again, F9 captures it into `captures/`.

Request keys (game_frame's flags): `package`, `id`, `out`, `name`, `cams` (play, chest), `zone`,
`time` (day/night), `clock`, `walk`, `turn`, `spot` (sun, shade, `dx,dz`), `off` (game_frame's terms:
ink, glow, key, ...), `light`, `light_only`, `global`, `solo`, `mods`, `size`. Unknown keys are refused.
`CAM_dump.json` has game_frame's `_dump` keys; `CAM.json` adds the package fingerprint (sha256 of the
manifest and every file it names), the game commit, the shader fingerprint, the switches used and the
timings (`turn_wait_s`, `replay_s`, `change_to_frame_s`).

`status.json`: `state` (booting, idle, waiting-turn, replaying, failed, stopped), `pid` (the game's own;
the console exe is a wrapper), `heartbeat` (unix s, written each second by a timer thread, so a replay's
scene load never reads as dead), `main_at` (when the main thread last wrote its state), `game_root`, `game_commit` (at start), `game_head_now`, `game_dirty_at_start`,
`shader_fingerprint` / `shader_fingerprint_now`, `stale` + `stale_why` (the checkout moved on or a
shader changed since boot: the frame is no longer the current game; restart), `turn`, `size`,
`replaying`, `shown` (last frame, when), `queue`, `last_error`. A tool reading frames should fail
loudly when the heartbeat is older than 10 s (not running), `main_at` older than 150 s (hung; a replay
fails itself after 120 s) or `stale` is true.

## Turn policy, and why

The viewer takes a godot turn (`tools/turn.py take godot "look-viewer: replays (pid N)"`) only for
a replay burst, and gives it back when the queue is empty. Between refreshes it holds the last frame
with the render loop off and the tree paused (no GPU, about no CPU), so a viewer left open never
blocks another lead's Godot run and never competes with one for the GPU. A request waits in the
queue (state `waiting-turn`) until a slot frees.

## Measured (13 Nov, gf_keeper_lamp, waystation day, 1920x1080)

Full-frame diffs (max abs / mean abs / % px > 2):

| | play | chest |
|---|---|---|
| game_frame vs game_frame (the floor) | 39 / 0.0022 / 0.034% | 35 / 0.031 / 0.61% |
| game_frame vs viewer (two replays) | 36-39 / 0.002 / 0.027-0.033% | 33-35 / 0.03 / 0.63-0.65% |
| viewer vs viewer | 8 / 0.001 / 0.009% | 37 / 0.035 / 0.65% |

The residue sits where game_frame differs from itself (a one-pixel column at the right edge, a few
sparkles); the capture lands on the same draw (361 play, 481 chest) at the same TIME and TAA phase.
Change to frame (a manifest edit, play camera): 29.5-30.7 s, of which the godot turn 4-6 s and the
replay (scene load plus 6 s of game at 60 fps) 21-25 s. With every godot slot taken a replay waits for
one (one request waited 224 s).

## What it does not cover

- `spot: shade` outside the waystation (game_frame's ray search) is refused; the table offset
  (waystation -1.0, 6.0) and explicit `dx,dz` work.
- game_frame's `--gf-clip`, `--gf-at`, `--gf-held`, `--gf-probe` are not ported.
- Game code changes (C#, scenes) need a restart; `stale` says when.
- It writes nothing under the game checkout and imports nothing (packages load as overlays).
