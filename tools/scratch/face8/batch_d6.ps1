param([string]$tag = 'd6')
# One godot turn: her own face under the white rig, her brows' dye and her skin's mottle each at three settings; and
# play zoom by day with her head as now carried.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag brows and mottle" --wait 300 | Out-Null
$w = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--open-eyes', '--rig-white')
& "$sc\shot.ps1" "${tag}_a" 8 @w --brows '0,0.85' --mottle '0.02,0.05' | Out-Null
& "$sc\shot.ps1" "${tag}_b" 8 @w --brows '0.15,0.85' --mottle '0.03,0.08' | Out-Null
& "$sc\shot.ps1" "${tag}_c" 8 @w --brows '0.3,0.7' --mottle '0,0.12' | Out-Null
& "$sc\shot.ps1" "${tag}_pz" 9 --quick warden --sex female --people dead --auto toward --hair long --zone waystation --time day | Out-Null
python $TP give godot "face: $tag brows and mottle" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
