# One GPU turn: her face painted from her_23 (paintJ, Blender too), then the presets' TRELLIS heads.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take gpu "face: her paint and preset TRELLIS heads" --wait 90 | Out-Null
"gpu taken $(Get-Date -Format HH:mm)"
python $T take blender "face: her paint" --wait 30 | Out-Null
New-Item -ItemType Directory -Force "$sc\paintJ" | Out-Null
$env:FACE_SEED = '11'; $env:FACE_REF = "$sc\from_face3\refs_her\her_23.png"
& $B -b "$w\tools\comfy\out\heroes\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- "$sc\paintJ" *> "$sc\build_paint.log"
"paint exit $LASTEXITCODE"
$env:FACE_REF = ''
python $T give blender "face: her paint" | Out-Null
Copy-Item "$sc\paintJ\face_paint.png" "$w\tools\assets\heroine_face\face_paint.png" -Force
$pick = @{ highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
foreach ($id in 'highborn', 'vixen', 'doe', 'sunborn', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') {
    $out = "$sc\tr_$id"
    New-Item -ItemType Directory -Force $out | Out-Null
    Get-ChildItem $out -Filter '*.glb' -ErrorAction SilentlyContinue | Remove-Item
    python "$w\tools\assets\face_trellis.py" "$sc\refs_front\$($pick[$id]).png" $out --seed 56 *> "$out\trellis.log"
    "[$id] trellis exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
}
python $T give gpu "face: her paint and preset TRELLIS heads" | Out-Null
"gpu given back"
