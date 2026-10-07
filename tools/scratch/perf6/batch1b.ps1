# Batch 1 (one Godot turn): the import; her in motion under each way of smoothing (164 Hz,
# drawn between steps or not); the crowd; still-camera shimmer; the Look's close-up; the
# see-through old and new; frame times of SMAA, FSR2 and TAA without MSAA against TAA with
# it in the dense fight (paired flips).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\perf5"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a20bdef993e00f26b"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: AA A/B batch, see-through, frame times"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
python $TurnScript take godot $TurnHolder --wait 600
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    & $GodotConsole --headless --path "$TreeDir\godot" --import *> "$ScratchDir\import1b.log"
    "import: exit $LASTEXITCODE, $([int]$clock.Elapsed.TotalSeconds) s"
    Remove-Item "$TreeDir\godot\.shots\her_at.txt" -ErrorAction SilentlyContinue
    python "$ScratchDir\shoot.py" "$ScratchDir\runs1b.txt"
    "shots done: $([int]$clock.Elapsed.TotalSeconds) s"
    foreach ($flip in @("aa:smaa", "aa:fsr2", "msaa")) {
        $tag = "f" + ($flip -replace "aa:", "")
        python "$TreeDir\tools\perf\run.py" dense --wait 120 --tag $tag -- --perf-flip $flip 2>&1 | Select-String "GPU before|no result|error|Error"
        python "$TreeDir\tools\perf\flip.py" "dense_$tag"
    }
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
