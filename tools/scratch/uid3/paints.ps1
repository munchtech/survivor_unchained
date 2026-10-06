param([string]$which = "")
# Paint designs: painted (heroine_paint.py), imported, photographed (creation_portraits.py paint), and a sheet of them.
$u = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3'
$wt = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a69858664f1d3dd29'
Set-Location $wt
$env:PAINT_PREVIEW = "$u\pp"
if ($which -ne "") { python tools/assets/heroine_paint.py $which.Split(',') } else { python tools/assets/heroine_paint.py }
$env:PAINT_PREVIEW = ''
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --path "$wt\godot" --headless --import 2>&1 | Out-Null
python tools/assets/creation_portraits.py paint --raw "$u\por"
$d = "$wt\godot\art\ui\create\female"
python $u\grid.py $u\paints_r.jpg 4 400 $d\paint_kohl.png $d\paint_rouge.png $d\paint_woad.png $d\paint_ochre.png $d\paint_ash.png $d\paint_blood.png $d\paint_gilt.png $d\paint_none.png
