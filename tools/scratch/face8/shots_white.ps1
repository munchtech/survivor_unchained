param([string]$tag = 'v10a')
# Every face under the Look's rig made white (--rig-white): her (TAG_white) and each preset (TAG_w_<id>), for
# tone_fit.py. One godot turn.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: $tag white shots" --wait 120 | Out-Null
$base = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--open-eyes', '--rig-white')
& "$sc\shot.ps1" "${tag}_white" 8 @base | Out-Null
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
foreach ($p in $presets) {
    if ($p.id -eq 'own') { continue }
    & "$sc\shot.ps1" "${tag}_w_$($p.id)" 8 @base --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
}
python $T give godot "face: $tag white shots" | Out-Null
"white shots done $(Get-Date -Format HH:mm)"
