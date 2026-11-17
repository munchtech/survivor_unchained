#!/bin/bash
# Lane G motion probe (16 Nov): A | B playing the same clips (--clip-tour) at the play camera and at close_town, 1:1 1920x1080,
# N frames a clip (--clip-tour-shots, evenly over its length) and the pose ruler's full dump every 2nd frame (each row tagged with
# the clip and its time: P1PoseProbe). Numbers: tools/body/motion_b.py. Raw frames in the worktree's git-ignored godot/.shots/motion_b/.
# usage: motion_b.sh [CLIPS] [BODIES] [CAMS]   (defaults below). Takes and gives back the godot turn (one take for the whole run).
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a8359f8b3c48d4eb8
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
TURN=/c/Users/munch/Desktop/survivorsunchained/tools/turn.py
O=$WT/godot/.shots/motion_b
CLIPS=${1:-run_warden,sword_fore,sword_back,sword_heavy,idle_warden,walk_warden,sprint_warden,stop_warden_l,stop_warden_r}
BODIES=${2:-A B}; CAMS=${3:-play side close}; N=${N:-8}
C0="--sex female --quick warden --preset own --skin fair --eyes moss --hair braid --no-spawn --nohud --no-pointer --time day"
declare -A CAM
CAM[play]="--zone waystation --facing 0"
CAM[side]="--zone waystation --facing 90"   # the play camera, her side on (the sword arm)
CAM[close]="--zone waystation --close 1 --facing 0"
python $TURN take godot "lane G: motion probe A|B" --wait 900 || { echo "NO TURN"; exit 2; }
cd $WT/godot
for BODY in $BODIES; do for K in $CAMS; do
  D=$O/$BODY/$K; mkdir -p $D
  X=""; [ $BODY = B ] && X="--body p1"
  timeout 900 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --shot mb_${BODY}_${K} --seconds 999 --count 0 ${CAM[$K]} $C0 $X \
    --clip-tour $CLIPS --clip-tour-shots $N --clip-tour-wait ${WAIT:-420} --pose-probe $(cygpath -w $D/pose.jsonl) --pose-probe-full $(cygpath -w $D/full.jsonl) \
    --pose-probe-every 2 </dev/null > $D/run.log 2>&1
  echo "== $BODY $K exit $?"; grep -a "clip-tour:" $D/run.log | grep -v end | tr '\n' ';'; echo
  grep -ai "script error\|ERROR:\|exception" $D/run.log | head -3
  for f in $(grep -ao "saved [^ ]*\.png" $D/run.log | cut -d' ' -f2); do mv "$f" $D/; done
done; done
python $TURN give godot "lane G: motion probe A|B"
echo DONE
