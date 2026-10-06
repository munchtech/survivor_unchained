# Her freckles' maps from the built blend (tools/assets/heroine_freckles.py) into head_tex: one blender turn.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: freckles" --wait 300 | Out-Null
& $B -b "$w\tools\comfy\out\heroes\heroine_built.blend" --python "$w\tools\assets\heroine_freckles.py" -- "$w\godot\art\people\head_tex" *> "$sc\freckles.log"
"freckles exit $LASTEXITCODE"
python $T give blender "face: freckles" | Out-Null
Get-Content "$sc\freckles.log" | Select-String -Pattern "FRECKLES|Traceback|Error"
