# Batch 2 (one Godot turn): the photoscans reimported with mipmaps and BC7/BC5
# (B), the B pictures, then the arena's and the Verge's loads with the A and B
# imports swapped in turn (interleaved, so contention weighs on both alike).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: photoscans B and load A/B"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
$ImportedDir = "$TreeDir\godot\.godot\imported"
python $TurnScript take godot $TurnHolder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    & $GodotConsole --headless --path "$TreeDir\godot" --import *> "$ScratchDir\importB.log"
    "import B: exit $LASTEXITCODE, $([int]$clock.Elapsed.TotalSeconds) s"
    New-Item -ItemType Directory -Force "$ScratchDir\scnB" | Out-Null
    Copy-Item "$ImportedDir\*.glb-*.scn" "$ScratchDir\scnB\" -Force
    foreach ($camDist in @("23", "31")) {
        foreach ($folk in @("pack", "dead")) {
            python "$ScratchDir\gshot.py" "scanB_${folk}_$camDist" --quick warden --sex female --zone arena --tier 2 --seed 3 --people $folk --auto idle --cam $camDist --seconds 6 --every 0.0333 --count 8 --perf x --perf-warm 1000 --perf-off crowd,fx,hud | Out-Null
        }
        python "$ScratchDir\gshot.py" "scanB_verge_$camDist" --quick warden --sex female --zone verge --time day --x 0 --auto idle --cam $camDist --seconds 8 --every 0.0333 --count 8 --perf x --perf-warm 1000 --perf-off crowd,fx,hud | Out-Null
    }
    "B shots taken: $([int]$clock.Elapsed.TotalSeconds) s"
    foreach ($round in 1..3) {
        foreach ($importSet in @("A", "B")) {
            Copy-Item "$ScratchDir\scn$importSet\*.scn" "$ImportedDir\" -Force
            "--- round $round, imports $importSet"
            python "$TreeDir\tools\perf\run.py" arena_open verge --wait 0 --tag "ld$importSet$round" -- --perf-warm 3 --perf-for 2 2>&1 | Select-String "built in|lap flora|lap props|lap landmarks|lap arena edge"
        }
    }
    Copy-Item "$ScratchDir\scnB\*.scn" "$ImportedDir\" -Force
    # A CPU profile: the arena's first build (her, the fresh bakes), then the
    # Waystation's second, warm one.
    & "$ScratchDir\loadprof.ps1" -ProfName "fresh_travel" -BuildDir "dll_new" -PlayArgs @("--quick", "warden", "--sex", "female", "--zone", "arena", "--tier", "2", "--auto", "--vat-fresh", "--vat-probe", "--log", "--travel", "waystation@8") -TraceSeconds 45 -WarmFor 40 -NoTurn
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
