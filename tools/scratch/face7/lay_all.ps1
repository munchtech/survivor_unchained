param([string]$gain = '1.7', [string]$mm = '2.0', [string[]]$only = @())
# Every face's paint laid again from the paintings already in its folder (FACE_LAY_ONLY: no Krea), the fine detail
# from the view that sees it best (heroine_face.py), into tools/assets/heroine_face. One blender turn.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$s4 = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: lay all" --wait 120 | Out-Null
$env:FACE_LAY_ONLY = '1'; $env:FACE_DETAIL_GAIN = $gain; $env:FACE_DETAIL_MM = $mm
if (-not $only.Count -or $only -contains 'own') {
    $env:FACE_REF = "$s4\from_face3\refs_her\her_23.png"; $env:FACE_SHAPE = ''; $env:FACE_WHO = ''
    & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- "$sc\paintL" *> "$sc\lay_own.log"
    "[own] lay exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    Copy-Item "$sc\paintL\face_paint.png" "$w\tools\assets\heroine_face\face_paint.png" -Force
}
$pick = @{ highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
foreach ($id in 'highborn', 'vixen', 'doe', 'sunborn', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') {
    if ($only.Count -and $only -notcontains $id) { continue }
    $out = "$sc\paint_$id"
    $env:FACE_SHAPE = "$out\shape.json"; $env:FACE_REF = "$s4\refs_front\$($pick[$id]).png"
    $env:FACE_WHO = python -c "import sys; sys.path.insert(0, r'$w\tools\assets'); import face_refs; t = face_refs.FACES['$id']; print(t.rsplit('.', 2)[0] + '.')"
    & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- $out *> "$out\lay.log"
    "[$id] lay exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    Copy-Item "$out\face_paint.png" "$w\tools\assets\heroine_face\face_paint_$id.png" -Force
}
$env:FACE_LAY_ONLY = ''; $env:FACE_DETAIL_GAIN = ''; $env:FACE_DETAIL_MM = ''; $env:FACE_REF = ''; $env:FACE_SHAPE = ''; $env:FACE_WHO = ''
python $T give blender "face: lay all" | Out-Null
