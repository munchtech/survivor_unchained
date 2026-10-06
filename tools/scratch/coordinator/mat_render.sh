#!/bin/bash
# Old vs new outfit materials, torso close-ups for each outfit: $TEMP/hs/cost/mat_<o>.png
cd /c/Users/munch/Desktop/survivorsunchained/godot
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
S="$TEMP/hs/cost"
for o in ${OUTFITS:-warden arcanist reaver ranger}; do
  for v in "OLDOUTFIT=1 old" "X=1 new"; do set -- $v
    env $1 FOV=${FOVV:-14} OUTFIT=$o HAIR=ponytail NOLIFE=1 NOJIGGLE=1 ORBIT=${ORB:-15,1.4,2.2,1.3} timeout 300 "$G" --path . --resolution 1200x1200 -s res://tools_scenes/lookdev.gd -- "Idle" "$S/m_${o}_$2.png" </dev/null 2>&1 | grep -E "SHADER|error\(" | head -3
  done
done
cd $S && python -c "
from PIL import Image
import os
for o in os.environ.get('OUTFITS','warden arcanist reaver ranger').split():
  ims=[Image.open(f'm_{o}_{k}.png').convert('RGB').crop((0,0,1200,800)) for k in ('old','new')]
  c=Image.new('RGB',(2400,800)); [c.paste(im,(i*1200,0)) for i,im in enumerate(ims)]; c.save(f'mat_{o}.png')"
