param([string]$tag = 'g1')
# One godot turn: import (her grain tile), her own face at the Look with her neck's grain at two strengths, under
# the white rig, and Fey under the white rig (Dove's last nudge).
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag grain" --wait 300 | Out-Null
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\logs\import_$tag.log"
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail')
& "$sc\shot.ps1" "${tag}_pony" 8 @look | Out-Null
& "$sc\shot.ps1" "${tag}_pony_14" 8 @look --grain 1.4 | Out-Null
& "$sc\shot.ps1" "${tag}_white" 8 @look --rig-white | Out-Null
& "$sc\shot.ps1" "${tag}_w_fey" 8 @look --rig-white --preset fey --skin fair --eyes dove | Out-Null
python $TP give godot "face: $tag grain" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
