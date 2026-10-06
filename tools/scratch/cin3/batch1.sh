#!/bin/sh
# C01 check, then C02 and C03 staging with the Warden's new clips (each run takes and gives its own Godot turn).
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/cin3
python "$S/jedit.py" c01 "$S/e_c01g.py"
python "$S/prev.py" c01 k6 48 --clean --wait 60 --quiet --only 5,7,8,8b --cols 2 --width 960 | tail -1
python "$S/prev.py" c02 st2 80 --clean --wait 60 --quiet | tail -1
python "$S/prev.py" c03 st3 80 --clean --wait 60 --quiet | tail -1
echo BATCH DONE
