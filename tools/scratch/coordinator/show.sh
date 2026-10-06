#!/bin/bash
# Render outfits ($OUTFITS) front, 3/4, back and a close-up at 1920x1080; sheets in $TEMP/hs/show/outfit_<o>.jpg
cd /c/Users/munch/Desktop/survivorsunchained/godot
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
S="$TEMP/hs/show"; mkdir -p $S
for k in 1 2 3; do timeout 900 "$G" --headless --path . --import >/dev/null 2>&1 && break; done
for o in ${OUTFITS:-warden ranger arcanist reaver}; do
  for v in "0 f" "35 q" "160 b"; do set -- $v
    env $EXTRA FOV=28 OUTFIT=$o HAIR=ponytail NOLIFE=1 NOJIGGLE=1 ORBIT=$1,1.0,3.9,0.93 timeout 300 "$G" --path . --resolution 1920x1080 -s res://tools_scenes/lookdev.gd -- "Idle" "$S/${o}_$2.png" </dev/null >/dev/null 2>&1
  done
  env $EXTRA FOV=16 OUTFIT=$o HAIR=ponytail NOLIFE=1 NOJIGGLE=1 ORBIT=${CLOSE:-25,1.4,2.3,1.3} timeout 300 "$G" --path . --resolution 1920x1080 -s res://tools_scenes/lookdev.gd -- "Idle" "$S/${o}_c.png" </dev/null >/dev/null 2>&1
done
cd $S && python -c "
from PIL import Image, ImageDraw, ImageFont
import os
names={'warden':'Warden','reaver':'Reaver','arcanist':'Arcanist','ranger':'Stalker'}
font=ImageFont.truetype('C:/Windows/Fonts/georgiab.ttf',40)
for o in os.environ.get('OUTFITS','warden ranger arcanist reaver').split():
  ims=[Image.open(f'{o}_{k}.png').convert('RGB').crop((660,0,1260,1080)) for k in ('f','q','b')]
  c=Image.open(f'{o}_c.png').convert('RGB').crop((420,0,1500,1080))
  out=Image.new('RGB',(2880,1080),(30,30,34))
  for i,im in enumerate(ims): out.paste(im,(i*600,0))
  out.paste(c,(1800,0))
  ImageDraw.Draw(out).text((24,18),names[o],font=font,fill=(235,215,170))
  out.save(f'outfit_{o}.jpg',quality=90)
"
