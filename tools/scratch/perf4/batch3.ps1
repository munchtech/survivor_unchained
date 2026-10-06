# Batch 3 (one Godot turn): the C# as players run it (optimised) against the
# editor's debug build: the first-launch VAT bakes, the densest fight (and a
# CPU profile of its main-thread spikes), and repeat entries of the Waystation
# and the Verge (--travel chained).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: optimised C#, bakes, dense spikes, repeat entries"
$LateBuild = "oathblade:8,seeking_motes:8,cinderfall:8,arcweb:7,knifestorm:7,hallowed_ring:7,+might:3,+haste:2"
$BothBuilds = "dbg=$ScratchDir\dll_chain,opt=$ScratchDir\dll_opt"
python $TurnScript take godot $TurnHolder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    python "$TreeDir\tools\perf\run.py" arena_open --repeat 2 --wait 0 --tag fresh --builds $BothBuilds -- --perf-warm 3 --perf-for 2 --vat-fresh --log 2>&1 | Select-String "^arena_open \(|baked|stood up|built in"
    "bakes timed: $([int]$clock.Elapsed.TotalSeconds) s"
    python "$TreeDir\tools\perf\run.py" dense --repeat 2 --wait 0 --tag spikes --builds $BothBuilds 2>&1 | Select-String "^dense \(|perf dense_spikes|hitch"
    "dense runs: $([int]$clock.Elapsed.TotalSeconds) s"
    & "$ScratchDir\loadprof.ps1" -ProfName "dense" -BuildDir "dll_opt" -PlayArgs @("--quick", "warden", "--sex", "female", "--zone", "arena", "--tier", "3", "--minute", "27.5", "--give", $LateBuild, "--auto", "--log") -TraceSeconds 59 -WarmFor 62 -NoTurn
    "profile taken: $([int]$clock.Elapsed.TotalSeconds) s"
    python "$TreeDir\tools\perf\run.py" hub --wait 0 --tag hops --builds "opt=$ScratchDir\dll_opt" -- --perf-warm 34 --perf-for 2 --travel "verge@6,waystation@14,verge@22,waystation@30" 2>&1 | Select-String "built in|lap "
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
