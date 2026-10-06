#!/bin/sh
B="C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe"
T="C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af551cacc6292152f/tools/creatures"
S="C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/boar"
for n in side14 tq11 shape22; do
  g=$(ls $S/trellis/$n/s42/*textured*.glb)
  "$B" -b --factory-startup --python "$T/boar_build.py" -- prep --work "$S/work_$n" --sculpt "$g" --yaw -90 2>&1 | grep -E "PARTS|SIZE|Error|Traceback" | head -5
  "$B" -b --factory-startup --python "$T/views.py" -- "$S/work_$n/prep.blend" "$S/views/${n}_p" --size 900 --views side,top,front 2>&1 | grep -E "Error" | head -3
  "$B" -b --factory-startup --python "$T/views.py" -- "$S/work_$n/prep.blend" "$S/views/${n}_ps" --size 900 --views side --solid 2>&1 | grep -E "Error" | head -3
done
python "$S/sheet.py" "$S/views/compare2.jpg" 3 640 $S/views/side14_p_side.png $S/views/tq11_p_side.png $S/views/shape22_p_side.png $S/views/side14_ps_side.png $S/views/tq11_ps_side.png $S/views/shape22_ps_side.png $S/views/side14_p_top.png $S/views/tq11_p_top.png $S/views/shape22_p_top.png
