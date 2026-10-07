param([string[]]$pairs)
# One blender turn: each "OUT|PAINT|SHAPE" drawn flat from in front (preview_front.py) on the unpainted head.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: previews" --wait 300 | Out-Null
foreach ($p in $pairs) {
    $o, $f, $s = $p.Split('|')
    & $B -b "$w\tools\comfy\out\heroes\heroine_unpainted.blend" --python "$sc\preview_front.py" -- "$sc\$o" $f $s *> "$sc\logs\preview.log"
    "[$o] exit $LASTEXITCODE"
    Get-Content "$sc\logs\preview.log" | Select-String -Pattern "Traceback|Error:" | Select-Object -First 3
}
python $T give blender "face: previews" | Out-Null
