param([string]$tag = 'x2')
# Where her skin's grain goes between her texture and the screen: unshaded with and without TAA, her paint read
# a mipmap or two finer, and all textures so.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
$base = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--open-eyes')
python $T take godot "face: $tag grain experiments" --wait 120 | Out-Null
& "$sc\shot.ps1" "${tag}_u" 8 @base --unshaded | Out-Null
& "$sc\shot.ps1" "${tag}_u_notaa" 8 @base --unshaded --no-taa | Out-Null
& "$sc\shot.ps1" "${tag}_u_b1" 8 @base --unshaded --skinparam paint_bias=-1 | Out-Null
& "$sc\shot.ps1" "${tag}_b1" 8 @base --skinparam paint_bias=-1 | Out-Null
& "$sc\shot.ps1" "${tag}_b2" 8 @base --skinparam paint_bias=-2 | Out-Null
& "$sc\shot.ps1" "${tag}_mb2" 8 @base --mipbias -2 | Out-Null
python $T give godot "face: $tag grain experiments" | Out-Null
"done $(Get-Date -Format HH:mm)"
