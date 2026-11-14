#!/bin/bash
# tour.sh NAME CLIPS [extra game args]: her (warden look, own preset) plays CLIPS (comma list) once each at the play
# camera, windowed 1920x1080 at 60 fps, the armor-inside probe on (skirt, pauldrons, every 2nd frame) and PIECE_SPRINGS_DBG=1.
# Out: $O/NAME.jsonl (probe) and $O/NAME.log. Takes and gives back its own godot turn unless TURN_HELD=1.
# Before = add --springs off.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/zen-bell-95ec3f
G=C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
O=${O:-/c/Users/munch/Desktop/survivorsunchained_inputs/her_springs}
N=$1; CLIPS=$2; shift 2
mkdir -p $O
if [ -z "$TURN_HELD" ]; then
  python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "her-springs: tour $N" --wait 900 || { echo "NO TURN"; exit 1; }
fi
cd $W/godot
rm -f $O/$N.jsonl
PIECE_SPRINGS_DBG=1 timeout 1500 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --zone verge --time day --quick warden --sex female --preset own --skin fair --eyes moss --hair braid \
  --no-spawn --nohud --facing 0 --clip-tour $CLIPS --wear-inside $(cygpath -w $O/$N.jsonl) --wear-inside-every ${EVERY:-2} "$@" </dev/null > $O/$N.log 2>&1
echo "$N rc=$?"
[ -z "$TURN_HELD" ] && python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "her-springs: tour $N"
grep -ai "script error\|shader error\|ERROR:\|exception" $O/$N.log | head -8
