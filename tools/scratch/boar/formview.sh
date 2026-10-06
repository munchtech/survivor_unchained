#!/bin/sh
# Renders a work dir's form (without the sculpt) in four views and tiles them.
B="C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe"
T="C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af551cacc6292152f/tools/creatures"
S="C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/boar"
W="$S/$1"
FILE="${2:-form}"
"$B" -b --factory-startup --python-expr "
import bpy
bpy.ops.wm.open_mainfile(filepath=r'$W/$FILE.blend')
for n in ('Sculpt','Form') if '$FILE' != 'form' else ('Sculpt',):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=r'$W/_view.blend')
" >/dev/null 2>&1
"$B" -b --factory-startup --python "$T/views.py" -- "$W/_view.blend" "$S/views/$1_$FILE" --size 1400 --views side,top,front,bottom --solid 2>&1 | grep Error
python "$S/sheet.py" "$S/views/$1_$FILE.jpg" 2 900 $S/views/$1_${FILE}_side.png $S/views/$1_${FILE}_top.png $S/views/$1_${FILE}_front.png $S/views/$1_${FILE}_bottom.png
