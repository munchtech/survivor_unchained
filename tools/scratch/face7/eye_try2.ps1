param([string]$tag = 'e1')
# Which light makes the white blob on her irises at the Look: each of the rig's taken away in turn, then all of it.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: $tag eyes" --wait 120 | Out-Null
$base = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--open-eyes')
& "$sc\shot.ps1" "${tag}_nofill" 8 @base --rig '1.15,0,0.8,0.55' | Out-Null
& "$sc\shot.ps1" "${tag}_noedge" 8 @base --rig '1.15,0.22,0,0.55' | Out-Null
& "$sc\shot.ps1" "${tag}_none" 8 @base --rig '0,0,0,0' | Out-Null
& "$sc\shot.ps1" "${tag}_dull" 8 @base --eyeparam 'wet=0.0,catchlight=0.0' | Out-Null
python $T give godot "face: $tag eyes" | Out-Null
"eyes $tag done"
