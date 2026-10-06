param([string]$tag = 'v11b', [switch]$nowhite, [switch]$noplay)
# The verification batch, one godot turn: every face under the white rig (tones, irises, brows), the Look's default
# and the nine presets, the book by day and night, and play zoom from the game's own camera (day, night, an arena,
# the nearest zoom), with a face-mottle trial.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag verification" --wait 300 | Out-Null
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes')
if (-not $nowhite) {
    & "$sc\shot.ps1" "${tag}_white" 8 @look --hair ponytail --rig-white | Out-Null
    foreach ($p in $presets) {
        if ($p.id -eq 'own') { continue }
        & "$sc\shot.ps1" "${tag}_w_$($p.id)" 8 @look --hair ponytail --rig-white --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
    }
}
& "$sc\shot.ps1" "${tag}_long" 8 @look --hair long | Out-Null
& "$sc\shot.ps1" "${tag}_pony" 8 @look --hair ponytail | Out-Null
& "$sc\shot.ps1" "${tag}_pony_r" 8 @look --hair ponytail --turn -40 | Out-Null
& "$sc\shot.ps1" "${tag}_pony_fm" 8 @look --hair ponytail --mottle '0.08,0.12' | Out-Null
foreach ($p in $presets) {
    if ($p.id -eq 'own') { continue }
    & "$sc\shot.ps1" "${tag}_p_$($p.id)" 8 @look --hair ponytail --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
}
$base = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--open-eyes')
& "$sc\shot.ps1" "${tag}_bk_pack" 9 @base --zone verge --time day --open inventory | Out-Null
& "$sc\shot.ps1" "${tag}_bk_self" 9 @base --zone verge --time night --open character | Out-Null
& "$sc\shot.ps1" "${tag}_bk_arts" 9 @base --zone verge --time day --open arts | Out-Null
if (-not $noplay) {
    $pz = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--auto', 'toward')
    & "$sc\shot.ps1" "${tag}_pz_day" 9 @pz --zone waystation --time day | Out-Null
    & "$sc\shot.ps1" "${tag}_pz_night" 9 @pz --zone waystation --time night | Out-Null
    & "$sc\shot.ps1" "${tag}_pz_verge" 9 @pz --zone verge --time day | Out-Null
    & "$sc\shot.ps1" "${tag}_pz_arena" 9 @pz --zone arena | Out-Null
    & "$sc\shot.ps1" "${tag}_pz_near" 9 @pz --zone waystation --time day --cam 12.5 | Out-Null
}
python $TP give godot "face: $tag verification" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
