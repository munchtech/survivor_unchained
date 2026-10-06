#!/bin/sh
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/cin3
python "$S/prev.py" c03 h4 30 --clean --wait 60 --stills 2 --only 4,6,8 --cols 2 --width 960 | grep 'warden\|heart\|stills'
python "$S/prev.py" c01 k7 48 --clean --wait 60 --quiet --only 5,8,8b --cols 3 --width 640 | tail -1
echo BATCH DONE
