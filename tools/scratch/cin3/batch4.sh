#!/bin/sh
# Staging for every Prologue cinematic, clean of titles, after the lamp and heart fixes.
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/cin3
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a79b6d8c81e14dc63
python "$S/jedit.py" c01 "$S/e_c01i.py"
python "$S/prev.py" c01 st1 75 --clean --wait 90 --quiet | tail -1
python "$S/prev.py" c02 st2 80 --clean --wait 90 | grep 'lamp=\|stills' | tail -8
python "$S/prev.py" c03 st3 80 --clean --wait 90 | grep 'lamp=\|stills' | tail -8
python "$S/prev.py" c04a st4a 80 --clean --wait 90 --quiet | tail -1
python "$S/prev.py" c04b st4b 40 --zone waystation --clean --wait 90 --quiet | tail -1
cd "$W"
for c in "c01 st1" "c02 st2" "c03 st3" "c04a st4a" "c04b st4b"; do set -- $c; python tools/cinematics/boards.py $1 --stage $2 | tail -1; done
echo BATCH DONE
