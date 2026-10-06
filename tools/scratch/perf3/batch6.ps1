# The photoscans before and after mipmaps and compression: still arena
# pictures (crowd, effects and HUD out), the reimport, the same pictures, and
# the arena's load; inside one Godot turn.
$Scratch = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3"
$Tree = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
$TurnTool = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$Holder = "performance: photoscan mipmaps A/B"
$GodotExe = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
python $TurnTool take godot $Holder --wait 40
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
function Shots($stage) {
    Copy-Item "$Scratch\dll_fx\SurvivorUnchained.*" "$Tree\godot\.godot\mono\temp\bin\Debug\" -Force
    foreach ($who in @("pack", "dead")) {
        python "$Scratch\gshot.py" "scan${stage}_$who" --quick warden --sex female --zone arena --tier 2 --seed 3 --people $who --auto idle --cam 23 --seconds 6 --every 0.0333 --count 8 --perf x --perf-warm 1000 --perf-off crowd,fx,hud | Out-Null
    }
}
try {
    Shots "A"
    "A taken"
    python "$Tree\tools\perf\run.py" arena_open --repeat 2 --wait 0 --tag scanA --builds "fx=$Scratch\dll_fx" -- --perf-warm 3 --perf-for 2 --people dead 2>&1 | Select-String "lap flora|built in"
    $saved = Get-Location
    & $GodotExe --headless --path "$Tree\godot" --import *> "$Scratch\import_world.log"
    "reimported: exit $LASTEXITCODE"
    Shots "B"
    "B taken"
    python "$Tree\tools\perf\run.py" arena_open --repeat 2 --wait 0 --tag scanB --builds "fx=$Scratch\dll_fx" -- --perf-warm 3 --perf-for 2 --people dead 2>&1 | Select-String "lap flora|built in"
    "BATCH RAN"
}
finally {
    python $TurnTool give godot $Holder
}
