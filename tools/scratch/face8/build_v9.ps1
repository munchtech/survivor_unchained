param([switch]$unpainted, [switch]$paint, [switch]$rest, [string]$tag = 'v9')
# v9: her own face only. -unpainted: the unpainted head and the teeth probe on it (blender). -paint: her paint (gpu;
# her sides kept: FACE_REUSE). -rest: painted head, features, hair, outfits (LOCAL), import. The presets' paints stay
# as they are: each preset's key is its own target less hers, so its face does not move with hers.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$s4 = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
if ($unpainted) {
    python $T take blender "face: $tag unpainted" --wait 120 | Out-Null
    $env:HEAD_UNPAINTED = '1'; $env:HEAD_CHECK = ''
    & $B -b "$H\heroine_body.blend" --python "$w\tools\assets\heroine_head.py" -- "$H\heroine_unpainted.blend" "$sc\art_unpainted" *> "$sc\build_unpainted.log"
    "unpainted exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    $env:HEAD_UNPAINTED = ''
    & $B -b "$H\heroine_unpainted.blend" --python "$sc\teeth_probe.py" *> "$sc\teeth_probe_$tag.log"
    Get-Content "$sc\teeth_probe_$tag.log" | Select-String -Pattern "^KEY|Traceback|Error"
    python $T give blender "face: $tag unpainted" | Out-Null
}
if ($paint) {
    python $T take gpu "face: $tag paint (Krea)" --wait 300 | Out-Null
    python $T take blender "face: $tag paint" --wait 120 | Out-Null
    $env:FACE_SEED = '11'; $env:FACE_REF = "$s4\from_face3\refs_her\her_23.png"; $env:FACE_REUSE = '1'
    & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- "$sc\paintL" *> "$sc\build_paint.log"
    "paint exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    Copy-Item "$sc\paintL\face_paint.png" "$w\tools\assets\heroine_face\face_paint.png" -Force
    $env:FACE_REF = ''; $env:FACE_REUSE = ''
    python $T give blender "face: $tag paint" | Out-Null
    python $T give gpu "face: $tag paint (Krea)" | Out-Null
}
if ($rest) {
    python $T take blender "face: $tag build" --wait 120 | Out-Null
    & "$sc\rebuild.ps1" -nohair
    & $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_features.py" -- "$w\godot\art\people\head_tex" *> "$sc\build_features.log"
    "features exit $LASTEXITCODE"
    & "$sc\rebuild.ps1" -nohead
    & $B -b "$H\heroine_built.blend" --python "$sc\teeth_probe.py" *> "$sc\teeth_probe_${tag}_built.log"
    Get-Content "$sc\teeth_probe_${tag}_built.log" | Select-String -Pattern "^KEY|Traceback|Error"
    & $B -b "$H\heroine_built.blend" --python "$w\tools\assets\heroine_outfits.py" -- "$w\godot\art\people\x" --body "$w\godot\art\people\heroine.glb" *> "$sc\build_outfits.log"
    "outfits exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    python $T give blender "face: $tag build" | Out-Null
    python $T take godot "face: import" --wait 120 | Out-Null
    & 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\build_import.log"
    "import exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
    python $T give godot "face: import" | Out-Null
}
