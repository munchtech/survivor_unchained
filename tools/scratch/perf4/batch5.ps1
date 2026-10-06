# Batch 5 (one Godot turn), optimised C# with the finer parts: the dense
# fight's hitches, her build's laps on repeat entries, the frame a journey
# starts in, and Hollow by Night (plain, then its fires, its lights' shadows
# and its pieces flipped).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: dense hitches, her laps, Hollow by Night"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
$OptBuild = "opt=$ScratchDir\dll_instopt"
python $TurnScript take godot $TurnHolder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    python "$TreeDir\tools\perf\run.py" dense --repeat 3 --wait 0 --tag hitch --builds $OptBuild 2>&1 | Select-String "^dense \(|perf dense_hitch|hitch"
    "dense done: $([int]$clock.Elapsed.TotalSeconds) s"
    python "$TreeDir\tools\perf\run.py" hub --wait 0 --tag laps --builds $OptBuild -- --perf-warm 34 --perf-for 2 --travel "verge@6,waystation@14,verge@22,waystation@30" 2>&1 | Select-String "built in|lap "
    python "$TreeDir\tools\perf\run.py" hub --wait 0 --tag go --builds $OptBuild -- --perf-warm 3 --perf-for 14 --travel "verge@8" 2>&1 | Select-String "hitch|built in"
    "hops done: $([int]$clock.Elapsed.TotalSeconds) s"
    foreach ($flipWhat in @("", "fires", "lampshadows", "pieces")) {
        $runName = if ($flipWhat) { "hollownight_$flipWhat" } else { "hollownight" }
        $flipArgs = if ($flipWhat) { @("--perf-flip", $flipWhat) } else { @() }
        & $GodotConsole --path "$TreeDir\godot" --resolution 2560x1440 -- --quick warden --sex female --night hollow --auto --quality high --perf $runName --perf-warm 12 --perf-for 30 @flipArgs *> "$ScratchDir\$runName.log"
        "== $runName"
        Get-Content "$ScratchDir\$runName.log" | Select-String "perf $runName done|built in|hitches" | ForEach-Object { $_.Line }
        if ($flipWhat) { python "$TreeDir\tools\perf\flip.py" $runName }
    }
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}
