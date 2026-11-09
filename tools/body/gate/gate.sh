#!/bin/bash
# P1 gate reshoot: F2's set.sh commands; takes and gives back the godot turn
SP="C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/c88e97d2-7d20-4384-a940-bbff97ea5906/scratchpad/shots"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/body-p1
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
TURN=/c/Users/munch/Desktop/survivorsunchained/tools/turn.py
C="--hair braid --nohud --hide-slots all --time day --seconds 5 --open-eyes"
declare -A J
J[look_look]="--new --sex female --step 1 --archetype reaver --zoom 0.45 $C"
J[close_town]="--zone waystation --quick reaver --close 1 --idle-after 1 $C"
J[play_town]="--zone waystation --quick reaver $C"
J[play_play]="--zone arena --quick reaver --auto idle $C"
python $TURN take godot "P1 gate: shots" --wait 90 || { echo "NO TURN"; exit 2; }
cd $WT/godot
run() { name=$1; shift; timeout 400 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --shot $name "$@" > "$SP/$name.log" 2>&1; echo "== $name exit $?"; grep -E "saved|ERROR|Exception" "$SP/$name.log" | head -3; }
for k in look_look close_town play_town play_play; do
  run ${k}_A ${J[$k]}
  run ${k}_B ${J[$k]} --body p1 --p1-probe
done
python $TURN give godot "P1 gate: shots"
echo DONE
