#!/bin/bash
# All outfits and her body (skin masks) rebuilt, imported, and each outfit rendered: $TEMP/hs/cost/sheet_<o>.png
cd /c/Users/munch/Desktop/survivorsunchained
timeout 7000 "/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_outfits.py -- godot/art/people/x --body godot/art/people/heroine.glb > "$TEMP/hs/outfits.log" 2>&1
grep -E "Error|Traceback|line [0-9]+|BODY|OUTFIT |PLATE CUP" "$TEMP/hs/outfits.log" | head -20
cd godot
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
S="$TEMP/hs/cost"
rm -f .godot/imported/heroine_outfit_*.gltf-*.md5 .godot/imported/heroine_outfit_*.gltf-*.scn  # (a .gltf is re-imported only when its JSON changes; its .bin can change alone)
for k in 1 2 3; do timeout 900 "$G" --headless --path . --import >/dev/null 2>&1 && break; echo "import retry $k"; done
for o in ${OUTFITS:-warden ranger arcanist reaver}; do
  for v in "0 f" "35 q" "150 b"; do set -- $v
    FOV=${FOVV:-14} OUTFIT=$o HAIR=ponytail NOLIFE=1 NOJIGGLE=1 ORBIT=$1,${CAM:-1.36,2.4,1.3} timeout 300 "$G" --path . --resolution 1000x1000 -s res://tools_scenes/lookdev.gd -- "Idle" "$S/s_${o}_$2.png" </dev/null >/dev/null 2>&1
  done
  (cd $S && python -c "
from PIL import Image
ims=[Image.open(f's_${o}_{k}.png').convert('RGB') for k in ('f','q','b')]
c=Image.new('RGB',(3000,1000)); [c.paste(im,(i*1000,0)) for i,im in enumerate(ims)]; c.save('sheet_${o}.png')")
done
