#!/bin/sh
# The hand-overs of the Prologue's other cinematics, one Godot turn each.
D=C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/cin4
python $D/ho.py c04a hoa_c04a 50 --wait 90 > $D/hoa_c04a.out 2>&1
python $D/ho.py c02 hoa_c02 56 --wait 90 > $D/hoa_c02.out 2>&1
python $D/ho.py c03 hoa_c03 59 --wait 90 > $D/hoa_c03.out 2>&1
python $D/ho.py c04b hoa_c04b 35 --zone waystation --wait 90 > $D/hoa_c04b.out 2>&1
echo all done
