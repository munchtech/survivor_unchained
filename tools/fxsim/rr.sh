#!/usr/bin/env bash
# rr.sh BAKE NAME [boom_sim args]: a render-only run of bake BAKE's cache into .shots/NAME (shading trials), under a
# blender turn. e.g. tools/fxsim/rr.sh c1 c1s1 --take burns_boom4 --only 4,11,21 --set "smoke_k=30"
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af0782e2e3f51bc1f
B=$1; N=$2; shift 2
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take blender "flare: boom render $N" --wait 600 >/dev/null || exit 1
cd $W && timeout 3000 /c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe -b -P tools/fxsim/boom_sim.py -- tools/fxsim/.shots/$N --render-only --cache tools/fxsim/.shots/$B/cache "$@" > tools/fxsim/.shots/$N.log 2>&1
echo "blender exit $?"
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give blender "flare: boom render $N" >/dev/null
grep -E "Error|RENDERED|Traceback" -A3 tools/fxsim/.shots/$N.log | grep -v INFO | head -8
