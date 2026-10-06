param([string]$tag = 'd5')
# One godot turn: play zoom with the marks grown to the pixel (day, night, arena, nearest), her chin up a little;
# and her own face under the white rig with her body's mottle at three strengths (her neck's grain, her brows, her
# painted iris's tint, her tone).
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag play zoom and mottle" --wait 300 | Out-Null
$pz = @('--quick', 'warden', '--sex', 'female', '--people', 'dead', '--auto', 'toward', '--hair', 'long')
& "$sc\shot.ps1" "${tag}_day" 9 @pz --zone waystation --time day | Out-Null
& "$sc\shot.ps1" "${tag}_day_up" 9 @pz --zone waystation --time day --head-level 1 --head-ease -12 | Out-Null
& "$sc\shot.ps1" "${tag}_night" 9 @pz --zone waystation --time night | Out-Null
& "$sc\shot.ps1" "${tag}_arena" 9 @pz --zone arena | Out-Null
& "$sc\shot.ps1" "${tag}_near" 9 @pz --zone waystation --time day --cam 12.5 | Out-Null
$w = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--open-eyes', '--rig-white')
& "$sc\shot.ps1" "${tag}_w_m0" 8 @w --mottle '0,0' | Out-Null
& "$sc\shot.ps1" "${tag}_w_m2" 8 @w --mottle '0,0.02' | Out-Null
& "$sc\shot.ps1" "${tag}_w_m4" 8 @w --mottle '0,0.04' | Out-Null
& "$sc\shot.ps1" "${tag}_w_m14" 8 @w --mottle '0.015,0.04' | Out-Null
python $TP give godot "face: $tag play zoom and mottle" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
