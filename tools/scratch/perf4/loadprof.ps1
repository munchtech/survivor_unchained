param([string]$ProfName = "arena", [string]$BuildDir = "dll_new", [string[]]$PlayArgs = @("--quick", "warden", "--sex", "female", "--zone", "arena", "--tier", "2", "--auto"), [int]$TraceSeconds = 30, [int]$WarmFor = 40, [switch]$NoTurn)
# A CPU profile (dotnet-trace, sampled) of a zone's build: the GUI exe started
# with a long warm-up so it outlives the trace; inside one Godot turn (unless
# the caller already holds one: -NoTurn).
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: load profile $ProfName"
if (!$NoTurn) {
    python $TurnScript take godot $TurnHolder --wait 30
    if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
}
try {
    Copy-Item "$ScratchDir\$BuildDir\SurvivorUnchained.*" "$TreeDir\godot\.godot\mono\temp\bin\Debug\" -Force
    $launchArgs = @("--path", "$TreeDir\godot", "--resolution", "2560x1440", "--log-file", "$ScratchDir\prof_$ProfName.log", "--") + $PlayArgs + @("--perf", "prof_$ProfName", "--perf-warm", "$WarmFor", "--perf-for", "2")
    $gameProc = Start-Process "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64.exe" -ArgumentList $launchArgs -PassThru
    Start-Sleep -Milliseconds 1500
    & "C:\Users\munch\.dotnet\tools\dotnet-trace.exe" collect -p $gameProc.Id --format speedscope -o "$ScratchDir\prof_$ProfName.nettrace" --duration "00:00:$TraceSeconds" 2>&1 | Select-Object -Last 3
    if (!$gameProc.WaitForExit(120000)) { $gameProc.Kill() }
    Get-Content "$ScratchDir\prof_$ProfName.log" | Select-String "perf lap|built in|baked|read |parts\+lods" | ForEach-Object { $_.Line }
}
finally {
    if (!$NoTurn) { python $TurnScript give godot $TurnHolder }
}
