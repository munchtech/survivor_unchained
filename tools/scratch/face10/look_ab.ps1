param([string]$tag = 'ab', [string[]]$runs = @(), [switch]$import, [string]$secs = '8', [string]$extra = '')
# One godot turn: (an import if asked), then each run "NAME|PRESET|ARGS..." at the Look's close-up (the Look's
# default framing, eyes open, ponytail): PRESET own or a face id (its skin and eyes from presets.json); ARGS more
# switches, space-separated (e.g. --head-paint C:\x.jpg --rig-white --turn 40). Pictures: godot/.shots/TAG_NAME.png.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abe65bc929823a791'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\face10'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
New-Item -ItemType Directory -Force "$sc\logs" | Out-Null
python $TP take godot "face: $tag" --wait 900 | Out-Null
if ($import) {
    & 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\logs\import_$tag.log"
    "import exit $LASTEXITCODE"
}
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
foreach ($r in $runs) {
    $parts = $r.Split('|')
    $name, $preset = $parts[0], $parts[1]
    $more = if ($parts.Count -gt 2 -and $parts[2]) { $parts[2].Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries) } else { @() }
    $look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail')
    if ($preset -and $preset -ne 'own') {
        $p = $presets | Where-Object { $_.id -eq $preset }
        $look += @('--preset', $p.id, '--skin', $p.skin, '--eyes', $p.eyes)
    }
    if ($extra) { $more += $extra.Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries) }
    & "$sc\shot.ps1" "${tag}_$name" $secs @look @more
}
python $TP give godot "face: $tag" | Out-Null
"look batch $tag done $(Get-Date -Format HH:mm)"
