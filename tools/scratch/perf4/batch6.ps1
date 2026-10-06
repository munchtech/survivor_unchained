# Batch 6 (one Godot turn), optimised C#: the GC's young generation larger
# (dense, interleaved), the people's first bakes with their textures decoded
# first, her body's laps on repeat entries, and Hollow by Night's dump (stage
# 0 and with its fires lit).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: GC young generation, people bakes, Hollow by Night dump"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
$BinDir = "$TreeDir\godot\.godot\mono\temp\bin\Debug"
python $TurnScript take godot $TurnHolder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    Copy-Item "$ScratchDir\dll_pfopt\SurvivorUnchained.*" $BinDir -Force
    foreach ($round in 1..2) {
        foreach ($gcMode in @("base", "gen0")) {
            if ($gcMode -eq "gen0") { $env:DOTNET_GCgen0size = "0x8000000" } else { Remove-Item Env:DOTNET_GCgen0size -ErrorAction SilentlyContinue }
            python "$TreeDir\tools\perf\run.py" dense --wait 0 --tag "gc$gcMode$round" 2>&1 | Select-String "perf dense_gc.* done|paused [1-9]"
        }
    }
    Remove-Item Env:DOTNET_GCgen0size -ErrorAction SilentlyContinue
    "gc done: $([int]$clock.Elapsed.TotalSeconds) s"
    foreach ($buildName in @("dll_paropt", "dll_pfopt", "dll_paropt", "dll_pfopt")) {
        Copy-Item "$ScratchDir\$buildName\SurvivorUnchained.*" $BinDir -Force
        & $GodotConsole --path "$TreeDir\godot" --resolution 2560x1440 -- --quick warden --sex female --zone arena --tier 2 --people dead --auto --quality high --perf "deadbake" --perf-warm 2 --perf-for 1 --vat-fresh --vat-probe --log *> "$ScratchDir\deadbake_$buildName.log"
        "== $buildName"
        Get-Content "$ScratchDir\deadbake_$buildName.log" | Select-String "baked |crowd's kinds|built in" | ForEach-Object { $_.Line }
    }
    Copy-Item "$ScratchDir\dll_pfopt\SurvivorUnchained.*" $BinDir -Force
    python "$TreeDir\tools\perf\run.py" hub --wait 0 --tag laps2 -- --perf-warm 26 --perf-for 2 --travel "verge@6,waystation@14,verge@22" 2>&1 | Select-String "her body|her outfit|her hair|stood up|its people|built in"
    "laps done: $([int]$clock.Elapsed.TotalSeconds) s"
    foreach ($stageNo in @("0", "9")) {
        & $GodotConsole --path "$TreeDir\godot" --resolution 2560x1440 -- --quick warden --sex female --night hollow --stage $stageNo --auto --quality high --perf "hollowdump$stageNo" --perf-warm 10 --perf-for 4 --perf-dump *> "$ScratchDir\hollowdump$stageNo.log"
        "== hollow dump, stage $stageNo"
        Get-Content "$ScratchDir\hollowdump$stageNo.log" | Select-String "perf dump|perf hollowdump.* done" | ForEach-Object { $_.Line }
    }
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    Remove-Item Env:DOTNET_GCgen0size -ErrorAction SilentlyContinue
    python $TurnScript give godot $TurnHolder
}
