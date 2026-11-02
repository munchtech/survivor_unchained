#!/bin/bash
# shoot_prop.sh NAME day|night [extra args]  (godot turn held). Her (warden, idle, facing camera) with the sunder blade planted.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-59
G=C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
O=/c/Users/munch/Desktop/survivorsunchained_inputs/anim59/prop
N=$1; MODE=$2; shift 2
if [ "$MODE" = night ]; then Z="--zone arena --time night"; elif [ "$MODE" = vnight ]; then Z="--zone verge --time night"; else Z="--zone verge --time day"; fi
PROP=${PROP:-arm:sunder_blade@-0.45,0.5,15,0.15}
cd $W/godot; mkdir -p $O/logs
rm -f .shots/${N}*.png
timeout 300 "$G" --path . --resolution 1920x1080 -- --shot $N $Z --quick warden --no-spawn --nohud --facing 0 --prop "$PROP" --seconds 6 --count 1 "$@" --sex female --preset own --skin fair --eyes moss --hair braid </dev/null > $O/logs/$N.log 2>&1
echo "$N rc=$?"
f=$(ls .shots/${N}*.png 2>/dev/null | head -1)
[ -n "$f" ] && mv "$f" $O/$N.png && echo "$N ok" || echo "$N MISSING"
grep -ai "prop:\|script error\|shader error\|ERROR:" $O/logs/$N.log | head -6
