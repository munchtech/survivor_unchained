#!/bin/bash
# shoot.sh <list> <outdir>: animation 45's NPC shots (GameNpcShot --npc), one godot turn. Each list line: NAME|ARGS
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
L=$(realpath $1); mkdir -p $2; O=$(realpath $2)
python $W/tools/turn.py take godot "anim-45: npc shots" --wait 900 --root $W || { echo "NO TURN"; exit 1; }
cd $W/godot
while IFS='|' read n args; do
  [ -z "$n" ] && continue; case "$n" in \#*) continue;; esac
  rm -f .shots/$n.png .shots/${n}_*.png
  timeout 400 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- $args --shot $n --count 1 </dev/null >"$O/log_$n.txt" 2>&1
  r=$?; f=$(ls .shots/$n*.png 2>/dev/null | head -1)
  if [ -n "$f" ]; then mv "$f" "$O/$n.png"; echo "$n ok"; else echo "$n MISSING exit $r"; fi
  grep -E "npc shot:|SCRIPT ERROR|ERROR" "$O/log_$n.txt" | head -3
done < $L
python $W/tools/turn.py give godot "anim-45: npc shots" --root $W
echo STEP DONE
