param([string]$tag = 'v11c', [switch]$nolook)
# One godot turn: every face under the white rig (tones, irises, brows) and at the Look's close-up (the ten-face
# sheet), her own included.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag faces" --wait 300 | Out-Null
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail')
& "$sc\shot.ps1" "${tag}_white" 8 @look --rig-white | Out-Null
if (-not $nolook) { & "$sc\shot.ps1" "${tag}_pony" 8 @look | Out-Null; & "$sc\shot.ps1" "${tag}_long" 8 --new --sex female --step 1 --part 1 --open-eyes --hair long | Out-Null }
foreach ($p in $presets) {
    if ($p.id -eq 'own') { continue }
    & "$sc\shot.ps1" "${tag}_w_$($p.id)" 8 @look --rig-white --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
    if (-not $nolook) { & "$sc\shot.ps1" "${tag}_p_$($p.id)" 8 @look --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null }
}
python $TP give godot "face: $tag faces" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
