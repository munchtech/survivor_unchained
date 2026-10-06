# Her pictures at each tier and resolution step, and the resolution steps'
# costs by paired flips; inside one Godot turn (tools/turn.py).
$P = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3"
$W = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
$T = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$who = "performance: tier pictures and FSR"
python $T take godot $who --wait 40
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
function Run($scen, $tag, $build, $flip, $more = @()) {
    $a = @("$W\tools\perf\run.py", $scen, "--wait", "0", "--tag", $tag, "--builds", "x=$P\$build", "--") + $more + @("--perf-flip", $flip)
    python @a 2>&1 | Select-String "GPU before|no result" | ForEach-Object { "  $scen ${tag}: $($_.Line.Trim())" }
}
try {
    python "$P\her_shots.py" hi "$P\dll_tiers" --quality high | Out-Null
    python "$P\her_shots.py" med "$P\dll_tiers" --quality medium | Out-Null
    python "$P\her_shots.py" lowold "$P\dll_cur" --quality low | Out-Null
    python "$P\her_shots.py" lownew "$P\dll_tiers" --quality low | Out-Null
    "pictures of the tiers taken"
    foreach ($step in "quality", "balanced", "performance") {
        python "$P\her_shots.py" "fsr$step" "$P\dll_tiers" --quality high --scale $step | Out-Null
        Run "dense" "s_$step" "dll_tiers" "scale:$step"
    }
    "BATCH RAN"
}
finally {
    python $T give godot $who
}
