param([string[]]$seeds = @('7', '11'), [string]$blend = 'heroine_unpainted.blend', [string]$prefix = 'paintB')
# Her face painted at each seed into face2\<prefix>_s<seed> (heroine_face.py), one after another.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
foreach ($s in $seeds) {
    $env:FACE_SEED = $s
    $out = Join-Path $sc ("{0}_s{1}" -f $prefix, $s)
    & 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe' -b "$w\tools\comfy\out\heroes\$blend" --python "$w\tools\assets\heroine_face.py" -- $out *> "$out.log"
    "seed $s done"
}
