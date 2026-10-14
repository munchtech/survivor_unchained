param([string]$tag = 'ab', [string[]]$runs = @(), [switch]$import, [string]$secs = '8', [int]$timeout = 240)
# One godot turn: (an import if asked), then each run "NAME|PRESET|ARGS" at the Look's close-up. Each shot is killed
# after $timeout s and retried once (about 1 in 20 hangs). Pictures: godot/.shots/TAG_NAME.png.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$godot = 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag" --wait 1800 | Out-Null
if ($import) {
    $p = Start-Process $godot -ArgumentList @('--headless', '--path', "$w\godot", '--import') -RedirectStandardOutput "$sc\logs\import_$tag.log" -RedirectStandardError "$sc\logs\import_$tag.err" -PassThru -NoNewWindow
    if (-not $p.WaitForExit(1200 * 1000)) { $p.Kill(); "import KILLED" } else { "import exit $($p.ExitCode)" }
}
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
foreach ($r in $runs) {
    $parts = $r.Split('|')
    $name, $preset = $parts[0], $parts[1]
    $more = if ($parts.Count -gt 2 -and $parts[2]) { $parts[2].Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries) } else { @() }
    $look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail')
    if ($preset -eq 'raw') { $look = @() }
    elseif ($preset -and $preset -ne 'own') {
        $pp = $presets | Where-Object { $_.id -eq $preset }
        $look += @('--preset', $pp.id, '--skin', $pp.skin, '--eyes', $pp.eyes)
    }
    $n = "${tag}_$name"
    $a = @('--path', "$w\godot", '--resolution', '1920x1080', '--', '--shot', $n, '--seconds', $secs) + $look + $more
    foreach ($try in 1, 2) {
        $p = Start-Process $godot -ArgumentList $a -RedirectStandardOutput "$sc\logs\$n.log" -RedirectStandardError "$sc\logs\$n.err" -PassThru -NoNewWindow
        if ($p.WaitForExit($timeout * 1000)) { break }
        $p.Kill(); "[$n] HUNG, killed (try $try)"
    }
    $errs = @(Get-Content "$sc\logs\$n.log", "$sc\logs\$n.err" -ErrorAction SilentlyContinue | Where-Object { $_ -match '(?i)error|exception' -and $_ -notmatch 'RID allocations|RenderingServer::get_singleton' })
    "[$n] $($errs.Count) errors; png $(Test-Path "$w\godot\.shots\$n.png")"
}
python $TP give godot "face: $tag" | Out-Null
"look batch $tag done $(Get-Date -Format HH:mm)"
