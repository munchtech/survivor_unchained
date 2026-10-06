param([string]$tag = 'g0', [switch]$import)
# Her in the game's own renderer: as lit, and as white clay (Lighting), all the portrait's lights and the key alone
# without its shadow; her throat (the band's view) and her bust bare (the reaver's) from two sides. One godot turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: game clay" --wait 120 | Out-Null
if ($import) { & "$sc\pk.ps1" "${tag}_lit" -jobs job_clay.json -noturn -import } else { & "$sc\pk.ps1" "${tag}_lit" -jobs job_clay.json -noturn }
& "$sc\pk.ps1" "${tag}_clay" -jobs job_clay.json -noturn -draw 'Lighting'
& "$sc\pk.ps1" "${tag}_claykey" -jobs job_clay.json -noturn -draw 'Lighting' -lights '1,0,0' -keyshadow '0'
python $T give godot "face: game clay" | Out-Null
"game clay $tag done $(Get-Date -Format HH:mm)"
