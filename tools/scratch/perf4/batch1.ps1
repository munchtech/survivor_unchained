# Batch 1 (one Godot turn): the A state's import (photoscans as before), the
# first-launch VAT bake with the sweep, the A pictures, and --travel with the
# effects made per place (base) against once a session (new).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: photoscans A, VAT sweep, travel A/B"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
$BinDir = "$TreeDir\godot\.godot\mono\temp\bin\Debug"
$VatDir = "$env:APPDATA\SurvivorUnchainedPerf\vat"
function VatSummary { ((Get-ChildItem $VatDir | ForEach-Object { ($_.Name -split '\.')[-2] } | Group-Object | ForEach-Object { "$($_.Name)x$($_.Count)" }) -join ' ') + ", MB " + [int]((Get-ChildItem $VatDir | Measure-Object Length -Sum).Sum / 1MB) }
python $TurnScript take godot $TurnHolder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    & $GodotConsole --headless --path "$TreeDir\godot" --import *> "$ScratchDir\importA.log"
    "import A: exit $LASTEXITCODE, $([int]$clock.Elapsed.TotalSeconds) s"
    # The A set of the photoscans' imports, kept for interleaved load runs later.
    New-Item -ItemType Directory -Force "$ScratchDir\scnA" | Out-Null
    Copy-Item "$TreeDir\godot\.godot\imported\*.glb-*.scn" "$ScratchDir\scnA\" -Force
    Copy-Item "$ScratchDir\dll_new\SurvivorUnchained.*" $BinDir -Force
    "VAT before: " + (VatSummary)
    & $GodotConsole --path "$TreeDir\godot" --resolution 2560x1440 -- --quick warden --sex female --zone arena --tier 2 --auto --quality high --perf vatfresh --perf-warm 3 --perf-for 2 --vat-probe --log *> "$ScratchDir\vatfresh.log"
    "VAT after: " + (VatSummary)
    foreach ($camDist in @("23", "31")) {
        foreach ($folk in @("pack", "dead")) {
            python "$ScratchDir\gshot.py" "scanA_${folk}_$camDist" --quick warden --sex female --zone arena --tier 2 --seed 3 --people $folk --auto idle --cam $camDist --seconds 6 --every 0.0333 --count 8 --perf x --perf-warm 1000 --perf-off crowd,fx,hud | Out-Null
        }
        python "$ScratchDir\gshot.py" "scanA_verge_$camDist" --quick warden --sex female --zone verge --time day --x 0 --auto idle --cam $camDist --seconds 8 --every 0.0333 --count 8 --perf x --perf-warm 1000 --perf-off crowd,fx,hud | Out-Null
    }
    "A shots taken: $([int]$clock.Elapsed.TotalSeconds) s"
    python "$TreeDir\tools\perf\run.py" arena_open --repeat 2 --wait 0 --tag travel --builds "base=$ScratchDir\dll_base,new=$ScratchDir\dll_new" -- --perf-warm 22 --perf-for 2 --travel waystation@6 2>&1 | Select-String "^arena_open \(|built in|lap "
    Copy-Item "$ScratchDir\dll_new\SurvivorUnchained.*" $BinDir -Force
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
