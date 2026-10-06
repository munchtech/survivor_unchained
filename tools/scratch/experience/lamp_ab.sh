#!/bin/sh
# The town's lamp at dusk with one effect off at a time: sh lamp_ab.sh (after tod.sh d4).
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
python "$E/play.py" lamp_volfog --timeout 300 -- --quick warden --sex female --zone waystation --time dusk --auto idle --seconds 4 --perf-off volfog | head -1
python "$E/play.py" lamp_glow --timeout 300 -- --quick warden --sex female --zone waystation --time dusk --auto idle --seconds 4 --perf-off glow | head -1
cd "$E"
python crop.py lamp_a.png lamp_volfog 400 300 1100 800 0.6
python crop.py lamp_b.png lamp_glow 400 300 1100 800 0.6
python crop.py lamp_c.png tod_t_d4 400 300 1100 800 0.6
python - <<'EOF'
from PIL import Image
ims = [Image.open(f) for f in ("lamp_c.png", "lamp_a.png", "lamp_b.png")]
o = Image.new("RGB", (sum(i.width for i in ims), max(i.height for i in ims)))
x = 0
for i in ims:
    o.paste(i, (x, 0)); x += i.width
o.save("lamp_abc.png"); print(o.size)
EOF
