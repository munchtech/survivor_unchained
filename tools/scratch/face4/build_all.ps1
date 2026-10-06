param([string]$paintDir = 'paintI', [string]$ref = '', [string]$seed = '11', [switch]$wrap, [switch]$reuseSides, [switch]$skipPaint, [switch]$noImport)
# Her whole head again in my worktree, taking turns as it goes (blender for Blender, gpu only while Krea paints, godot for
# the import): [her portrait wrap] -> unpainted head -> her face painted from $ref into face4\$paintDir -> painted head
# -> features -> hair -> outfits and body (heroine_outfits.py --body, LOCAL ONLY: never commit what it writes) -> import.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
if (-not $ref) { $ref = "$sc\from_face3\refs_her\her_23.png" }
python $T take blender "face: head build" --wait 30 | Out-Null
if ($wrap) {
    & "$sc\portrait.ps1" -id heroine -ref $ref -skipTrellis:$true 2>&1 | Out-Null
    "wrap done"
}
if (-not $skipPaint) {
    $env:HEAD_UNPAINTED = '1'; $env:HEAD_CHECK = ''
    & $B -b "$H\heroine_body.blend" --python "$w\tools\assets\heroine_head.py" -- "$H\heroine_unpainted.blend" "$sc\art_unpainted" *> "$sc\build_unpainted.log"
    "unpainted exit $LASTEXITCODE"
    $env:HEAD_UNPAINTED = ''
    New-Item -ItemType Directory -Force "$sc\$paintDir" | Out-Null
    if ($reuseSides) { Copy-Item "$sc\paintF\painted_left.png", "$sc\paintF\painted_right.png" "$sc\$paintDir\"; $env:FACE_REUSE = '1' }
    python $T take gpu "face: paint (Krea)" --wait 30 | Out-Null
    $env:FACE_SEED = $seed; $env:FACE_REF = $ref
    & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- "$sc\$paintDir" *> "$sc\build_paint.log"
    "paint exit $LASTEXITCODE"
    python $T give gpu "face: paint (Krea)" | Out-Null
    $env:FACE_REF = ''; $env:FACE_REUSE = ''
    Copy-Item "$sc\$paintDir\face_paint.png" "$w\tools\assets\heroine_face\face_paint.png" -Force
}
& "$sc\rebuild.ps1" -nohair
& $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_features.py" -- "$w\godot\art\people\head_tex" *> "$sc\build_features.log"
"features exit $LASTEXITCODE"
& "$sc\rebuild.ps1" -nohead
& $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_outfits.py" -- "$w\godot\art\people\x" --body "$w\godot\art\people\heroine.glb" *> "$sc\build_outfits.log"
"outfits exit $LASTEXITCODE"
python $T give blender "face: head build" | Out-Null
if (-not $noImport) {
    python $T take godot "face: import" --wait 30 | Out-Null
    & 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\build_import.log"
    "import exit $LASTEXITCODE"
    python $T give godot "face: import" | Out-Null
}
