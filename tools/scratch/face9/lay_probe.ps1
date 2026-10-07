param([string[]]$dirs = @('lay_doe_old', 'lay_doe_new'), [string]$ref = 'doe_37', [string]$gain = '1.7', [string]$mm = '2.0')
# One blender turn: a face's paint laid again from the paintings in each folder (FACE_LAY_ONLY), on her head shaped
# as that face (the folder's shape.json); a folder named *_old with the reference's features blended as before.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$s4 = 'C:\Users\munch\Desktop\survivorsunchained_inputs\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: lay probe" --wait 300 | Out-Null
$env:FACE_LAY_ONLY = '1'; $env:FACE_DETAIL_GAIN = $gain; $env:FACE_DETAIL_MM = $mm
foreach ($d in $dirs) {
    $out = "$sc\$d"
    $env:FACE_SHAPE = if (Test-Path "$out\shape.json") { "$out\shape.json" } else { '' }
    $env:FACE_REF = if ($ref -eq 'her_23') { "$s4\from_face3\refs_her\her_23.png" } else { "$s4\refs_front\$ref.png" }
    $env:FACE_FRONT_FEATURES = if ($d -like '*_old' -or $d -like '*_nf*') { '0' } else { '1' }
    $env:FACE_MATCH = if ($d -like '*_old') { 'add' } else { '' }
    & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- $out *> "$out\lay_probe.log"
    "[$d] lay exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    Get-Content "$out\lay_probe.log" | Select-String -Pattern "Traceback|Error|FRONT FEATURES|FACE PAINT|REFERENCE" | Select-Object -Last 5
}
$env:FACE_LAY_ONLY = ''; $env:FACE_DETAIL_GAIN = ''; $env:FACE_DETAIL_MM = ''; $env:FACE_REF = ''; $env:FACE_SHAPE = ''; $env:FACE_FRONT_FEATURES = ''; $env:FACE_MATCH = ''
python $T give blender "face: lay probe" | Out-Null
