#!/bin/bash
# Weight variants (reweight.py, read at run time) with the round bulge law.
#   bash shots3.sh <out subdir> <variant dir under var/> <elbow b> <elbow max> <knee b> <knee max> [<variant dir> <eb> <em> <kb> <km>]...
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a8d33b2672b7be905
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/0b33992d-1e38-4eb8-80a1-d5c23b1a44e6/scratchpad/an
SW=C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/0b33992d-1e38-4eb8-80a1-d5c23b1a44e6/scratchpad/an
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
O=$S/$1
shift
mkdir -p $O
cp $WT/godot/art/people/rig_helpers.json $S/rig_helpers.keep.json
W="animation: weight variants"
until $T take godot "$W" --wait 60 >/dev/null 2>&1; do :; done
echo "godot turn $(date +%H:%M:%S)"
cd $WT/godot
one() {
  tag=$1; clip=$2; shift 2
  env FRAMES=8 COLS=8 HAIR=none OUTFIT=none W=400 H=400 FIXCAM=1 "$@" timeout 300 "$G" --path . --fixed-fps 30 --resolution 400x400 -s res://tools_scenes/anim_review.gd -- "$clip" "$O/$tag.png" </dev/null >"$O/$tag.log" 2>&1
  grep -cE "SHEET" "$O/$tag.log" >/dev/null || echo "FAILED $tag"
}
while [ $# -ge 5 ]; do
  v=$1
  python $S/variant.py $2 $3 $4 $5 >/dev/null
  shift 5
  bd=$SW/var/$v
  one arm_side_$v $SW/clips/rig_arm.json BODYDIR=$bd LOOK=lowerarm_l VIEW=side ZOOM=5
  one arm_back_$v $SW/clips/rig_arm.json BODYDIR=$bd LOOK=lowerarm_l VIEW=back ZOOM=5
  one arm_front_$v $SW/clips/rig_arm.json BODYDIR=$bd LOOK=lowerarm_l VIEW=front ZOOM=5
  one knee_side_$v $SW/clips/rig_knee.json BODYDIR=$bd LOOK=calf_l VIEW=side ZOOM=3.5
  one knee_back_$v $SW/clips/rig_knee.json BODYDIR=$bd LOOK=calf_l VIEW=back ZOOM=3.5
  echo "done $v $(date +%H:%M:%S)"
done
cp $S/rig_helpers.keep.json $WT/godot/art/people/rig_helpers.json
$T give godot "$W" >/dev/null
echo "godot done $(date +%H:%M:%S)"
echo SHOTSDONE
