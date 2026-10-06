param([string]$Build, [string]$Tag, [int]$N = 8)
$S = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf2"
Set-Location "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7145e18b3eb78294"
Copy-Item "$Build\SurvivorUnchained.*" godot\.godot\mono\temp\bin\Debug\ -Force
foreach ($i in 1..$N) {
    & "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe" --path godot --resolution 2560x1440 --fixed-fps 60 -- --shot "cl_$Tag" --quick warden --sex female --zone waystation --time day --quality high --seconds 10 --cam 30 *> "$S\cl_${Tag}_$i.log"
    "$Tag run $i exit $LASTEXITCODE"
}
"LOOP DONE"
