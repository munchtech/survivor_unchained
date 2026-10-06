#!/bin/bash
# Rebuild (optional) and render the long hair: 4 views + a close-up, sheet in $TEMP/hs/hg.
cd /c/Users/munch/Desktop/survivorsunchained
if [ "$1" == "build" ]; then
  timeout 2400 "/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_hair.py -- godot/art/people $ATL ${STYLE:-long} 2>&1 | grep -E "STYLE|Error|Traceback|line [0-9]" | head -8
fi
cd godot
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
timeout 600 "$G" --headless --path . --import >/dev/null 2>&1
S="$TEMP/hs/hg"
for v in "0 f" "40 q" "100 s" "180 b"; do set -- $v; HAIR=${STYLE:-long} ORBIT=$1,1.62,1.05,1.55 NOJIGGLE=1 timeout 300 "$G" --path . --resolution 1200x1200 -s res://tools_scenes/lookdev.gd -- "Idle" "$S/h_$2.png" </dev/null 2>&1 | grep -E "SHADER|Parse|error\(" | head -5; done
HAIR=${STYLE:-long} ORBIT=25,1.72,0.5,1.7 NOJIGGLE=1 timeout 300 "$G" --path . --resolution 1200x1200 -s res://tools_scenes/lookdev.gd -- "Idle" "$S/h_close.png" </dev/null >/dev/null 2>&1
HAIR=${STYLE:-long} ORBIT=150,1.75,0.55,1.7 NOJIGGLE=1 timeout 300 "$G" --path . --resolution 1200x1200 -s res://tools_scenes/lookdev.gd -- "Idle" "$S/h_close2.png" </dev/null >/dev/null 2>&1
cd "$S" && python -c "
from PIL import Image
ims=[Image.open(f'h_{k}.png').convert('RGB') for k in ('f','q','s','b')]
w,h=ims[0].size
ims=[im.crop((int(w*0.25),0,int(w*0.75),h)) for im in ims]
out=Image.new('RGB',(ims[0].width*4,ims[0].height))
for i,im in enumerate(ims): out.paste(im,(i*ims[0].width,0))
out.save('hg_sheet.png')
a,b=Image.open('h_close.png').convert('RGB'),Image.open('h_close2.png').convert('RGB')
c=Image.new('RGB',(a.width*2,a.height)); c.paste(a,(0,0)); c.paste(b,(a.width,0)); c.save('hg_close.png')"
