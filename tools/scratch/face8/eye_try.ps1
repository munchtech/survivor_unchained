param([string]$tag = 'e0')
# Her catchlight at the Look's close-up: the cornea's roughness and sheen tried, and the key taken away. One godot turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: $tag eyes" --wait 120 | Out-Null
$base = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--open-eyes')
& "$sc\shot.ps1" "${tag}_r012" 8 @base --eyeparam wet_rough=0.012 | Out-Null
& "$sc\shot.ps1" "${tag}_r08" 8 @base --eyeparam wet_rough=0.08 | Out-Null
& "$sc\shot.ps1" "${tag}_w15" 8 @base --eyeparam wet=0.15 | Out-Null
& "$sc\shot.ps1" "${tag}_nokey" 8 @base --rig '0,0.22,0.8,0.55' | Out-Null
& "$sc\shot.ps1" "${tag}_norim" 8 @base --rig '1.15,0.22,0.8,0' | Out-Null
python $T give godot "face: $tag eyes" | Out-Null
"eyes $tag done"
