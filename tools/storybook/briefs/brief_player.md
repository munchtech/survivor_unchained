Context budget: 280k

You are the code solver for the STORYBOOK PLAYER in Survivor Unchained (Godot 4.5.1 .NET, C#). You report to the storybook lead who spawned you: your final message is your report (what's built, commits, numbers, what's left). Never SendMessage "main".

## Where and the rules
- Worktree: C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\storybook-1, branch `storybook-1`. Work only there. Use absolute paths.
- `godot/assets` there is a junction: NEVER run `git stash`, `git reset --hard` or `git checkout .`. Check out named files only. Commit as you go (WIP commits are fine), push `storybook-1` at each milestone (`git push origin storybook-1`).
- Run `dotnet test` in `godot/tests` before each commit and keep it green. Run `dotnet build` before any Godot run that shoots pictures (shoots don't rebuild C#).
- Godot runs for pictures take a turn: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "storybook: <job>"` (exit 1 = busy: do code meanwhile, ask again within 90 s or use `--wait N` minutes), and `give godot "<same name>"` the moment it ends. Never kill processes by name; stop only a PID you started. Don't test or shoot the male hero.
- Comments are short prose that say why. Read files by section (grep first); don't read huge files whole.
- Godot: C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\ (the _console.exe). See how existing shot runs are launched (grep `tools/shot.mjs`, `Shots.Want`, `Args.Get`) and follow that.

## What the storybook is (the owner's words)
"another cheaper, but stylisticly and artistically STILL PERFECT version of like a storybook type cinematic drawings that can show true anguish much better". Diablo III's drawn act cinematics are the touchstone: painted, inked illustrations in layers, slow camera moves, parallax, living touches (fire, smoke, cloth, rain, ink that spreads), cut and scored like film. The first one, SB00 "Stay Where They Reach" (docs/story/storybook/sb00_stay_where_they_reach.md: read "The plates", "Handover to C01", "Lines"), OPENS the game: it plays when creation is confirmed, before C01, and ends in black on silence after the drowning. The lead makes the art; you build the player and the format so the art can be dropped in. Keep it cheap to run.

## Build
### 1. The format: one JSON file per storybook, `godot/data/storybook/<id>.json`
Write `docs/storybook/README.md` ("Format", "Running it", "Provenance" left as a heading for the lead) from what you build. Shape (v1; extend only where needed and say so):
```
{ "id": "sb00", "conversation": "sb_stay_where_they_reach",
  "canvas": [3200, 1800],            // the plate's reference frame in px (16:9); the 2.39:1 bars crop it
  "grain": 0.05, "vignette": 0.3,    // a light screen-space finish over everything
  "plates": [ { "id": "p1", "at": 2.5, "until": 11.0,       // seconds from the first frame of black
      "in":  {"kind": "ink", "dur": 1.6, "origin": [0.42, 0.55], "map": "res://...png" (optional), "edge": "#0b0a09", "soft": 0.08},
      "out": {"kind": "fade", "dur": 2.0} (optional),
      "camera": [ {"t": 0, "x": 1600, "y": 700, "zoom": 1.08, "dolly": 0, "rot": 0},
                  {"t": 8.5, "x": 1700, "y": 1150, "zoom": 1.2, "dolly": 0.12, "ease": "inout"} ],
      "grade":  [ {"t": 0, "exposure": 1, "tint": "#ffffff", "sat": 1}, ... ] (optional, keyed like the camera),
      "layers": [ { "id": "sky", "image": "res://art/storybook/sb00/p1/sky.png", "pos": [0, 0], "scale": 1, "z": 6,
                    "blend": "mix|add|screen|multiply", "opacity": 1, "pivot": [x, y],
                    "keys": [ {"t": 5.0, "dx": 0, "dy": 0, "scale": 1.0, "rot": 0, "opacity": 1, "ease": "inout"}, ... ],
                    "frames": [ {"t": 0, "image": "a.png"}, {"t": 3.2, "image": "b.png", "fade": 0.4} ],   // drawn key poses, crossfaded
                    "touch": [ {"kind": "flicker", ...}, ... ] } ],
      "fx":   [ {"kind": "particles", "preset": "smoke", "at": [x, y], "area": [w, h], "z": 0.8, ...}, {"kind": "mist", ...} ],
      "cues": [ {"at": 0.0, "do": "line", "id": "legion"}, ... ]   // times relative to the plate's "at"
  } ],
  "cues": [ ... at absolute times ... ], "end": 89.5 }
```
- Times, positions and sizes are in seconds and canvas px. Plates overlap during their "in" transitions; a plate is drawn from `at - in.dur`... choose one clear rule and document it (the lead's preference: the incoming plate's `at` is when its transition STARTS, and the outgoing plate is drawn until the transition ends).
### 2. The camera and parallax (2.5D)
- Each layer is a plane at distance `z` from the camera at rest (1 = the reference plane; sky 6-20; foreground 0.5-0.9). Its image is authored as seen from the rest camera, so at rest every layer sits at its `pos`.
- Camera keys: `x, y` = the canvas point at the screen's center on the reference plane; `zoom` = lens magnification (1 = the canvas width fills the screen width; uniform, no parallax change); `dolly` = how far the camera has moved forward, in the same depth units (a push: near layers grow faster than far ones); `rot` = small roll in degrees. Pinhole projection: for layer depth z, apparent scale = z/(z - dolly), and a pan of the camera by (x - W/2) shifts the layer by (x - W/2)/z on the reference scale. Unit-test this math.
- Interpolation: smooth and slow. Per-segment ease (`linear|in|out|inout|hold`, default inout); the speed must be continuous across a key that isn't a hold (use a Catmull-Rom/Hermite through the keys or equivalent). No jitter; sub-pixel smooth.
- Implementation suggestion (yours to decide, say why): 2D. Each plate renders into its own SubViewport (Node2D layers placed by the projection each frame, CanvasItem shaders for touches, GPUParticles2D for fx), and a full-screen composite shader mixes the outgoing and incoming plates for transitions, then applies grade, grain and vignette. Only plates being drawn exist.
### 3. Living touches (shaders and particles), each documented with its parameters in the README
- `flicker` {rate, amount, seed}: brightness noise for fire and lamp light layers (usually `blend: add`). Layered noise, never a sine.
- `sway` {mask, amp px, freq, dir, scale}: displacement by low-frequency noise weighted by a mask texture (cloth, weed, banners, flame tongues).
- `water` {mask, amp, freq, scale}: finer, faster displacement inside a mask (a trembling surface, a reflection).
- `ripple` {centers [[x,y],...], start, period, speed, amp, rings, mask}: expanding concentric rings (a faint highlight and a little refraction), fading with radius; repeating every period.
- `reveal` {map, t0, t1, soft, invert}: the layer appears (or goes) where a grayscale order map passes an animated threshold (a crack spreading through frost, a glow narrowing to a line and going out, light draining into the ground).
- `scroll` {speed [x,y]}: UV scroll of a repeating texture (mist bands, flowing water).
- fx `particles` presets: `smoke` (soft, rising, slow, fading), `sparks` (tiny, bright, gravity, short life, `burst` times), `motes` (glowing dots rising slowly with wobble), `bubbles` (rising fast), `drips` (falling drops), `ash`/`snow`. Params: at, area, z, rate, burst [times], life, speed, dir, spread, gravity, size, color (start/end), additive, seed. Particles parallax with their z like a layer. Use small soft sprites you generate procedurally (or a texture the lead supplies) so they read as painted, not as engine sparkles.
- fx `mist` {rect, z, color, density, speed, scale}: a procedural noise fog band that drifts.
### 4. Transitions (`in`) and `out`
`cut`, `fade` {dur, color}, `dissolve` {dur}, `ink` {dur, origin, map, edge, soft} (the incoming plate appears where an ink-bloom map passes a rising threshold, with a dark wet-ink rim at the front: "the next plate's ink spreads up through the last"; default map procedural, fractal, from `origin`), `light` (ink, but the front is warm light: P0's lamp opening P1), `waterline` {dur, wave} (a wavy surface line sweeping up the frame as the camera goes under). `out: fade` to black.
### 5. Sound, lines and subtitles (reuse the game's systems)
- `line` {id, tag}: the line `<conversation>.<id>` through `CineLines` (godot/logic/Cinema/CineLines.cs) and the game's VoiceOver (godot/src/Audio/VoiceOver.cs): play its take when there is one, else run silent for the reading pace; its subtitle through `CinemaBars.Say` (godot/src/Ui/CinemaBars.cs) for the take's length. `tag` sets the speaker label for that line only (SB00's first line is tagged "An old Watchman"; the later lines are untagged roman). A line id with a dot is a full id from another conversation (SB00 reuses `cin_none_cross.call`, sung: its subtitle in italics under "A voice under the water").
- `sfx` {name, gain, pan}: the game's named sounds (godot/src/Audio/Sfx.cs).
- `sound` {file, id, gain dB, pan, fade, loop}: an AudioStreamPlayer on a storybook bus; `stop` {id, fade}.
- `music` {mood}: the game's Music (SB00 starts with `silence`).
- `bus` {lowpass Hz, gain dB, over s}: the storybook bus's filter and level moving over time (the underwater muffle; "every sound sinks away, as if down a well" in the last 2 s).
- `say` {text, speaker, sung, dur}: a subtitle without a take.
- The bars: CinemaBars at 2.39:1, fully in from the first frame.
### 6. Skip, the hook before C01, the flag
- Hold interact or pause to skip (the CinemaBars ring), allowed from 1.5 s on a first view and at once once the profile flag `seen.sb00` is set (find where profile-level settings/flags live; set it when SB00 first starts). A skip cuts to black, fades all its sound in 0.15 s and ends it as skipped.
- The hook (sb00 doc, "Trigger and facts" and "Handover to C01"): on a new journey, when creation is confirmed (`GameFront.BeginJourney`), creation's last frame holds 0.5 s and fades to black over 0.8 s with the title music, then SB00 plays from black. At its end (black, silence) the zone is entered under the black as now and C01 plays. If SB00 played to its end, C01 starts at shot 1 WITHOUT its first sound (`water_close` in shot 1 of godot/data/cinematics/c01.json) and with 1.0 s more silence at its start (shot 1 becomes 2.5 s; the rest of C01's timing unchanged); if it was skipped, C01 plays exactly as written. Use a journey fact and the cine format's existing `when` (CineWhen) rather than a second C01. C01 must start with the bars already in (like a chained cinematic), so nothing moves at the seam. `--nocine` and quick starts skip SB00 as they skip C01; `--cines` plays it.
- Only when `godot/data/storybook/sb00.json` exists; otherwise everything plays as now.
### 7. Running it for pictures (the lead and the judges need these)
- `--storybook ID`: play that storybook at once over black (no creation, no zone) and quit at its end.
- `--sb-from S`: start at time S (incremental checks).
- `--sb-shots T1,T2,...`: save full-resolution PNG frames at those times (named `sb_<id>_<t>.png` where the game's shots go), then quit after the last.
- A capture with sound for the cut's judge: Godot's Movie Maker (`--write-movie <file>.avi --fixed-fps 30`) must play it deterministically; check and document the command (and an ffmpeg line to mp4 if ffmpeg is present).
### 8. Cheap to run
Load a plate's textures when it's about to be drawn (threaded preload of the next plate), free them after. Import storybook art VRAM-compressed (high quality) with mipmaps. Measure one busy plate (6 layers at 3200x1800, 3 particle systems, 3 touches) at 1080p and report the frame time.
### 9. A test storybook and SB00's skeleton
- `godot/data/storybook/test_plates.json` with procedural placeholder layers you generate (`godot/art/storybook/test/`) that prove parallax, every touch, every transition and the cues; shoot a few frames and LOOK at them (half size is enough for you) to check the parallax and transitions behave.
- `godot/data/storybook/sb00.json`: the full timeline from the doc with placeholder layers (a flat dark card per plate with its id written small), every plate's time (P0 0-2.5, P1 2.5-11, P2 11-15.5, P3 15.5-25.5, P4 25.5-37, P5 37-46, P6 46-56, P7 56-63.5, P8 63.5-71, P9 71-78, P10a 78-81.5, P10b 81.5-84, P10c 84-87.5, black to 89.5), each plate's line cue from the doc's Lines table (conversation `sb_stay_where_they_reach`; add the 9 lines to the game's dialogue data where conversations live, with the exact words from the doc, speaker `watchman`), and the sung `cin_none_cross.call` in P10. The lead replaces the placeholders with art.
### 10. Tests
xUnit in godot/tests, as the existing ones: the format parses (sb00 and the test file); the projection math; camera interpolation (continuous, eased, holds); which plates draw at a time and a transition's progress; cue order; skip rules (1.5 s vs at once); the C01 variant (water_close dropped and +1.0 s only when SB00 ended).

## Report (your final message, short)
Commits (hash, one line each), how to run it (exact command lines), the frame-time numbers, what you looked at, and anything left or decided differently from this brief, with why. Stop at about 260k: commit, push, and report what's left.
