param([string]$tag = 'b0', [switch]$import)
# The throat band, judged in the portrait's own light and camera: the key alone, with and without her pores'
# relief, and the normals Godot draws with (NormalBuffer). One godot turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: band probe" --wait 120 | Out-Null
if ($import) { & "$sc\pk.ps1" "${tag}_all" -noturn -import } else { & "$sc\pk.ps1" "${tag}_all" -noturn }
& "$sc\pk.ps1" "${tag}_key" -noturn -lights '1,0,0'
& "$sc\pk.ps1" "${tag}_key_nopore" -noturn -lights '1,0,0' -skin 'pore_depth=0'
& "$sc\pk.ps1" "${tag}_nb" -noturn -skin 'pore_depth=0' -draw 'NormalBuffer'
& "$sc\pk.ps1" "${tag}_nb_pore" -noturn -draw 'NormalBuffer'
python $T give godot "face: band probe" | Out-Null
"band probe done $(Get-Date -Format HH:mm)"
