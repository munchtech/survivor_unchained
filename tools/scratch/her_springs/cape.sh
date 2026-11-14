#!/bin/bash
# cape.sh: the Ford-Warden walking his circle beside her for 20 s, PIECE_SPRINGS_DBG=1, the old springs (--springs-legacy)
# then the new (TURN_HELD=1: the caller holds the godot turn); his cape's worst link inside each body capsule from the logs. Out: $O/cape_{legacy,new}.log. One turn.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/zen-bell-95ec3f
G=C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
O=${O:-/c/Users/munch/Desktop/survivorsunchained_inputs/her_springs}
if [ -z "$TURN_HELD" ]; then
  python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "her-springs: cape" --wait 900 || { echo "NO TURN"; exit 1; }
fi
cd $W/godot
for v in legacy new; do
  [ $v = legacy ] && X="--springs-legacy" || X=""
  PIECE_SPRINGS_DBG=1 timeout 300 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --shot cape_$v --zone verge --time day --quick warden --sex female --preset own \
    --no-spawn --nohud --npc ford_warden:walk --seconds 20 --count 1 $X </dev/null > $O/cape_$v.log 2>&1
  echo "$v rc=$?"
  rm -f .shots/cape_$v*.png
  grep -a "springs:.*inside (cm" $O/cape_$v.log | tail -2
done
[ -z "$TURN_HELD" ] && python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "her-springs: cape"
