# Batch 1 (one Godot turn): the import; her in motion under each way of smoothing (164 Hz,
# drawn between steps or not); the crowd; still-camera shimmer; the see-through old and new;
# frame times of SMAA and FSR2 against TAA in the dense fight (paired flips).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf5"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad57a6dd0798688d7"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: her motion blur A/B, see-through, AA frame times"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
python $TurnScript take godot $TurnHolder --wait 60
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    & $GodotConsole --headless --path "$TreeDir\godot" --import *> "$ScratchDir\import1.log"
    "import: exit $LASTEXITCODE, $([int]$clock.Elapsed.TotalSeconds) s"
    Remove-Item "$TreeDir\godot\.shots\her_at.txt" -ErrorAction SilentlyContinue
    python "$ScratchDir\shoot.py" "$ScratchDir\runs1.txt"
    "shots done: $([int]$clock.Elapsed.TotalSeconds) s"
    foreach ($aaMode in @("smaa", "fsr2")) {
        python "$TreeDir\tools\perf\run.py" dense --wait 0 --tag "aa$aaMode" -- --perf-flip "aa:$aaMode" 2>&1 | Select-String "perf dense_aa$aaMode done"
        python "$TreeDir\tools\perf\flip.py" "dense_aa$aaMode"
    }
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
