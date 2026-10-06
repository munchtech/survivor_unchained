#!/bin/sh
B="C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe"
V="C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af551cacc6292152f/tools/creatures/views.py"
S="C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/boar"
for n in side14 tq11 shape22; do
  g=$(ls $S/trellis/$n/s42/*textured*.glb)
  "$B" -b --factory-startup --python "$V" -- "$g" "$S/views/$n" --size 900 --views side,top,front $1 2>&1 | grep -E "VIEW|Error" | head -3
  "$B" -b --factory-startup --python "$V" -- "$g" "$S/views/${n}_solid" --size 900 --views side --solid 2>&1 | grep -E "Error" | head -3
done
python "$S/sheet.py" "$S/views/compare.jpg" 4 600 $S/views/side13_side.png $S/views/side14_side.png $S/views/tq11_side.png $S/views/shape22_side.png $S/views/side13_top.png $S/views/side14_top.png $S/views/tq11_top.png $S/views/shape22_top.png
python "$S/sheet.py" "$S/views/compare_solid.jpg" 3 700 $S/views/side14_solid_side.png $S/views/tq11_solid_side.png $S/views/shape22_solid_side.png
