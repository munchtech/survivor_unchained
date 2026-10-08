#!/bin/bash
# Joint sheets with and without her helper bones, in one Godot turn.
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ae2a9884e3e51609c
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/0b33992d-1e38-4eb8-80a1-d5c23b1a44e6/scratchpad/an
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
O=$S/sh2
SW=C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/0b33992d-1e38-4eb8-80a1-d5c23b1a44e6/scratchpad/an
mkdir -p $O
W="animation: joint sheets"
until $T take godot "$W" --wait 60 >/dev/null 2>&1; do :; done
echo "godot turn $(date +%H:%M:%S)"
cd $WT/godot

# shot <tag> <clip> <frames> [env...]: the same sheet with the helpers (a) and without (b)
shot() {
  tag=$1; clip=$2; n=$3; shift 3
  for j in a b; do
    if [ $j = b ]; then bd=$SW/before/people; else bd=; fi
    env BODYDIR=$bd FRAMES=$n COLS=$n HAIR=none "$@" timeout 300 "$G" --path . --fixed-fps 30 --resolution 400x400 -s res://tools_scenes/anim_review.gd -- "$clip" "$O/${tag}_$j.png" </dev/null >"$O/${tag}_$j.log" 2>&1
    grep -E "SHEET|ERROR|error" "$O/${tag}_$j.log" | head -3
  done
}

shot arm_side $SW/clips/rig_arm.json 8 OUTFIT=none W=400 H=400 LOOK=lowerarm_l VIEW=side ZOOM=5 FIXCAM=1
shot arm_front $SW/clips/rig_arm.json 8 OUTFIT=none W=400 H=400 LOOK=lowerarm_l VIEW=front ZOOM=5 FIXCAM=1
shot arm_back $SW/clips/rig_arm.json 8 OUTFIT=none W=400 H=400 LOOK=lowerarm_l VIEW=back ZOOM=5 FIXCAM=1
shot sh_front $SW/clips/rig_shoulder.json 8 OUTFIT=none W=400 H=400 LOOK=upperarm_l VIEW=front ZOOM=3.2 FIXCAM=1
shot sh_side $SW/clips/rig_shoulder.json 8 OUTFIT=none W=400 H=400 LOOK=upperarm_l VIEW=side ZOOM=3.2 FIXCAM=1
shot knee_side $SW/clips/rig_knee.json 8 OUTFIT=none W=400 H=400 LOOK=calf_l VIEW=side ZOOM=3.5 FIXCAM=1
shot knee_back $SW/clips/rig_knee.json 8 OUTFIT=none W=400 H=400 LOOK=calf_l VIEW=back ZOOM=3.5 FIXCAM=1
# In motion, jiggle on: her own clips that bend the elbow most.
shot cast_raise her/cast_raise 16 OUTFIT=none W=400 H=400 LOOK=lowerarm_l VIEW=front ZOOM=3
shot cup_hands her/cup_hands 16 OUTFIT=none W=400 H=400 STEP=2 LOOK=lowerarm_r VIEW=front ZOOM=3
shot sword_fore her/sword_fore 16 OUTFIT=none WEAPON=sword W=400 H=400 LOOK=lowerarm_r VIEW=three ZOOM=3

$T give godot "$W" >/dev/null
echo "godot done $(date +%H:%M:%S)"
echo SHOTSDONE
