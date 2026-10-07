# Batch 2 (one Godot turn): the see-through after its fix; FSR 2's sharpening swept (her running,
# the still camera, the Look); the Look's references; the crowd and the dense fight at 1:1; her
# hair's motion vectors as made, then with the debug include (last frame's run raised half a
# metre, put back after); the Hollow's soft moon shadows flipped (arena art's ask).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\perf5"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a20bdef993e00f26b"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: batch 2, FSR 2 sharpness, see-through, hair vectors"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
$Hair = "$TreeDir\godot\shaders\heroine_hair.gdshaderinc"
python $TurnScript take godot $TurnHolder --wait 600
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    & $GodotConsole --headless --path "$TreeDir\godot" --import *> "$ScratchDir\import2.log"
    "import: exit $LASTEXITCODE, $([int]$clock.Elapsed.TotalSeconds) s"
    python "$ScratchDir\shoot.py" "$ScratchDir\runs2.txt"
    "shots done: $([int]$clock.Elapsed.TotalSeconds) s"
    Copy-Item $Hair "$ScratchDir\heroine_hair.real.gdshaderinc" -Force
    try {
        Copy-Item "$ScratchDir\heroine_hair_debug.gdshaderinc" $Hair -Force
        python "$ScratchDir\shoot.py" "$ScratchDir\runs2_debug.txt"
    }
    finally {
        Copy-Item "$ScratchDir\heroine_hair.real.gdshaderinc" $Hair -Force
        "hair include put back: $((Get-FileHash $Hair).Hash -eq (Get-FileHash "$ScratchDir\heroine_hair.real.gdshaderinc").Hash)"
    }
    "debug shots done: $([int]$clock.Elapsed.TotalSeconds) s"
    & $GodotConsole --path "$TreeDir\godot" --resolution 2560x1440 -- --quick warden --sex female --night hollow --auto --quality high --perf hollow_soft --perf-warm 12 --perf-for 40 --perf-flip softshadow *> "$ScratchDir\hollow_soft.log"
    "hollow: exit $LASTEXITCODE"
    Select-String -Path "$ScratchDir\hollow_soft.log" -Pattern "softshadow|perf hollow" | ForEach-Object { $_.Line }
    python "$TreeDir\tools\perf\flip.py" hollow_soft
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
