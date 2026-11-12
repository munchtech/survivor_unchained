# Renderer messages

Investigation on November 11–12, 2026, using Godot 4.5.1 Mono
(`f62fdbde1`), Vulkan Forward+, and the RTX 5080. The integration ruling's
baseline was 2,349 passed, 0 failed, 11 skipped.

The geometry warning is an engine pairing bug. The cache-write errors were
caused by our close-up harness changing its user directory too late. Only the
harness startup and its documentation change; game lighting, shaders, art,
layout, and writing are untouched.

## Geometry/light pairing

The longer prologue trace first emitted four messages when c03 ended and the
Low Ford changed from night to dawn, immediately before `sb_dawn` and c04a.
This was a change of the Low Ford's time of day, before the physical trip to
the Waystation. `Game.Cine.Finish()` releases its rig lights and
`HerLightEnd()` returns the cinematic double's meshes to people's layer.

The affected lights were the hair and gear twins of c03's final `skin` rig
(shot s12: color `#ffd8b0`, energy 1.7, angle 32 degrees, range 6 m). In the
measured baseline they were
`/root/Game/World_lowford/_SpotLight3D_1393_hair` (mask `0x1000`) and
`/root/Game/World_lowford/_SpotLight3D_1393_gear` (mask `0x2000`). The repeat
named them `_SpotLight3D_1351_hair` and `_SpotLight3D_1351_gear`; both runs
released them at process frame 2,617 and printed twice for each. Replacing a
rig while its old node is queued for
deletion can give the replacement an automatic node name; the number is not
a stable identifier. These twins come from `GameCinemaHer.Twin`, not the
close-up `CelRigKey` cache fixed by `codex/closeup-blackscreen`.

