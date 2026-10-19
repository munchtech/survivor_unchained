#!/bin/bash
# perf.sh : three alternating 20 s play-camera runs, full warden vs the mixed look (caller holds the godot turn)
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-1
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
O=$W/godot/.shots/armor2; mkdir -p $O
cd $W/godot
for i in 1 2 3; do
  for k in full mix; do
    a="--quick warden --sex female --nohud --zone waystation --seed 1"
    [ $k = mix ] && a="$a --wear warden.top,ranger.bottom,ranger.boots"
    timeout 300 "$G" --path . --resolution 1920x1080 -- $a --perf wr2_${k}_$i --perf-for 20 </dev/null >"$O/perf_${k}_$i.txt" 2>&1
    echo "$k $i exit $?: $(grep -E "perf wr2_${k}_$i done" "$O/perf_${k}_$i.txt" | cut -c1-400)"
  done
done
echo STEP DONE
