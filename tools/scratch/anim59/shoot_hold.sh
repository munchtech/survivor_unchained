#!/bin/bash
# shoot_hold.sh NAME TIME_S day|night FACING [extra game args]
# Her (warden look, own preset, fair, moss, braid) holding sunder_blade in flare_long_cut held at TIME_S seconds with the
# clip's own legs (--hold-full), the game's PLAY camera, 1920x1080, no HUD; FACING in degrees (0 = toward the camera).
# Frames to survivorsunchained_inputs/anim59/clip/NAME.png (+ NAME_half.jpg). Takes and gives back its own godot turn
# unless TURN_HELD=1. CLIP=other_clip overrides the clip; HELD=piece the right-hand piece.
# Needs the clip packed (python tools/anim/build.py flare_long_cut) and the C# built (dotnet build in godot/).
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-59
G=C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
O=/c/Users/munch/Desktop/survivorsunchained_inputs/anim59/clip
N=$1; T=$2; MODE=$3; FC=${4:-0}; shift 4
CLIP=${CLIP:-flare_long_cut}; HELD=${HELD:-sunder_blade}
if [ "$MODE" = night ]; then Z="--zone verge --time night"; else Z="--zone verge --time day"; fi
mkdir -p $O/logs
if [ -z "$TURN_HELD" ]; then
  python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "anim59: shoot $N" --wait 600 || { echo "NO TURN"; exit 1; }
fi
cd $W/godot
rm -f .shots/${N}*.png
timeout 300 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --shot $N $Z --quick warden --sex female --preset own --skin fair --eyes moss --hair braid \
  --no-spawn --nohud --facing $FC --held-right $HELD --hold $CLIP@$T --hold-full --seconds 6 --count 1 "$@" </dev/null > $O/logs/$N.log 2>&1
echo "$N rc=$?"
[ -z "$TURN_HELD" ] && python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "anim59: shoot $N"
f=$(ls .shots/${N}*.png 2>/dev/null | head -1)
if [ -n "$f" ]; then mv "$f" $O/$N.png; python $W/tools/half.py $O/$N.png >/dev/null; echo "$N ok"; else echo "$N MISSING"; fi
grep -ai "script error\|shader error\|ERROR:" $O/logs/$N.log | head -6
