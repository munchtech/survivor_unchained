#!/bin/bash
# shoot.sh <list> : armor lead 2's wear shots, one godot turn (held by the caller). Each list line: NAME|ARGS
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-1
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
O=$W/godot/.shots/armor4/probe; mkdir -p $O
cd $W/godot
while IFS='|' read n args; do
  [ -z "$n" ] && continue; case "$n" in \#*) continue;; esac
  rm -f .shots/$n.png .shots/${n}_*.png
  timeout 400 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- $args --shot $n --count 1 </dev/null >"$O/log_$n.txt" 2>&1
  r=$?; f=$(ls .shots/$n*.png 2>/dev/null | head -1)
  if [ -n "$f" ]; then mv "$f" "$O/$n.png"; echo "$n ok"; else echo "$n MISSING exit $r"; fi
  grep -E "her wear|wear:|ERROR|SCRIPT ERROR" "$O/log_$n.txt" | head -5
done < "$1"   # (an absolute path: the loop runs in godot/)
echo STEP DONE
