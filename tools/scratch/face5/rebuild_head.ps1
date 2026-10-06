param([switch]$hair)
# Painted head (paints as they are), features, [hair], outfits and body (LOCAL), import; turns taken.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face5'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: head rebuild" --wait 60 | Out-Null
& "$sc\rebuild.ps1" -nohair
& $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_features.py" -- "$w\godot\art\people\head_tex" *> "$sc\build_features.log"
"features exit $LASTEXITCODE"
if ($hair) { & "$sc\rebuild.ps1" -nohead }
& $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_outfits.py" -- "$w\godot\art\people\x" --body "$w\godot\art\people\heroine.glb" *> "$sc\build_outfits.log"
"outfits exit $LASTEXITCODE"
python $T give blender "face: head rebuild" | Out-Null
python $T take godot "face: import" --wait 60 | Out-Null
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\build_import.log"
"import exit $LASTEXITCODE"
python $T give godot "face: import" | Out-Null

