# Medium with SMAA: her edges (pictures, flicker) and its cost; inside one Godot turn.
$P = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3"
$W = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
$T = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$who = "performance: medium with smaa"
python $T take godot $who --wait 40
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
function Run($scen, $tag, $build, $flip, $more = @()) {
    $a = @("$W\tools\perf\run.py", $scen, "--wait", "0", "--tag", $tag, "--builds", "x=$P\$build", "--") + $more + @("--perf-flip", $flip)
    python @a 2>&1 | Select-String "GPU before|no result" | ForEach-Object { "  $scen ${tag}: $($_.Line.Trim())" }
}
try {
    python "$P\her_shots.py" medsmaa "$P\dll_medsmaa" --quality medium | Out-Null
    python "$P\her_shots.py" med3 "$P\dll_aa" --quality medium | Out-Null
    "pictures taken"
    Run "dense" "m_smaa" "dll_medsmaa" "smaa" @("--quality", "medium")
    Run "dense" "m_msaa2x_b" "dll_med2x" "msaa" @("--quality", "medium")
    "BATCH RAN"
}
finally {
    python $T give godot $who
}
