# Batch 4 (one Godot turn): the bakes skinned on worker threads against the old
# single-thread bake: the same bytes (beasts and people), and the time, in the
# Debug and the optimised C#.
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: parallel VAT bake check"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
$BinDir = "$TreeDir\godot\.godot\mono\temp\bin\Debug"
$VatDir = "$env:APPDATA\SurvivorUnchainedPerf\vat"
python $TurnScript take godot $TurnHolder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    foreach ($buildName in @("dll_chain", "dll_par", "dll_opt", "dll_paropt")) {
        Copy-Item "$ScratchDir\$buildName\SurvivorUnchained.*" $BinDir -Force
        foreach ($folk in @("pack", "dead")) {
            $logFile = "$ScratchDir\bake_${buildName}_$folk.log"
            & $GodotConsole --path "$TreeDir\godot" --resolution 2560x1440 -- --quick warden --sex female --zone arena --tier 2 --people $folk --auto --quality high --perf "bake_$buildName" --perf-warm 2 --perf-for 1 --vat-fresh --vat-probe --log *> $logFile
            "== $buildName $folk"
            Get-Content $logFile | Select-String "baked |parts\+lods|crowd's kinds" | ForEach-Object { $_.Line }
            New-Item -ItemType Directory -Force "$ScratchDir\vat_${buildName}_$folk" | Out-Null
            Copy-Item "$VatDir\*.bin" "$ScratchDir\vat_${buildName}_$folk\" -Force
        }
    }
    # Her files' load: windowed (with the renderer's uploads) and headless (without), twice each.
    foreach ($round in 1..2) {
        "== her load, windowed, round $round"
        & $GodotConsole --path "$TreeDir\godot" --resolution 1280x720 -s "$ScratchDir\herload.gd" 2>&1 | Select-String "MB read"
        "== her load, headless, round $round"
        & $GodotConsole --headless --path "$TreeDir\godot" -s "$ScratchDir\herload.gd" 2>&1 | Select-String "MB read"
    }
    "BATCH RAN"
}
finally {
    Copy-Item "$ScratchDir\dll_paropt\SurvivorUnchained.*" $BinDir -Force
    python $TurnScript give godot $TurnHolder
}
