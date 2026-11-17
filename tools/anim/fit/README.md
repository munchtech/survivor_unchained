# tools/anim/fit: her drawn-sword carry, as a recipe for any body

The owner, 16 Nov: "remember to always keep marionette looped in for anything were building in modeling rigging animating so we can reproduce it." (PIPELINE.md, "Marionette is the pipe".)

The carry is set three ways:
- **A's clip keys:** the clip builders under tools/anim (prowl.py, run.py, sprint_stop.py).
- **Each body's bake:** tools/body/bake_clips.sh. Any per-body arm turn goes in tools/body/p1_clips.json, recorded with a "why".
- **The runtime layer:** godot/logic/Play/SideCarry.cs.

A body is held to the targets in carry_targets.json. They are written as data, not as joint angles.

| tool | inputs | outputs |
|---|---|---|
| fr.py | clip json dir (tools/anim/out/clips), clip names, PITCH | arm read per facing; with FR_JSON, carry_ref_a.json |
| m11.py | clip json dir | sword line per clip as played (clavhold + armroll), read at the play camera |
| carry_read.py | bake keys dump dir (tools/body/out/clips), carry_targets.json, carry_ref_a.json | the body's arm read against A's, flags; exit 1 on a flag |
| ana10.py | LOG=shoot dir (views.log), leg, frame range | the game's drawn blade per frame (screen angle, tip under the boot, shown fraction, pitch, heading `hd`, `loc` tip and grip over this frame's lower ankle) |
| t10.py | shoot dirs | the judge bars T1, T1', T3 over the pivot windows |
| scan.py | shoot dir, number of legs | the judge scan: T3, dshown, SPIKE shown/tilt/pitch, cane, STOP window, TILTFLIP per frame, plus a counts line |
| hidden.py | shoot dir, number of legs (optional LEG LO HI) | T4: per leg, runs of frames where the blade is hidden behind her legs (fails on a run > 3) |
| runsame.py | shots dir, two shoot tags, legs, frame range | largest frame-for-frame blade-trace difference between two shoots (T5) |
| simlog.py, m14.py | views.log | log parsing and screen projection, used by the tools above |

For a new body:
1. Bake it: `bash tools/body/bake_clips.sh --p1-bake-only warden` dumps the keys and writes nothing.
2. Run `python tools/anim/fit/carry_read.py tools/body/out/clips`.
3. If a flag shows, add arm turns for that clip in p1_clips.json and rebake. Do not hand-key.
4. Shoot the DirRun eight legs on that body and run t10.py and ana10.py against the "game" bars.
5. Re-measure that body's constants under "runtime_body_constants".
