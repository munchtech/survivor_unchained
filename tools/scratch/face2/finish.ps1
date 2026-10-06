param([string]$paint = "")
# Her face paint chosen (a face2 folder's face_paint.png), then her head, its features and her hair rebuilt, and Godot's import.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6784044c82f101d9'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face2'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
if ($paint) { Copy-Item "$sc\$paint\face_paint.png" "$w\tools\assets\heroine_face\face_paint.png" -Force; "paint from $paint" }
& "$sc\rebuild.ps1" -nohair
& $B -b "$w\tools\comfy\out\heroes\heroine_built.blend" --python "$w\tools\assets\heroine_features.py" -- "$w\godot\art\people\head_tex" *> "$sc\features.log"
Get-Content "$sc\features.log" | Select-String "FEATURES|Error|Traceback"
& "$sc\rebuild.ps1" -nohead
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\import_f.log"
"import exit $LASTEXITCODE"
