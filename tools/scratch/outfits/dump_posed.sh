#!/bin/bash
# dump.sh <outdir> "outfit clip frames" ... : shoulder-framed frames (960x540) plus posed-mesh dumps (DUMP=1), one Godot turn
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a5ca10091b08dc429
D="$1"; shift; mkdir -p "$D"
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
V="${VIEWS:-shl:70,1.50,0.42,1.42:30;shf:20,1.55,0.42,1.42:30;shb:120,1.50,0.42,1.42:30}"
python $WT/tools/legal/motioncheck/make_motioncheck.py $D/motioncheck.gd >/dev/null || exit 1
until $T take godot "outfits lead: dump frames" --wait 60 >/dev/null 2>&1; do :; done
cd $WT/godot
for spec in "$@"; do set -- $spec
  env FOV=30 OUTFIT="$1" HAIR=ponytail SPREAD=1 FRAMES=$3 VIEWS="$V" DUMP=1 $EXTRA \
    timeout 600 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$D/motioncheck.gd" -- "her/$2" "$D/${1}_$2.png" </dev/null >"$D/log_${1}_$2.txt" 2>&1
  echo "$1 $2 $(ls $D/${1}_$2*_posed.json 2>/dev/null | wc -l) dumps"
done
$T give godot "outfits lead: dump frames" >/dev/null
echo DUMPDONE
