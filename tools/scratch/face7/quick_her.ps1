param([string]$tag = 'q1', [string]$gain = '1.35', [string]$mm = '1.6', [switch]$nolay, [string[]]$extra = @())
# Her paint laid again from the paintings in paintL (no Krea: FACE_LAY_ONLY), her head's texture remade, imported,
# and her shot at the Look (Tail; Loose; Tail under a white rig): one blender turn, one godot turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$s4 = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take blender "face: $tag lay" --wait 120 | Out-Null
if (-not $nolay) {
    $env:FACE_LAY_ONLY = '1'; $env:FACE_REF = "$s4\from_face3\refs_her\her_23.png"; $env:FACE_DETAIL_GAIN = $gain; $env:FACE_DETAIL_MM = $mm
    & $B -b "$w\tools\comfy\out\heroes\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- "$sc\paintL" *> "$sc\lay_$tag.log"
    "lay exit $LASTEXITCODE"
    $env:FACE_LAY_ONLY = ''; $env:FACE_REF = ''; $env:FACE_DETAIL_GAIN = ''; $env:FACE_DETAIL_MM = ''
    Copy-Item "$sc\paintL\face_paint.png" "$w\tools\assets\heroine_face\face_paint.png" -Force
}
& "$sc\rebuild.ps1" -nohair
python $T give blender "face: $tag lay" | Out-Null
python $T take godot "face: $tag shots" --wait 120 | Out-Null
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\import_$tag.log"
$base = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes') + $extra
& "$sc\shot.ps1" "${tag}_pony" 8 @base --hair ponytail | Out-Null
& "$sc\shot.ps1" "${tag}_long" 8 @base --hair long | Out-Null
& "$sc\shot.ps1" "${tag}_white" 8 @base --hair ponytail --rig-white | Out-Null
python $T give godot "face: $tag shots" | Out-Null
"done $(Get-Date -Format HH:mm)"