Godot prints twice for one stale light: on removal from its scenario
(`renderer_scene_cull.cpp:835`) and on release of its base (`:607`).
Changing a mesh's layer can leave its old light pairing behind in Forward+;
the old unpair routine then rejects the pairing because the *new* layer no
longer matches the light. The engine's layer setter must unpair geometry
before changing that layer. This matches [Godot issue 121989](https://github.com/godotengine/godot/issues/121989)
and the correction in [Godot PR 122064](https://github.com/godotengine/godot/pull/122064).
The installed 4.5.1 source still has the faulty conditional in
[`instance_set_layer_mask`](https://github.com/godotengine/godot/blob/4.5.1-stable/servers/rendering/renderer_scene_cull.cpp).

A separate engine-only control used one box and one `OmniLight3D` named
`ProbeLight`: matching layer 1, five process frames, change the box to layer
2, five frames, free the light. It produced exactly two warnings. Keeping
the box on layer 1 produced zero. Both controls contained no game code and
exited with code 0 without C# exceptions. No game lifetime-order
workaround or mask change is made for this engine defect.

The message alone did not stop the cinematic or cause the close-up's former
disposed-object black screen in these checks. It is still an engine invariant
failure, not a promise that every occurrence is harmless. The old rendering
handoff also [records a shutdown crash after this warning](../handoff/history/rendering.md).
Do not suppress it
or classify a crash as successful merely because the warning is known.

## Shader-cache writes

The unmodified `CloseUpLifetime._Ready()` changed
`application/config/custom_user_dir_name` to
`Survivor Unchained Codex closeup-blackscreen` after the renderer had already
initialized. Godot's renderer had created its shader-cache directory tree
under the *startup* `user://`, and retained paths beginning
`user://shader_cache`. The later setting redirected those paths into the
harness profile, where the initialized cache directories did not exist.

Consequently `ShaderRD::_save_to_cache` could not open its destination and
printed `Condition "f.is_null()" is true` at `shader_rd.cpp:516`. This fired
while Low Ford/Waystation materials first requested shader variants, including
the c04b harness, rather than when a particular light was freed. It has no
single offending light or mesh. Shader compilation had succeeded; storing
the compiled bytes for another run failed. See the engine's
[cache-directory setup](https://github.com/godotengine/godot/blob/4.5.1-stable/servers/rendering/renderer_rd/renderer_compositor_rd.cpp)
and [cache-write/compile-completion paths](https://github.com/godotengine/godot/blob/4.5.1-stable/servers/rendering/renderer_rd/shader_rd.cpp).

`tools/experience/closeup_lifetime.py` now supplies the private profile in a
temporary `godot/override.cfg` before starting Godot. The C# harness only
verifies isolation; it never moves `user://`. The launcher preserves and
restores any existing override, serializes checks within one worktree, takes
and releases a Godot turn, and requires all three lifecycle passes and zero
cache-write errors. It leaves shader caching enabled. On Windows it resolves
the console wrapper to the actual engine executable so a timeout stops its
own engine PID without leaving the wrapper's child behind.

The old rendered harness produced **351 cache-write errors**, while passing
all three lifecycle checks. The corrected rendered harness produced **0**,
also with all three checks passing and no `ObjectDisposedException`. Its
previous startup configuration was restored byte for byte. These cache
errors were harmless to the already compiled frame, but prevented cache
reuse and could increase compilation cost on later runs. They were ours to
remove.

## Measured counts

Count each printed message once in the merged stdout/stderr log; do not count
the same engine log a second time. Count cache writes by the following
`at: _save_to_cache` line, not by every `f.is_null()` elsewhere in Godot.

| Rendered segment/check | Geometry before | Geometry after | Cache writes before | Cache writes after |
| --- | ---: | ---: | ---: | ---: |
| Low Ford, including c03 → dawn → c04a | 4 | 4 | 0 | 0 |
| Low Ford → Waystation and town play | 0 | 0 | 0 | 0 |
| Waystation → Deep Shaw arena, combat, return to town | 0 | 0 | 0 | 0 |
| Shutdown of that route | 0 | 0 | 0 | 0 |
| **Whole three-zone route** | **4** | **4** | **0** | **0** |
| Separate close-up lifetime/c04b harness | 0 | 0 | **351** | **0** |

The ordinary game route does not run the broken harness, so its cache count
was already zero. The before/after pairing count is unchanged because no
game lighting or engine pairing code changed. The reported six-to-eight
was not reproduced by this seed: two affected lights produced four messages,
rather than a fixed count per zone change.

Both measured runs used 1,920 × 1,080 Forward+, seed 1, and 240 simulated
seconds: c03 at 20 s, travel to the Waystation at 100 s, take its first arena
offer at 160 s, then return to town after falling. The baseline took 520.96 s
wall time; the repeat took 420.03 s. Both exited 0, had no C# exceptions and
did not fire the quit guard. Frames of Low Ford, the town, and arena combat
were inspected at full resolution. Existing shutdown resource-leak messages
were present in both runs and are not included in either target count.

Effective game arguments, passed after the engine's `--`:

```text
--quick warden --zone lowford --auto idle --seed 1 --time night
--close-hold 0 --cine c03 --cine-at 20 --travel waystation@100 --pull 160
--shot NAME --on noise --every 40 --count 6 --until 240
--cast-ahead off --no-double-ahead
```

These route runs used this local `godot/override.cfg` **before Godot started**;
the raw game arguments alone do not isolate developer saves:

```ini
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="CodexRendererNoise"
```

The last two switches disable background actor preparation for this scripted
start; the same actors, clips, materials, and light settings are rendered.
Starting c03 on the fresh scene's first second stalled actor preparation;
that stopped attempt is excluded. A separate full-prologue diagnostic located
the same c03 warnings but missed its scheduled arena pull, so it is also
excluded from the comparison. An initial short route skipped c03 and had
zero pairing warnings; that zero was not treated as a fix.

The engine-only box/light control produced 2 messages with a layer change
and 0 without one, both with exit 0. The corrected close-up harness was
repeated after the launcher switched to the actual engine PID: 3/3 checks,
zero cache writes, zero `ObjectDisposedException` entries.

## Suite validation

The earlier full suite on merged integration `d04430318` passed
**2,349/0/11**. The later post-merge run hit the existing
`SmoothNormalsTests.SixtyThousandVertsBakeFast` wall-time assertion while
rendering jobs were active (361 ms against 250 ms). It passed alone after
those jobs stopped, then passed in the complete suite. On integration
`8d30ec648` merged into this branch (`af446a826`), the final full
`dotnet test --no-restore` run passed **2,364 tests, 0 failed, 11 skipped**
(2,375 total; 11 minutes 36 seconds), without concurrent renderer jobs of
ours. The game build also completed with 0 errors. No test assertions,
thresholds, or suite cases were changed by this job.

## Distinguishing a real failure

- Pairing noise: the exact native message at `instance_set_scenario` or
  `instance_set_base`, at a traced light exit after mesh layer changes.
  Verify that the next cinematic and zone still render and continue.
- Cache noise: `_save_to_cache` with compiled frames still present. An
  isolated startup profile should eliminate this harness defect. If writes
  still fail, check its real cache path, directory existence, and write access.
- A C# `ObjectDisposedException`, `closeup lifetime: FAIL`, missing PASS
  markers, a frozen black frame, shader **compilation** errors, a graphics
  device loss, a storage-buffer error, or a nonzero process exit is a
  separate failure. None is excused by either message above.
- Shutdown RID/PagedAllocator leaks were also observed. Some separate
  diagnostics fired the existing quit guard; the measured three-zone runs
  did not. These are recorded separately. A guard's code 0 must not be
  described as a clean engine shutdown.

## Repeating the close-up check

After importing and building this worktree, set `GODOT_CONSOLE` to the Godot
4.5.1 Mono console executable and run:

```powershell
python tools/experience/closeup_lifetime.py --timeout 600 `
    --log godot/.shots/closeup-lifetime.log
```

This is a rendered tool run, not a unit test. Add `--headless` only for the
dummy-renderer lifecycle check. Raw investigation logs and scripts are kept
in the job worktree's ignored `.renderer-noise/` directory:
`route_measured_before.log/.json`, `route_measured_after.log/.json`,
`counts.json`, `probe_layers.log`, `probe_static.log`, `cache_before.log`,
`cache_after.log`, `cache_final.log`, `timing-check.log`, and `suite-serial.log`.
The route's observer and command driver are `trace.gd` and `run.py` there;
the local startup override isolates its saves under `CodexRendererNoise`.

## Initial control save incident

The first short control, `before.log`, used the game's default developer
save path before the route's startup isolation was installed. It logged
`save: every slot in use, slot 0 replaced (a dev path)`; the default profile's
`saves/slot0.json` and `meta.json` were written at 21:44 on November 11.
Every subsequent route and close-up check used a private profile. The route
driver now refuses to run without its isolated startup configuration.

The coordinator's recorded profile backups covered settings, and the saved
journey snapshots found in the repo/input folders predated this run by days.
No exact pre-run slot-0 backup was found, so no uncertain older save was
written back. The post-control slot and metadata are preserved locally in
`.renderer-noise/save-incident/`. This incident remains open for the
owner/coordinator; it is separate from the renderer findings.
