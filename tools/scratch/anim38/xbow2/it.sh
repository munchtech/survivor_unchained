#!/bin/sh
# it.sh <clips...>: build (heroine), armscheck crossbow, motion right arm, stock yaw/pitch
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d
S=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d/tools/scratch/anim38/xbow2
cd $W
python tools/anim/build.py --no-pack "$@" | grep -E "^\s+\w" | awk '{print $1}' | tr '\n' ' '; echo
python tools/anim/armscheck.py "$@" --sets crossbow 2>&1 | grep -E "^[a-z_]+ +crossbow" | cut -c1-120 &
python tools/anim/motion.py "$@" 2>&1 | grep "|" | cut -c1-110 &
python $S/yaw.py "$@" &
wait
