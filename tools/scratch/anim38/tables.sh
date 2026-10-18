#!/bin/sh
# All five fistfit tables in parallel. Usage: tables.sh <tag>
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d
O=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/463a4243-9324-49b0-bda9-b9fb9a9d68b1/scratchpad/a38/t_$1
mkdir -p $O
cd $W
python tools/anim/fistfit.py sword > $O/sword.txt 2>&1 &
python tools/anim/fistfit.py viking_sword > $O/viking.txt 2>&1 &
python tools/anim/fistfit.py staff > $O/staff.txt 2>&1 &
python tools/anim/fistfit.py daggers > $O/daggers.txt 2>&1 &
python tools/anim/fistfit.py daggers --side l > $O/daggers_l.txt 2>&1 &
wait
tail -n 1 $O/*.txt
