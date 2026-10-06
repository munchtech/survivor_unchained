param([string[]]$ids = @())
# Each preset's face painted from its own reference on her head shaped as it (its face_<id> key), into
# tools\assets\heroine_face\face_paint_<id>.png (scratch: face4\paint_<id>). Needs heroine_unpainted.blend built with
# every portrait target in place. Takes the gpu turn (Krea) for the whole batch; run it under the blender turn.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
$pick = @{ highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
if (-not $ids.Count) { $ids = @('highborn', 'vixen', 'doe', 'sunborn', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') }
python $T take gpu "face: preset paints (Krea)" --wait 60 | Out-Null
foreach ($id in $ids) {
    $out = "$sc\paint_$id"
    New-Item -ItemType Directory -Force $out | Out-Null
    "{""face_$id"": 1.0}" | Set-Content -Encoding ascii "$out\shape.json"
    # (the woman she is, for Krea's sides, without her hair: heroine_face.py's prompt has her bald)
    $who = python -c "import sys; sys.path.insert(0, r'$w\tools\assets'); import face_refs; t = face_refs.FACES['$id']; print(t.rsplit('.', 2)[0] + '.')"
    $env:FACE_SHAPE = "$out\shape.json"; $env:FACE_WHO = $who; $env:FACE_REF = "$sc\refs_front\$($pick[$id]).png"; $env:FACE_SEED = '11'
    & $B -b "$w\tools\comfy\out\heroes\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- $out *> "$out\paint.log"
    "[$id] paint exit $LASTEXITCODE"
    Copy-Item "$out\face_paint.png" "$w\tools\assets\heroine_face\face_paint_$id.png" -Force -ErrorAction SilentlyContinue
}
$env:FACE_SHAPE = ''; $env:FACE_WHO = ''; $env:FACE_REF = ''
python $T give gpu "face: preset paints (Krea)" | Out-Null
