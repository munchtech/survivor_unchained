# Her outfits and the quality tiers, measured with paired flips, then her
# pictures at each tier; all inside one Godot turn (tools/turn.py).
$S = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3"
$W = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
$T = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$who = "performance: tiers and her outfits"
python $T take godot $who --wait 40
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
function Run($scen, $tag, $build, $flip, $more = @()) {
    $a = @("$W\tools\perf\run.py", $scen, "--wait", "0", "--tag", $tag, "--builds", "x=$S\$build", "--") + $more + @("--perf-flip", $flip)
    python @a 2>&1 | Select-String "GPU before|no result" | ForEach-Object { "  $scen ${tag}: $($_.Line.Trim())" }
}
try {
    foreach ($c in "warden", "reaver", "arcanist", "stalker") { Run "hub" "her_$c" "dll_cur" "her" @("--quick", $c) }
    foreach ($c in "warden", "reaver") { Run "dense" "her_$c" "dll_cur" "her" @("--quick", $c) }
    Run "dense" "q_med" "dll_cur" "quality:medium"
    Run "dense" "q_lowold" "dll_cur" "quality:low"
    Run "dense" "q_lownew" "dll_tiers" "quality:low"
    foreach ($s in "quality", "balanced", "performance") { Run "dense" "s_$s" "dll_cur" "scale:$s" }
    python "$S\her_shots.py" hi "$S\dll_tiers" --quality high | Out-Null
    python "$S\her_shots.py" med "$S\dll_tiers" --quality medium | Out-Null
    python "$S\her_shots.py" lowold "$S\dll_cur" --quality low | Out-Null
    python "$S\her_shots.py" lownew "$S\dll_tiers" --quality low | Out-Null
    "BATCH RAN"
}
finally {
    python $T give godot $who
}
