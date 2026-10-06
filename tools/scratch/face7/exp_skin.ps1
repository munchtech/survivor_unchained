param([string]$tag = 'x1')
# What softens and pinks her skin at the Look's close-up: TAA off, textures sampled sharper, less scattering, and the
# rig's light white (her and Sunborn), each one picture of Tail (ponytail) in one godot turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
$base = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--open-eyes')
python $T take godot "face: $tag skin experiments" --wait 120 | Out-Null
& "$sc\shot.ps1" "${tag}_notaa" 8 @base --no-taa | Out-Null
& "$sc\shot.ps1" "${tag}_mip1" 8 @base --mipbias -1 | Out-Null
& "$sc\shot.ps1" "${tag}_sss" 8 @base --skinparam scatter=0.12 | Out-Null
& "$sc\shot.ps1" "${tag}_white" 8 @base --rig-white | Out-Null
& "$sc\shot.ps1" "${tag}_white_sunborn" 8 @base --rig-white --preset sunborn --skin brown --eyes sloe | Out-Null
python $T give godot "face: $tag skin experiments" | Out-Null
"experiments done $(Get-Date -Format HH:mm)"
