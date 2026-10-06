param([string]$tag = 'n2')
# Her head built into the scratchpad (built_TAG.blend, its textures in art_TAG), then her chest and throat in clay
# (as built, by part, flat) and the crease probe across her throat: one blender turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: head try $tag" --wait 300 | Out-Null
$env:HEAD_UNPAINTED = ''; $env:HEAD_CHECK = ''
& $B -b "$w\tools\comfy\out\heroes\heroine_body.blend" --python "$w\tools\assets\heroine_head.py" -- "$sc\built_$tag.blend" "$sc\art_$tag" *> "$sc\head_$tag.log"
"head exit $LASTEXITCODE"
Get-Content "$sc\head_$tag.log" | Select-String -Pattern "MIDDLE|NORMALS|FOLDS|Traceback|Error" | Select-Object -Last 8
$env:SIDE_VIEW = 'chest'
& $B -b "$sc\built_$tag.blend" --python "$sc\side2.py" -- "$sc\cl_$tag" asis mat flat *> "$sc\cl_$tag.log"
$env:SIDE_VIEW = ''
$env:ZS = '1.60,1.58,1.56,1.54,1.52,1.50,1.48,1.46'
& $B -b "$sc\built_$tag.blend" --python "$sc\crease_probe.py" *> "$sc\crease_$tag.log"
$env:ZS = ''
python $T give blender "face: head try $tag" | Out-Null
