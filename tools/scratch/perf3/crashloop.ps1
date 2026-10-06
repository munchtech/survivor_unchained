param([string[]]$Builds, [int]$N = 20, [string]$Zone = "waystation", [int]$Seconds = 10)
# The Waystation shot N times per build, builds interleaved run by run, and
# each run's exit code: 0 is a clean quit, -1073741819 (0xC0000005) the crash.
# -Builds tag=dir,tag=dir
$S = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3"
$W = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
$bin = "$W\godot\.godot\mono\temp\bin\Debug"
$crashes = @{}
foreach ($i in 1..$N) {
    foreach ($b in $Builds) {
        $tag, $dir = $b.Split("=", 2)
        Copy-Item "$dir\SurvivorUnchained.*" $bin -Force
        $t0 = Get-Date
        & "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe" --path "$W\godot" --resolution 2560x1440 --fixed-fps 60 -- --shot "cl_$tag" --quick warden --sex female --zone $Zone --time day --quality high --seconds $Seconds --cam 30 *> "$S\cl_${tag}_$i.log"
        $code = $LASTEXITCODE
        if ($code -ne 0) { $crashes[$tag] = 1 + [int]$crashes[$tag] }
        "{0} run {1} exit {2} in {3:n0}s" -f $tag, $i, $code, ((Get-Date) - $t0).TotalSeconds
    }
}
foreach ($b in $Builds) { $tag = $b.Split("=")[0]; "{0}: {1} of {2} crashed" -f $tag, [int]$crashes[$tag], $N }
"LOOP DONE"
