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

Each live change first gets a FAST PREVIEW, then the exact replay replaces it. The preview keeps the
held scene (the last replay's, camera and all), forgets the package's caches, rebuilds only the shot NPC
in its place (`Game.RebuildShotNpc`, its driver kept; a file whose sha256 is unchanged stays loaded, so a
manifest edit rebuilds in about 0.01 s and only a changed glb is read again), draws 6 frames to settle and saves that frame
as `live_out/CAM.png` with `"kind": "preview"` in `CAM.json` (`status.json` state `preview`); the window
shows a small yellow PREVIEW tag in the top-left corner until the replay starts (the saved frame has no
tag). A preview is not a capture: lighting history, TIME and the clock are the held scene's, not a fresh
run's. Requests (captures) are always exact replays. A change that lands during a live replay waits for
it to finish (its frame is written, with its own fingerprint), then is previewed in its scene and
replayed (a replay dropped early has no scene worth previewing in: still fading in, the zone title up).
A touch that changes neither the files' content nor `live.json` replays nothing (F5 replays anyway).
There is no preview right after boot (no held shot yet) or when no godot turn frees within 3 s.
In the window: F5 replays the live package again, F9 captures it into `captures/`.

Request keys (game_frame's flags): `package`, `id`, `out`, `name`, `cams` (play, chest), `zone`,
`time` (day/night), `clock`, `walk`, `turn`, `spot` (sun, shade, `dx,dz`), `off` (game_frame's terms:
ink, glow, key, ...), `light`, `light_only`, `global`, `solo`, `mods`, `size`. Unknown keys are refused.
`CAM_dump.json` has game_frame's `_dump` keys; `CAM.json` adds the package fingerprint (sha256 of the
manifest and every file it names), the game commit, the shader fingerprint, the switches used and the
timings (`turn_wait_s`, `replay_s`, `change_to_frame_s`, and `split`: where the replay's time went,
`change_call_s`, `load_to_ready_s`, `ready_to_first_draw_s`, `stepped_draws`, `stepped_fps`,
`median_draw_ms`, `p90_draw_ms`, `slowest_draws_ms`, `last_draw_to_capture_s`).

`status.json`: `state` (booting, idle, waiting-turn, preview, replaying, failed, stopped), `pid` (the game's own;
the console exe is a wrapper), `heartbeat` (unix s, written each second by a timer thread, so a replay's
scene load never reads as dead), `main_at` (when the main thread last wrote its state), `game_root`, `game_commit` (at start), `game_head_now`, `game_dirty_at_start`,
`shader_fingerprint` / `shader_fingerprint_now`, `stale` + `stale_why` (the checkout moved on or a
shader changed since boot: the frame is no longer the current game; restart), `turn`, `size`,
`replaying`, `shown` (last frame, when), `queue`, `last_error`. A tool reading frames should fail
loudly when the heartbeat is older than 10 s (not running), `main_at` older than 150 s (hung; a replay
fails itself after 120 s) or `stale` is true.

## Turn policy, and why

The viewer takes a godot turn (`tools/turn.py take godot "look-viewer: replays (pid N)"`) only for
a burst of work and gives it back when the queue is empty: at once after a capture, 60 s after a live
replay or preview (`--look-turn-grace S`), so the next edit's preview starts at once while an edit
session is going. Between refreshes it holds the last frame with the render loop off and the tree
paused (no GPU, about no CPU), so a viewer left open never competes for the GPU and holds a slot at
most a minute past its last live frame. A preview asks for a turn for 3 s at most (else no preview,
the replay waits its place); a replay or request waits in the queue (`waiting-turn`) until a slot frees.

## Measured (13 Nov, gf_keeper_lamp, waystation day, 1920x1080)

Full-frame diffs (max abs / mean abs / % px > 2):

| | play | chest |
|---|---|---|
| game_frame vs game_frame (the floor) | 39 / 0.0022 / 0.034% | 35 / 0.031 / 0.61% |
| game_frame vs viewer (two replays) | 36-39 / 0.002 / 0.027-0.033% | 33-35 / 0.03 / 0.63-0.65% |
| viewer vs viewer | 8 / 0.001 / 0.009% | 37 / 0.035 / 0.65% |

The residue sits where game_frame differs from itself (a one-pixel column at the right edge, a few
sparkles); the capture lands on the same draw (361 play, 481 chest) at the same TIME and TAA phase.
One residue varies from replay to replay: a dim patch in the bottom-left corner of the play frame (max
14/255, 0-1150 px; with it one viewer replay read 0.084% px > 2). Both game_frame runs had none there;
its source is not found (the lights in the dumps match).
Change to pixels (play camera, the turn held from the last live frame):

| change | preview | exact replay |
|---|---|---|
| manifest only (body.glb kept loaded) | 0.84-0.89 s | 21.9-27.8 s |
| a new body.glb (222 MB, 30 embedded images) | 3.6-4.6 s (the glb read 2.9-4.0 s) | 22.5-30.3 s |

Where a replay's 17-26 s go (`timings.split`, 13 Nov, the GPU shared with other leads): the scene
change call 0.03 s and load to `Shots._Ready` 0.2-0.3 s; then the first draw waits 10-16 s (the world
build and the package: its glb read 3-6 s of that); then the 361 stepped draws (6 s of game at a fixed 60
fps) take 6-10 s at 14-21 fps (median draw 14-24 ms); the capture lands 0.6-1.0 s after the last draw.
The glb read was 6.7-6.9 s before its images were decoded on all cores (`GlbPredecode`, the same
decoders, handed to GltfDocument; `--no-glb-predecode` for Godot's own; frames unchanged: viewer vs
game_frame play 0.029%, chest 0.64% after it). The rest is the world and the stepping, which the
floor needs (skipping draws changes TIME and the TAA phase), so it stays. With every godot slot taken a
replay waits for one (one request waited 224 s).

## What it does not cover

- `spot: shade` outside the waystation (game_frame's ray search) is refused; the table offset
  (waystation -1.0, 6.0) and explicit `dx,dz` work.
- game_frame's `--gf-clip`, `--gf-at`, `--gf-held`, `--gf-probe` are not ported.
- Game code changes (C#, scenes) need a restart; `stale` says when.
- It writes nothing under the game checkout and imports nothing (packages load as overlays).
