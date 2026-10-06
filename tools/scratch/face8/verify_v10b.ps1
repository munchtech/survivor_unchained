# v10b at the Look: her own face (tones, copper hair, dyed brows, light freckles, clean neck), under the white rig,
# Hard-won (freckled preset), and her freckles at full. One godot turn (import first: new maps).
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: v10b check" --wait 120 | Out-Null
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\import_v10b2.log"
$base = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--open-eyes')
& "$sc\shot.ps1" "vb_own" 8 @base | Out-Null
& "$sc\shot.ps1" "vb_own_w" 8 @base --rig-white | Out-Null
& "$sc\shot.ps1" "vb_hardwon" 8 @base --preset hardwon --skin rose --eyes flint | Out-Null
& "$sc\shot.ps1" "vb_heavy" 8 @base --skinparam 'freckle_amount=1.0' | Out-Null
python $T give godot "face: v10b check" | Out-Null
"v10b check done"
