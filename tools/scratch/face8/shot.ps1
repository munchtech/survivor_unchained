param([string]$name, [string]$secs = "6", [Parameter(ValueFromRemainingArguments = $true)] $rest)
# The game in my worktree at 1920x1080, a picture after SECS: godot/.shots/NAME.png (errors summarised).
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$wt = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\godot'
$godot = 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe'
New-Item -ItemType Directory -Force (Join-Path $sp 'logs') | Out-Null
$log = Join-Path $sp "logs\log_$name.txt"
$args2 = @('--path', $wt, '--resolution', '1920x1080', '--', '--shot', $name, '--seconds', $secs) + $rest
& $godot @args2 *> $log
$lines = Get-Content $log
$errs = $lines | Where-Object { $_ -match '(?i)error|exception' -and $_ -notmatch 'RID allocations|RenderingServer::get_singleton' }
"[$name] $(@($errs).Count) errors"
$errs | Where-Object { $_ -notmatch '^\s*at ' } | Group-Object | Select-Object -First 6 | ForEach-Object { "  $($_.Count) $($_.Name)" }

