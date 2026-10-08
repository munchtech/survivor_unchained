param([string[]]$ids = @('own', 'highborn', 'doe', 'sunborn'), [string]$tag = 'pt', [string]$detail = '0')
# One blender turn: each face's front warped again from its portrait with its brows pinned (heroine_face.py,
# FACE_BROW_PIN on by default), the sides' paintings reused, no Krea (FACE_DETAIL=0) unless asked; laid; then the old
# and new paints drawn flat from in front (preview_front.py) for a look and headpose.py's measures.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abe65bc929823a791'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\face10'
$in7 = 'C:\Users\munch\Desktop\survivorsunchained_inputs\face7'
$s4 = 'C:\Users\munch\Desktop\survivorsunchained_inputs\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
$pick = @{ own = 'her_23'; highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
New-Item -ItemType Directory -Force "$sc\logs" | Out-Null
python $T take blender "face: $tag brow pin" --wait 900 | Out-Null
$env:FACE_REUSE = '1'; $env:FACE_DETAIL = $detail; $env:FACE_DETAIL_GAIN = '1.7'; $env:FACE_DETAIL_MM = '2.0'
foreach ($id in $ids) {
    $src = if ($id -eq 'own') { "$in7\paintL" } else { "$in7\paint_$id" }
    $out = "$sc\${tag}_$id"
    if (-not (Test-Path $out)) { Copy-Item $src $out -Recurse }
    Remove-Item "$out\marks_front.json" -ErrorAction SilentlyContinue
    $env:FACE_SHAPE = if (Test-Path "$out\shape.json") { "$out\shape.json" } else { '' }
    $env:FACE_REF = if ($id -eq 'own') { "$s4\from_face3\refs_her\her_23.png" } else { "$s4\refs_front\$($pick[$id]).png" }
    & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- $out *> "$out\pin.log"
    "[$id] lay exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    Get-Content "$out\pin.log" | Select-String -Pattern "Traceback|Error|BROWS|TINTED|FRONT FEATURES|FACE PAINT|REFERENCE|DETAIL" | Select-Object -Last 8
    $shp = if (Test-Path "$out\shape.json") { "$out\shape.json" } else { '' }
    $old = if ($id -eq 'own') { "$in7\paintL\face_paint.png" } else { "$in7\paint_$id\face_paint.png" }
    & $B -b "$H\heroine_unpainted.blend" --python "$sc\preview_front.py" -- "$sc\${tag}_prev_${id}_old.png" $old $shp *> "$sc\logs\prev_old.log"
    & $B -b "$H\heroine_unpainted.blend" --python "$sc\preview_front.py" -- "$sc\${tag}_prev_${id}_new.png" "$out\face_paint.png" $shp *> "$sc\logs\prev_new.log"
}
$env:FACE_REUSE = ''; $env:FACE_DETAIL = ''; $env:FACE_DETAIL_GAIN = ''; $env:FACE_DETAIL_MM = ''; $env:FACE_REF = ''; $env:FACE_SHAPE = ''
python $T give blender "face: $tag brow pin" | Out-Null
"pin test done $(Get-Date -Format HH:mm)"
