#!/bin/bash
# shot.sh NAME CLIP@T play|close FACING [extra game args]: her (warden look, own preset) held at CLIP@T with the clip's own
# legs (--hold-full), 1920x1080, no HUD, day; play = the game's play camera, close = the close view held at 1.
# Frame to $O/NAME.png (+ NAME_half.jpg), log $O/logs/NAME.log. Takes/gives its own godot turn unless TURN_HELD=1.
# Before = add --springs off.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/zen-bell-95ec3f
G=C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
O=${O:-/c/Users/munch/Desktop/survivorsunchained_inputs/her_springs/shots}
N=$1; HOLD=$2; CAM=$3; FC=$4; shift 4
[ "$CAM" = close ] && C="--close 1 --close-hold 1" || C=""
mkdir -p $O/logs
if [ -z "$TURN_HELD" ]; then
  python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "her-springs: shoot $N" --wait 900 || { echo "NO TURN"; exit 1; }
fi
cd $W/godot
rm -f .shots/${N}*.png
timeout 300 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --shot $N --zone verge --time day --quick warden --sex female --preset own --skin fair --eyes moss --hair braid \
  --no-spawn --nohud --facing $FC --hold $HOLD --hold-full --seconds 6 --count 1 $C "$@" </dev/null > $O/logs/$N.log 2>&1
echo "$N rc=$?"
[ -z "$TURN_HELD" ] && python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "her-springs: shoot $N"
f=$(ls .shots/${N}*.png 2>/dev/null | head -1)
if [ -n "$f" ]; then mv "$f" $O/$N.png; python $W/tools/half.py $O/$N.png >/dev/null; echo "$N ok"; else echo "$N MISSING"; fi
grep -ai "script error\|shader error\|exception" $O/logs/$N.log | head -4
