# Parallel dependency reads (load A/B and quit-crash check), and the
# photoscans' shimmer before any reimport; inside one Godot turn.
$Scratch = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3"
$Tree = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
$TurnTool = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$Holder = "performance: load A/B and scan shimmer"
python $TurnTool take godot $Holder --wait 40
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    python "$Tree\tools\perf\run.py" hub arena_open --repeat 2 --wait 0 --tag ld2 --builds "old=$Scratch\dll_tiers,dep=$Scratch\dll_dep" -- --perf-warm 3 --perf-for 2 2>&1 | Select-String "^(hub|arena_open) \(|built in|its textures"
    & "$Scratch\crashloop.ps1" -Builds @("dep=$Scratch\dll_dep") -N 10 | Select-String "crashed"
    Copy-Item "$Scratch\dll_dep\SurvivorUnchained.*" "$Tree\godot\.godot\mono\temp\bin\Debug\" -Force
    foreach ($place in @(@("arena_hollow", "--zone", "arena", "--tier", "2", "--seed", "3", "--auto", "idle"), @("verge", "--zone", "verge", "--time", "day", "--x", "0"))) {
        $label = $place[0]
        $rest = $place[1..($place.Length - 1)]
        python "$Scratch\gshot.py" "scanA_$label" --quick warden --sex female @rest --cam 23 --seconds 10 --every 0.0333 --count 8 | Out-Null
    }
    "BATCH RAN"
}
finally {
    python $TurnTool give godot $Holder
}
