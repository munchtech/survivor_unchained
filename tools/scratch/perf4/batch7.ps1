# Batch 7 (one Godot turn), optimised C#: her body held for the session (laps
# on repeat entries), the synth's kept buffers (dense: garbage, GCs, the
# draft's UI part), and a quit check over journeys (exit codes).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: her body held, synth garbage, quit check"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
$BinDir = "$TreeDir\godot\.godot\mono\temp\bin\Debug"
python $TurnScript take godot $TurnHolder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    python "$TreeDir\tools\perf\run.py" hub --wait 0 --tag held --builds "opt=$ScratchDir\dll_hold" -- --perf-warm 26 --perf-for 2 --travel "verge@6,waystation@14,verge@22" 2>&1 | Select-String "her body|her outfit|her hair|stood up|built in"
    "laps done: $([int]$clock.Elapsed.TotalSeconds) s"
    foreach ($round in 1..2) {
        foreach ($buildPair in @("old=$ScratchDir\dll_pfopt", "new=$ScratchDir\dll_hold")) {
            python "$TreeDir\tools\perf\run.py" dense --wait 0 --tag "syn$round" --builds $buildPair 2>&1 | Select-String "perf dense_syn.* done|perf dense_syn.* alloc by|young GC|draftui [1-9]|paused [1-9]"
        }
    }
    "dense done: $([int]$clock.Elapsed.TotalSeconds) s"
    Copy-Item "$ScratchDir\dll_hold\SurvivorUnchained.*" $BinDir -Force
    $crashCount = 0
    foreach ($runNo in 1..10) {
        & $GodotConsole --path "$TreeDir\godot" --resolution 2560x1440 --fixed-fps 60 -- --shot "quitcheck" --quick warden --sex female --zone waystation --time day --quality high --seconds 16 --cam 30 --travel "verge@4,waystation@10" *> "$ScratchDir\quit_$runNo.log"
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) { $crashCount++ }
        "quit run $runNo exit $exitCode"
    }
    "quit check: $crashCount of 10 crashed"
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
