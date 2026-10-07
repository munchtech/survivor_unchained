# Batch 3 (one Godot turn): today's references on the fixed scene; FSR 2 (sharpening off) with
# her hair, brows and lashes cut by a threshold moved every frame; the Look at the face lead's
# scatter 0.1; the see-through's second fix; frame times of FSR 2 (sharpening off) against
# today's TAA with MSAA in the dense fight (paired flip).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\perf5"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a20bdef993e00f26b"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: batch 3, FSR 2 with coverage, references, see-through"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
python $TurnScript take godot $TurnHolder --wait 600
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    & $GodotConsole --headless --path "$TreeDir\godot" --import *> "$ScratchDir\import3.log"
    "import: exit $LASTEXITCODE, $([int]$clock.Elapsed.TotalSeconds) s"
    python "$ScratchDir\shoot.py" "$ScratchDir\runs3.txt"
    "shots done: $([int]$clock.Elapsed.TotalSeconds) s"
    python "$TreeDir\tools\perf\run.py" dense --wait 120 --tag ffc -- --perf-flip aa:fsr2 --fsr-sharpness 2.0 --coverage 2>&1 | Select-String "GPU before|no result|error|Error"
    python "$TreeDir\tools\perf\flip.py" dense_ffc
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
