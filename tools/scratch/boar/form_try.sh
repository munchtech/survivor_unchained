#!/bin/sh
B="C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe"
T="C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af551cacc6292152f/tools/creatures"
S="C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/boar"
W="$S/work_side14"
for v in "0.005 25"; do
  set -- $v
  "$B" -b --factory-startup --python "$T/boar_build.py" -- form --work "$W" --smooth $2 2>&1 | grep -E "FORM|Error|Traceback" | head -5
  cp "$W/form.blend" "$W/form_$1.blend"
  "$B" -b --factory-startup --python-expr "
import bpy
bpy.ops.wm.open_mainfile(filepath=r'$W/form_$1.blend')
bpy.data.objects['Sculpt'].hide_render=True
bpy.data.objects['Sculpt'].hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=r'$W/form_view.blend')
" >/dev/null 2>&1
  "$B" -b --factory-startup --python "$T/views.py" -- "$W/form_view.blend" "$S/views/form_$1" --size 900 --views side,top,front --solid 2>&1 | grep -E "Error" | head -3
done
python "$S/sheet.py" "$S/views/forms.jpg" 3 640 $S/views/form_0.005_side.png $S/views/form_0.005_top.png $S/views/form_0.005_front.png
