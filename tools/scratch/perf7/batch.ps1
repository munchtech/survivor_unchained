# One Godot turn: import, then the runs in RUNSFILE (shoot.py), then give the turn back.
#   powershell -File batch.ps1 RUNSFILE "HOLDER NAME" [-NoImport]
param([string]$Runs, [string]$Holder, [switch]$NoImport)
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\perf7"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7afb4d33cdd5efba"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
python $TurnScript take godot $Holder --wait 1800
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    if (-not $NoImport) {
        & $GodotConsole --headless --path "$TreeDir\godot" --import *> "$ScratchDir\import.log"
        "import: exit $LASTEXITCODE, $([int]$clock.Elapsed.TotalSeconds) s"
    }
    python "$ScratchDir\shoot.py" $Runs
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $Holder
}
