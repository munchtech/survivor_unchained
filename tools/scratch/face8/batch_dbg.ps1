param([string]$tag = 'd1')
# One godot turn: is the far features' darkening reaching her face at all? Forced on at the Look's close-up (where
# the mask lies), forced to its strongest at play zoom, and play's view from 8 m.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag far debug" --wait 300 | Out-Null
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\logs\import_$tag.log"
& "$sc\shot.ps1" "${tag}_look_far" 8 --new --sex female --step 1 --part 1 --hair ponytail --open-eyes --skinparam 'far_from=-20,far_to=-19' | Out-Null
$pz = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--auto', 'toward', '--zone', 'waystation', '--time', 'day')
& "$sc\shot.ps1" "${tag}_pz_max" 9 @pz --skinparam 'far_dark=1,far_bold=10' | Out-Null
& "$sc\shot.ps1" "${tag}_pz_cam8" 9 @pz --cam 8 | Out-Null
python $TP give godot "face: $tag far debug" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
