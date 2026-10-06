param([string]$tag = 'v11a')
# v11's first look, one godot turn: the Look's default (four columns), the nine presets, the book by day and night,
# and play zoom from the game's own camera (the Waystation by day and night, the Verge by day, an arena), walking
# toward the camera.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag batch" --wait 300 | Out-Null
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes')
& "$sc\shot.ps1" "${tag}_long" 8 @look --hair long | Out-Null
& "$sc\shot.ps1" "${tag}_pony" 8 @look --hair ponytail | Out-Null
& "$sc\shot.ps1" "${tag}_pony_r" 8 @look --hair ponytail --turn -40 | Out-Null
& "$sc\shot.ps1" "${tag}_u_long" 8 @look --hair long --unshaded | Out-Null
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
foreach ($p in $presets) {
    if ($p.id -eq 'own') { continue }
    & "$sc\shot.ps1" "${tag}_p_$($p.id)" 8 @look --hair ponytail --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
}
$base = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead')
& "$sc\shot.ps1" "${tag}_bk_pack" 9 @base --zone verge --time day --open inventory | Out-Null
& "$sc\shot.ps1" "${tag}_bk_self" 9 @base --zone verge --time night --open character | Out-Null
& "$sc\shot.ps1" "${tag}_bk_arts" 9 @base --zone verge --time day --open arts | Out-Null
& "$sc\shot.ps1" "${tag}_pz_way_day" 9 @base --zone waystation --time day --auto toward | Out-Null
& "$sc\shot.ps1" "${tag}_pz_way_night" 9 @base --zone waystation --time night --auto toward | Out-Null
& "$sc\shot.ps1" "${tag}_pz_verge" 9 @base --zone verge --time day --auto toward | Out-Null
& "$sc\shot.ps1" "${tag}_pz_arena" 9 @base --zone arena --auto toward | Out-Null
python $TP give godot "face: $tag batch" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
