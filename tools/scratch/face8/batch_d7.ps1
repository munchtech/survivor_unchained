param([string]$tag = 'v11d')
# One godot turn: every face under the white rig (the irises' third fit), her own at the Look with her neck's soft
# mottle at two strengths, and the book by day (her lamp at half).
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag irises and mottle" --wait 300 | Out-Null
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail')
& "$sc\shot.ps1" "${tag}_white" 8 @look --rig-white | Out-Null
foreach ($p in $presets) {
    if ($p.id -eq 'own') { continue }
    & "$sc\shot.ps1" "${tag}_w_$($p.id)" 8 @look --rig-white --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
}
& "$sc\shot.ps1" "${tag}_pony" 8 @look | Out-Null
& "$sc\shot.ps1" "${tag}_pony_m2" 8 @look --mottle '0,0.2' | Out-Null
& "$sc\shot.ps1" "${tag}_bk_pack" 9 --quick warden --sex female --hair long --people dead --open-eyes --zone verge --time day --open inventory | Out-Null
python $TP give godot "face: $tag irises and mottle" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
