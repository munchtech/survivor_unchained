# Every face repainted (her and the nine presets) on the unpainted head as it is, one gpu turn under a blender turn,
# then the head rebuilt and imported, then the shots (tag v7c).
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: repaint" --wait 60 | Out-Null
python $T take gpu "face: repaint (Krea)" --wait 60 | Out-Null
$env:FACE_SEED = '11'; $env:FACE_REF = "$sc\from_face3\refs_her\her_23.png"
& $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- "$sc\paintL" *> "$sc\build_paint.log"
"paint exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
Copy-Item "$sc\paintL\face_paint.png" "$w\tools\assets\heroine_face\face_paint.png" -Force
$pick = @{ highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
foreach ($id in $pick.Keys) {
    $out = "$sc\paint_$id"
    $who = python -c "import sys; sys.path.insert(0, r'$w\tools\assets'); import face_refs; t = face_refs.FACES['$id']; print(t.rsplit('.', 2)[0] + '.')"
    $env:FACE_SHAPE = "$out\shape.json"; $env:FACE_WHO = $who; $env:FACE_REF = "$sc\refs_front\$($pick[$id]).png"; $env:FACE_REUSE = '1'
    & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- $out *> "$out\paint.log"
    "[$id] paint exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    Copy-Item "$out\face_paint.png" "$w\tools\assets\heroine_face\face_paint_$id.png" -Force -ErrorAction SilentlyContinue
}
$env:FACE_SHAPE = ''; $env:FACE_WHO = ''; $env:FACE_REF = ''; $env:FACE_REUSE = ''
python $T give gpu "face: repaint (Krea)" | Out-Null
python $T give blender "face: repaint" | Out-Null
& "$sc\rebuild_head.ps1"
& "$sc\shots_v7.ps1" -tag v7c
