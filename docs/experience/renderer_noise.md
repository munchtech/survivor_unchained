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

The affected lights were the hair and gear twins of c03's final `skin` rig.
In that trace they were
`/root/Game/World_lowford/_SpotLight3D_6640_hair` (mask `0x1000`) and
`/root/Game/World_lowford/_SpotLight3D_6640_gear` (mask `0x2000`). They exited
at process frame 21,338. Replacing a rig while its old node is queued for
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
the box on layer 1 produced zero. Neither control contains game code, either
exited with code 0, and neither threw a C# exception. No game lifetime-order
workaround or mask change is made for this engine defect.

The message alone did not stop the cinematic or cause the close-up's former
disposed-object black screen in these checks. It is still an engine invariant
failure, not a promise that every occurrence is harmless. The old rendering
handoff also records a shutdown crash after this warning. Do not suppress it
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
cache-write errors. It leaves shader caching enabled.

The old rendered harness produced **351 cache-write errors**, while passing
all three lifecycle checks. The corrected rendered harness produced **0**,
also with all three checks passing and no `ObjectDisposedException`. Its
previous startup configuration was restored byte for byte. These cache
errors were harmless to the already compiled frame, but prevented cache
reuse and could increase compilation cost on later runs. They were ours to
remove.

## Counts and remaining verification

Count each printed message once in the merged stdout/stderr log; do not count
the same engine log a second time. Count cache writes by the following
`at: _save_to_cache` line, not by every `f.is_null()` elsewhere in Godot.

| Rendered check | Geometry messages | Cache-write errors |
| --- | ---: | ---: |
| Short Low Ford → Waystation/c04b → arena control | 0 | 0 |
| Full prologue diagnostic through c03 and c04a | 4 | 0 |
| Original close-up lifetime harness | 0 | 351 |
| Corrected close-up lifetime harness | 0 | 0 |
| Engine box/light control, layer changed | 2 | 0 |
| Engine box/light control, layer unchanged | 0 | 0 |

The full prologue diagnostic's scheduled arena pull overlapped the town
arrival, so it is used to locate the c03 warning, not as the requested
three-zone comparison. The timed three-zone before/after measurement is in
progress. The initial short control skipped c03; its zero does not establish
that the historical six-to-eight messages were fixed.

The full suite on merged integration `d04430318` passed **2,349/0/11** in
15 minutes 37 seconds under shared load. A previous restricted testhost
launch aborted before connecting; the successful run used
`VSTEST_CONNECTION_TIMEOUT=300` and the normal full `dotnet test` command.
No tests or long-running suite cases were added.

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
- Shutdown RID/PagedAllocator leaks and `quit guard: fired` were also
  observed. They are recorded separately and are not cache-write or pairing
  counts. The guard's code 0 must not be described as a clean engine shutdown.

## Repeating the close-up check

After importing and building this worktree, set `GODOT_CONSOLE` to the Godot
4.5.1 Mono console executable and run:

```powershell
python tools/experience/closeup_lifetime.py --timeout 600 `
    --log godot/.shots/closeup-lifetime.log
```

This is a rendered tool run, not a unit test. Add `--headless` only for the
dummy-renderer lifecycle check. Raw investigation logs and scripts are kept
in the job worktree's ignored `.renderer-noise/` directory: `before.log`,
`natural_before.log`, `probe_layers.log`, `probe_static.log`,
`cache_before.log`, `cache_after.log`, and `suite-retry.log`.
