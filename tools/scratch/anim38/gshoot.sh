#!/bin/bash
# gshoot.sh <list> <outdir>: lead 34's game-camera shots. Each list line: NAME|QUICK|WEAPON|CLIP@SECONDS|TIME|CLOSE|FACING
# Real game (waystation, --nohud), 1920x1080 native, her clip held by --hold (PlayerView). One godot turn for the list.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
L=$(realpath $1); mkdir -p $2; O=$(realpath $2)
python $W/tools/turn.py take godot "animation 38: game-camera shots" --wait 600 --stale-ok --root $W || { echo "NO TURN"; exit 1; }
(cd $W/godot && timeout 1200 "$G" --headless --path . --import > $O/import.log 2>&1; echo IMPORT $?)
(cd $W/tools/anim && python -c "import build; build.pack()") && echo PACKED_OK
cd $W/godot
while IFS='|' read n q wp hold tm cl fc; do
  [ -z "$n" ] && continue; case "$n" in \#*) continue;; esac
  extra=""; [ "$wp" != "-" ] && extra="--weapon $wp"; [ "$cl" != "0" ] && extra="$extra --close $cl"
  rm -f .shots/$n.png .shots/${n}_*.png
  timeout 300 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --quick $q --sex female --nohud --zone waystation --time $tm $extra --facing $fc --hold $hold --shot $n --seconds 6 --count 1 </dev/null >"$O/log_$n.txt" 2>&1
  r=$?; f=$(ls .shots/$n*.png 2>/dev/null | head -1)
  if [ -n "$f" ]; then cp "$f" "$O/$n.png"; echo "$n ok"; else echo "$n MISSING exit $r"; fi
done < $L
python $W/tools/turn.py give godot "animation 38: game-camera shots" --root $W
echo STEP DONE
