param([string]$tag = 'd4', [string[]]$extra = @())
# One godot turn: her face at play zoom, from the game's own camera, walking toward it: the Waystation by day (her
# head as the clip carries it, and carried level), by night, an arena, the nearest zoom, and her hair tied back.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag play zoom" --wait 300 | Out-Null
$pz = @('--quick', 'warden', '--sex', 'female', '--people', 'dead', '--auto', 'toward') + $extra
& "$sc\shot.ps1" "${tag}_day" 9 @pz --hair long --zone waystation --time day | Out-Null
& "$sc\shot.ps1" "${tag}_day_bowed" 9 @pz --hair long --zone waystation --time day --head-level 0 | Out-Null
& "$sc\shot.ps1" "${tag}_day_pony" 9 @pz --hair ponytail --zone waystation --time day | Out-Null
& "$sc\shot.ps1" "${tag}_night" 9 @pz --hair long --zone waystation --time night | Out-Null
& "$sc\shot.ps1" "${tag}_arena" 9 @pz --hair long --zone arena | Out-Null
& "$sc\shot.ps1" "${tag}_near" 9 @pz --hair long --zone waystation --time day --cam 12.5 | Out-Null
python $TP give godot "face: $tag play zoom" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
