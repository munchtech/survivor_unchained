param([string[]]$ids = @('highborn', 'vixen', 'doe', 'sunborn', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey'), [switch]$hair)
# The presets' paints anew, sides and all (v7's sides were painted from drawings of its broken cheeks), on the
# unpainted head as it is; then the painted head, features, [hair], outfits (LOCAL) and import.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face5'
$s4 = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: v8b build" --wait 120 | Out-Null
python $T take gpu "face: v8b preset paints (Krea)" --wait 120 | Out-Null
$pick = @{ highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
$env:FACE_SEED = '11'; $env:FACE_REUSE = ''
foreach ($id in $ids) {
    $out = "$sc\paint_$id"
    $who = python -c "import sys; sys.path.insert(0, r'$w\tools\assets'); import face_refs; t = face_refs.FACES['$id']; print(t.rsplit('.', 2)[0] + '.')"
    $env:FACE_SHAPE = "$out\shape.json"; $env:FACE_WHO = $who; $env:FACE_REF = "$s4\refs_front\$($pick[$id]).png"
    & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- $out *> "$out\paint.log"
    "[$id] paint exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    Copy-Item "$out\face_paint.png" "$w\tools\assets\heroine_face\face_paint_$id.png" -Force -ErrorAction SilentlyContinue
}
$env:FACE_SHAPE = ''; $env:FACE_WHO = ''; $env:FACE_REF = ''
python $T give gpu "face: v8b preset paints (Krea)" | Out-Null
& "$sc\rebuild.ps1" -nohair
& $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_features.py" -- "$w\godot\art\people\head_tex" *> "$sc\build_features.log"
"features exit $LASTEXITCODE"
if ($hair) { & "$sc\rebuild.ps1" -nohead }
& $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_outfits.py" -- "$w\godot\art\people\x" --body "$w\godot\art\people\heroine.glb" *> "$sc\build_outfits.log"
"outfits exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
python $T give blender "face: v8b build" | Out-Null
python $T take godot "face: import" --wait 120 | Out-Null
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\build_import.log"
"import exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
python $T give godot "face: import" | Out-Null
