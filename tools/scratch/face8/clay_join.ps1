param([string]$blend = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\tools\comfy\out\heroes\heroine_built.blend', [string]$prefix = 'cj')
# Her front where the graft meets her (CUT) and her middle: which is which, and the surface flat-shaded. One blender turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: join look" --wait 300 | Out-Null
$env:SIDE_VIEW = 'chest'
& $B -b $blend --python "$sc\side2.py" -- "$sc\$prefix" asis mat flat *> "$sc\${prefix}.log"
$env:SIDE_VIEW = ''
python $T give blender "face: join look" | Out-Null
Get-Content "$sc\${prefix}.log" | Select-String -Pattern "Traceback|Error|SIDE"
