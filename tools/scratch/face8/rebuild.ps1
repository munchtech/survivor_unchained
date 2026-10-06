param([switch]$nohead, [switch]$nohair, [string]$styles = "")
# Her head (heroine_head.py, with the face paint in tools/assets/heroine_face) and then her hair (all styles,
# saved into the blend) in my worktree. Logs in face2\head.log and face2\hair.log.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$env:HEAD_UNPAINTED = ''; $env:HEAD_CHECK = ''
if (-not $nohead) {
    & $B -b "$w\tools\comfy\out\heroes\heroine_body.blend" --python "$w\tools\assets\heroine_head.py" -- "$w\tools\comfy\out\heroes\heroine_built.blend" "$w\godot\art\people" *> "$sc\head.log"
    "head exit $LASTEXITCODE"
    Get-Content "$sc\head.log" | Select-String -Pattern "Traceback|Error|SHAPES|LIPS|FACE PAINT" | Select-Object -Last 6
}
if (-not $nohair) {
    $env:HAIR_BLEND = "$w\tools\comfy\out\heroes\heroine_built.blend"
    $st = if ($styles) { $styles.Split(",") } else { @() }
    & $B -b "$w\tools\comfy\out\heroes\heroine_built.blend" --python "$w\tools\assets\heroine_hair.py" -- "$w\godot\art\people" @st *> "$sc\hair.log"
    "hair exit $LASTEXITCODE"
    $env:HAIR_BLEND = ''
    Get-Content "$sc\hair.log" | Select-String -Pattern "Traceback|Error|STYLE" | Select-Object -Last 8
}

