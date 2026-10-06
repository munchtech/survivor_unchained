param([string]$tag = 's0')
# The key's terminator down her throat: her skin's scatter at none, as it is and full; and Godot's own lighting
# alone (Lighting: her skin as white clay). One godot turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: sss probe" --wait 120 | Out-Null
& "$sc\pk.ps1" "${tag}_sc0" -noturn -lights '1,0,0' -skin 'scatter=0'
& "$sc\pk.ps1" "${tag}_sc1" -noturn -lights '1,0,0' -skin 'scatter=1'
& "$sc\pk.ps1" "${tag}_lit" -noturn -draw 'Lighting'
& "$sc\pk.ps1" "${tag}_litkey" -noturn -lights '1,0,0' -draw 'Lighting'
python $T give godot "face: sss probe" | Out-Null
"sss probe done $(Get-Date -Format HH:mm)"
