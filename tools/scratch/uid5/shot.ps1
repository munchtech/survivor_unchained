param([string]$name, [string]$secs, [Parameter(ValueFromRemainingArguments = $true)] $rest)
# The UI design lead's shot: the game at 1920x1080, a picture after SECS, its focus audited.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid5'
$wt = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aab47bfdab5955dac\godot'
$godot = 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe'
New-Item -ItemType Directory -Force (Join-Path $sp 'logs') | Out-Null
$log = Join-Path $sp "logs\log_$name.txt"
$eng = @(); if ($env:SHOT_ENGINE) { $eng = $env:SHOT_ENGINE.Split(' ') }; $args2 = @('--path', $wt, '--resolution', '1920x1080') + $eng + @('--', '--shot', $name, '--seconds', $secs, '--navcheck') + $rest
& $godot @args2 *> $log
$lines = Get-Content $log
$errs = $lines | Where-Object { $_ -match '(?i)error|exception' -and $_ -notmatch 'RID allocations|RenderingServer::get_singleton|leaked at exit|CategoryInfo|FullyQualifiedErrorId|NativeCommandError' }
$saved = ($lines | Where-Object { $_ -match '^(?i)saved' } | Select-Object -First 1)
"[$name] $(@($errs).Count) errors; $saved"
$errs | Where-Object { $_ -notmatch '^\s*at ' } | Group-Object | Select-Object -First 6 | ForEach-Object { "  $($_.Count) $($_.Name)" }
$lines | Where-Object { $_ -match '^nav ' } | Select-Object -First 12




