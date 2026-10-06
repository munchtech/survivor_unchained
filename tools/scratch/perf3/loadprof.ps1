param([string]$Name = "arena", [string]$Build = "dll_tiers", [string[]]$GameArgs = @("--quick", "warden", "--sex", "female", "--zone", "arena", "--tier", "2", "--auto"), [int]$Seconds = 30)
# A CPU profile (dotnet-trace, sampled) of a zone's build: the GUI exe started
# with a long warm-up so it outlives the trace; inside one Godot turn.
$Scratch = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3"
$Tree = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
$TurnTool = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$Holder = "performance: load profile $Name"
python $TurnTool take godot $Holder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    Copy-Item "$Scratch\$Build\SurvivorUnchained.*" "$Tree\godot\.godot\mono\temp\bin\Debug\" -Force
    $gameArgs = @("--path", "$Tree\godot", "--resolution", "2560x1440", "--log-file", "$Scratch\prof_$Name.log", "--") + $GameArgs + @("--perf", "prof_$Name", "--perf-warm", "40", "--perf-for", "2")
    $proc = Start-Process "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64.exe" -ArgumentList $gameArgs -PassThru
    Start-Sleep -Milliseconds 1500
    & "C:\Users\munch\.dotnet\tools\dotnet-trace.exe" collect -p $proc.Id --format speedscope -o "$Scratch\prof_$Name.nettrace" --duration "00:00:$Seconds" 2>&1 | Select-Object -Last 3
    if (!$proc.WaitForExit(90000)) { $proc.Kill() }
    Get-Content "$Scratch\prof_$Name.log" | Select-String "perf lap|built in" | ForEach-Object { $_.Line }
}
finally {
    python $TurnTool give godot $Holder
}
