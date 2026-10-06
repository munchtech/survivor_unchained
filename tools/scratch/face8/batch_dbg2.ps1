param([string]$tag = 'd2')
# One godot turn: does her hair hide her eyes from play's camera? Each cut at play zoom, the far marks at their
# strongest, by day at the Waystation; and the default marks with her hair tied back.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag hair at play zoom" --wait 300 | Out-Null
$pz = @('--quick', 'warden', '--sex', 'female', '--people', 'dead', '--auto', 'toward', '--zone', 'waystation', '--time', 'day')
foreach ($h in 'ponytail', 'pixie', 'bob') {
    & "$sc\shot.ps1" "${tag}_pz_${h}_max" 9 @pz --hair $h --skinparam 'far_dark=1,far_bold=10' | Out-Null
}
& "$sc\shot.ps1" "${tag}_pz_ponytail" 9 @pz --hair ponytail | Out-Null
python $TP give godot "face: $tag hair at play zoom" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
