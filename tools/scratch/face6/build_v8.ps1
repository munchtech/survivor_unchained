param([switch]$skipPaint)
# v8: the unpainted head (every face_<id> key, from the wraps as they are) -> her paint and the presets' (one gpu
# turn, their sides kept from v7: FACE_REUSE) -> painted head -> features -> hair -> outfits (LOCAL) -> import.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2f7b0f1283f6144a'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face6'
$s4 = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: v8 build" --wait 60 | Out-Null
if (-not $skipPaint) {
    $env:HEAD_UNPAINTED = '1'; $env:HEAD_CHECK = ''
    & $B -b "$H\heroine_body.blend" --python "$w\tools\assets\heroine_head.py" -- "$H\heroine_unpainted.blend" "$sc\art_unpainted" *> "$sc\build_unpainted.log"
    "unpainted exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    $env:HEAD_UNPAINTED = ''
    python $T take gpu "face: v8 paints (Krea)" --wait 120 | Out-Null
    $env:FACE_SEED = '11'; $env:FACE_REF = "$s4\from_face3\refs_her\her_23.png"; $env:FACE_REUSE = '1'
    & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- "$sc\paintL" *> "$sc\build_paint.log"
    "paint exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    Copy-Item "$sc\paintL\face_paint.png" "$w\tools\assets\heroine_face\face_paint.png" -Force
    $pick = @{ highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
               saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
    foreach ($id in 'highborn', 'vixen', 'doe', 'sunborn', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') {
        $out = "$sc\paint_$id"
        $who = python -c "import sys; sys.path.insert(0, r'$w\tools\assets'); import face_refs; t = face_refs.FACES['$id']; print(t.rsplit('.', 2)[0] + '.')"
        $env:FACE_SHAPE = "$out\shape.json"; $env:FACE_WHO = $who; $env:FACE_REF = "$s4\refs_front\$($pick[$id]).png"
        & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- $out *> "$out\paint.log"
        "[$id] paint exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
        Copy-Item "$out\face_paint.png" "$w\tools\assets\heroine_face\face_paint_$id.png" -Force -ErrorAction SilentlyContinue
    }
    $env:FACE_SHAPE = ''; $env:FACE_WHO = ''; $env:FACE_REF = ''; $env:FACE_REUSE = ''
    python $T give gpu "face: v8 paints (Krea)" | Out-Null
}
& "$sc\rebuild.ps1" -nohair
& $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_features.py" -- "$w\godot\art\people\head_tex" *> "$sc\build_features.log"
"features exit $LASTEXITCODE"
& "$sc\rebuild.ps1" -nohead
& $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_outfits.py" -- "$w\godot\art\people\x" --body "$w\godot\art\people\heroine.glb" *> "$sc\build_outfits.log"
"outfits exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
python $T give blender "face: v8 build" | Out-Null
python $T take godot "face: import" --wait 120 | Out-Null
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\build_import.log"
"import exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
python $T give godot "face: import" | Out-Null
