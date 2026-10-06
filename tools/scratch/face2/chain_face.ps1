param([string[]]$seeds = @('11', '23'), [string]$prefix = 'paintC')
# After a change to her face's shape: her head unpainted, then painted at each seed (face2\<prefix>_s<seed>).
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6784044c82f101d9'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face2'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$env:HEAD_UNPAINTED = '1'; $env:HEAD_CHECK = ''
& $B -b "$w\tools\comfy\out\heroes\heroine_body.blend" --python "$w\tools\assets\heroine_head.py" -- "$w\tools\comfy\out\heroes\heroine_unpainted.blend" "$sc\art_unpainted" *> "$sc\head_unpainted.log"
"unpainted head exit $LASTEXITCODE"
$env:HEAD_UNPAINTED = ''
& "$sc\paint_seeds.ps1" -seeds $seeds -prefix $prefix
