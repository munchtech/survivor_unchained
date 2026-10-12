#!/bin/bash
# The new hero: import, then his views. Usage: shoot2.sh <out dir> [names...]
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ac39445bca5508eaf
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
O=$1; shift
mkdir -p $O
cd $WT
$G --headless --path godot --import > $O/import.log 2>&1
R=2560x1440
shot() { # name env...
  local n=$1; shift
  env "$@" NOLIFE=1 $G --path godot --resolution $R -s res://tools_scenes/lookdev.gd -- ${CLIP:-Idle} $O/$n.png > $O/$n.log 2>&1
  [ -f $O/$n.png ] && echo "ok $n" || echo "FAIL $n"
}
H="BODY=hero HAIR=none FOV=30 $EXTRA"
shot hero_front $H ORBIT=0,1.05,4.6,1.0
shot hero_side $H ORBIT=90,1.05,4.6,1.0
shot hero_back $H ORBIT=180,1.05,4.6,1.0
shot hero_q $H ORBIT=35,1.05,4.6,1.0
shot hero_torsoF $H ORBIT=0,1.4,1.7,1.32
shot hero_torsoB $H ORBIT=180,1.4,1.7,1.32
shot hero_torsoS $H ORBIT=70,1.4,1.7,1.32
shot hero_face $H ORBIT=0,1.86,0.75,1.82
shot hero_face34 $H ORBIT=35,1.86,0.75,1.80
