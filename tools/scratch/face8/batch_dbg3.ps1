param([string]$tag = 'd3')
# One godot turn: play zoom at 4K (the same view, four times the pixels), to see what of her face the camera has.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag play zoom 4K" --wait 300 | Out-Null
$pz = @('--quick', 'warden', '--sex', 'female', '--people', 'dead', '--auto', 'toward', '--zone', 'waystation', '--time', 'day')
& "$sc\shotr.ps1" "${tag}_pz4k_long" 9 3840x2160 @pz --hair long | Out-Null
& "$sc\shotr.ps1" "${tag}_pz4k_pony_max" 9 3840x2160 @pz --hair ponytail --skinparam 'far_dark=1,far_bold=10' | Out-Null
python $TP give godot "face: $tag play zoom 4K" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
