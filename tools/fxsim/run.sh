#!/usr/bin/env bash
# run.sh NAME [boom_sim args]: one Blender sim+render under a blender turn, then a preview strip.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af0782e2e3f51bc1f
N=$1; shift
mkdir -p $W/tools/fxsim/.shots
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take blender "flare: boom sim $N" --wait 600 --root $W || exit 1
cd $W && timeout 3000 /c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe -b -P tools/fxsim/boom_sim.py -- tools/fxsim/.shots/$N "$@" > tools/fxsim/.shots/$N.log 2>&1
echo "blender exit $?"
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give blender "flare: boom sim $N"
grep -E "Error|BAKED|RENDERED|Traceback" -A3 tools/fxsim/.shots/$N.log | grep -v INFO | head -12
python tools/fxsim/pack.py preview tools/fxsim/.shots/$N tools/fxsim/.shots/${N}_prev.jpg --every ${EVERY:-4} --cell ${CELL:-256}
