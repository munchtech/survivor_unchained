#!/bin/bash
# Build one outfit ($1) and render its torso from three angles: $TEMP/hs/cost/wcups.png
cd /c/Users/munch/Desktop/survivorsunchained
timeout 3000 "/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_outfits.py -- godot/art/people/x --only $1 > "$TEMP/hs/w.log" 2>&1
grep -E "PLATE CUP|FULL CUP|Error|Traceback|line [0-9]+|OUTFIT" "$TEMP/hs/w.log" | head
cd godot
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
S="$TEMP/hs/cost"
for k in 1 2 3; do timeout 900 "$G" --headless --path . --import >/dev/null 2>&1 && break; echo "import retry $k"; done
OUT=$1; for v in "0 f" "35 q" "150 b"; do set -- $v; FOV=${FOVV:-20} OUTFIT=$OUT HAIR=ponytail NOLIFE=1 NOJIGGLE=1 ORBIT=$1,${CAM:-1.25,2.6,1.15} timeout 300 "$G" --path . --resolution 1000x1000 -s res://tools_scenes/lookdev.gd -- "Idle" "$S/wc_$2.png" </dev/null >/dev/null 2>&1; done
cd $S && python -c "
from PIL import Image
ims=[Image.open(f'wc_{k}.png').convert('RGB') for k in ('f','q','b')]
c=Image.new('RGB',(3000,1000)); [c.paste(im,(i*1000,0)) for i,im in enumerate(ims)]; c.save('wcups.png')"
