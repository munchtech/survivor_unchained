# Waystation close-up lifetime regression

`Game.LeaveZone()` queues the old `WorldScene` for deletion. Its child `CelRigKey`
is freed with it; cinematic teardown does not free that key. The cached reference
survived in `Game`, so `CelRigHeld` read `Visible` on a disposed light after c04b.
That exception skipped the rest of `_Process`, including cinema and seam updates.

`CloseUpLeave()` now restores the world key's layer mask, releases the camera rig,
unhooks lamp dimming, and drops the scene-owned close-up and creation light caches
before the scene is freed. Reads of optional cached lights check instance validity;
the gear and hair keys can each be rebuilt independently. `FrameGuard` contains a
close-up exception, reports it once, and retries in the next zone.

## Checks

- `dotnet test` in `godot/tests`, with integration `f7c7ff458` merged: 2,265 passed,
  0 failed, 11 skipped (the pre-merge fix also passed 2,213/0/11).
- `FrameGuardTests`: the frame continues after a disposed-object failure, the
  error is reported once, and a new zone can resume the subsystem.
- `CloseUpLifetime`: build a cel key in the Low Ford, enter the Waystation, wait
  for the old scene to free, and check every cached light and the restored mask.
  Free a fresh cel key and tick close-up directly; free the sibling lights and
  tick again; play c04b and require 120 further play frames in the Waystation
  without disabling close-up.

Both the headless and Vulkan Forward+ runs passed all three engine checks, reached
the Waystation after c04b, and logged zero `ObjectDisposedException` entries. The
rendered run logged zero C# exceptions. Headless mode also reports dummy-renderer
blend-shape and 3D color-table errors; the rendered run avoids those, but reports
shader-cache write errors. Logs stay in the worktree as `closeup-harness-final.log`,
`closeup-rendered.log`, and `closeup-rendered-stderr.log` (ignored).
The final rendered recheck after the integration merge also passed all three
checks with zero C# exceptions; its logs are `closeup-integrated-rendered.log`
and `closeup-integrated-rendered-stderr.log`.

The engine harness uses its own `Survivor Unchained Codex closeup-blackscreen`
user directory and checks that isolation before creating the game. Run from the
worktree after importing its assets and building `godot/SurvivorUnchained.csproj`:

```powershell
python tools/turn.py take godot "codex: closeup-blackscreen" --stale-ok
if ($LASTEXITCODE -ne 0) { throw "Godot turn was not granted" }
try {
    & $env:GODOT_CONSOLE --headless --fixed-fps 60 --path godot `
        --log-file "$PWD/closeup-lifetime-engine.log" `
        -s res://tools_scenes/closeup_lifetime.gd --quit-after 6000 `
        -- --quick warden --zone waystation *> closeup-lifetime.log
} finally {
    python tools/turn.py give godot "codex: closeup-blackscreen"
}
```

Set `GODOT_CONSOLE` to the Godot 4.5.1 Mono console executable. `--stale-ok` is for
this lifecycle check, which makes no visual judgment. A passing run prints all
three `closeup lifetime: PASS` lines and has zero `ObjectDisposedException` entries.
