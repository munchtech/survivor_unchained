param([string]$blend, [string]$prefix, [string[]]$views = @('chest', 'torso', 'back', 'under'), [switch]$noturn)
# White clay of her body and head under a light from the side, in each view (side2.py), as her normals are and
# coloured by how far they lean from her surface's own: one blender turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
if (-not $noturn) { python $T take blender "face: clay $prefix" --wait 300 | Out-Null }
foreach ($v in $views) {
    $env:SIDE_VIEW = $v
    [string[]]$modes = if ($v -eq 'chest') { @('asis', 'dev') } else { @('asis') }
    & $B -b $blend --python "$sc\side2.py" -- "$sc\$prefix" @modes *> "$sc\${prefix}_$v.log"
    Get-Content "$sc\${prefix}_$v.log" | Select-String -Pattern "DEV|Traceback|Error"
}
$env:SIDE_VIEW = ''
if (-not $noturn) { python $T give blender "face: clay $prefix" | Out-Null }
"clay $prefix done"
