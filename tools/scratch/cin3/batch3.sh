#!/bin/sh
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/cin3
python "$S/jedit.py" c03 "$S/e_c03l.py"
python "$S/prev.py" c03 h5 34 --clean --wait 60 --stills 2 --only 4,6,8 --cols 2 --width 960 | grep 'lamp=\|stills'
python "$S/prev.py" c02 h6 50 --clean --wait 60 --stills 2 --only 7,8,9 --cols 2 --width 960 | grep 'lamp=\| her \|stills'
echo BATCH DONE
