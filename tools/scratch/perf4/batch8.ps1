# Batch 8 (one Godot turn), optimised C#: what the dense fight's garbage is
# made of (allocation samples by type), and the four arenas' dumps beside
# Hollow by Night's (shadow casters, instances, lights).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: dense garbage by type, arena dumps"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
$BinDir = "$TreeDir\godot\.godot\mono\temp\bin\Debug"
python $TurnScript take godot $TurnHolder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    Copy-Item "$ScratchDir\dll_alloc\SurvivorUnchained.*" $BinDir -Force
    $LateBuild = "oathblade:8,seeking_motes:8,cinderfall:8,arcweb:7,knifestorm:7,hallowed_ring:7,+might:3,+haste:2"
    & $GodotConsole --path "$TreeDir\godot" --resolution 2560x1440 -- --quick warden --sex female --zone arena --tier 3 --minute 27.5 --give $LateBuild --auto --quality high --perf "dense_allocs" --perf-warm 25 --perf-for 40 --perf-allocs *> "$ScratchDir\dense_allocs.log"
    Get-Content "$ScratchDir\dense_allocs.log" | Select-String "perf alloc|allocated \(sampled\)|young GC|dense_allocs done" | ForEach-Object { $_.Line }
    "allocs done: $([int]$clock.Elapsed.TotalSeconds) s"
    foreach ($folk in @("pack", "dead", "lamplings", "kerchiefs")) {
        & $GodotConsole --path "$TreeDir\godot" --resolution 2560x1440 -- --quick warden --sex female --zone arena --tier 2 --seed 3 --people $folk --auto --quality high --perf "dump_$folk" --perf-warm 10 --perf-for 4 --perf-dump *> "$ScratchDir\dump_$folk.log"
        "== $folk"
        Get-Content "$ScratchDir\dump_$folk.log" | Select-String "perf dump: World|done:" | ForEach-Object { $_.Line }
    }
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
