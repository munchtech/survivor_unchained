#!/bin/bash
# Body-bar shoot: hero vs heroine, same light and camera. The window caps at 2526x1421.
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ac39445bca5508eaf
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
O=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/ba85aba8-36f4-4cf9-99c5-4c5ef9e4a65c/scratchpad/b1
cd $WT
R=2560x1440
shot() { # name env...
  local n=$1; shift
  env "$@" NOLIFE=1 $G --path godot --resolution $R -s res://tools_scenes/lookdev.gd -- Idle $O/$n.png > $O/$n.log 2>&1
  [ -f $O/$n.png ] && echo "ok $n" || echo "FAIL $n"
}
H="BODY=hero HAIR=none SCALP=0.55 BEARD=0.35 FOV=30"
F="BODY=heroine HAIR=pixie FOV=30"
shot hero_face $H ORBIT=0,1.86,0.75,1.82
shot hero_face34 $H ORBIT=35,1.86,0.75,1.80
for v in 0:front 90:side 180:back 35:q; do a=${v%%:*}; n=${v##*:}
  shot hero_$n $H ORBIT=$a,1.05,4.6,1.0
  shot her_$n $F ORBIT=$a,1.05,4.6,1.0
done
shot hero_torsoF $H ORBIT=0,1.4,1.7,1.32
shot hero_torsoB $H ORBIT=180,1.4,1.7,1.32
shot hero_torsoS $H ORBIT=70,1.4,1.7,1.32
shot hero_legs $H ORBIT=25,0.6,2.2,0.55
shot her_face $F ORBIT=0,1.75,0.72,1.71
