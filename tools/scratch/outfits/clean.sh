#!/bin/bash
# The motion check's own clips, cameras and frames rendered clean (no codes, the game's
# tonemapper), to read a flagged frame against the real picture. One Godot turn.
#   bash clean.sh <outfit> <tag> <clip> [clip ...]        (FLOOR=1 for the lying-down views)
#   RES=1920x1080 for full-size pictures (the coded ones are 960x540)
O="$1"; TAG="$2"; shift 2
WT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"  # (this worktree)
L="${OSCR:?set OSCR, the outfits scratch folder}/legal"
OUT="$L/$TAG/$O"; mkdir -p "$OUT"
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
N="outfits lead: clean frames, $O ($TAG)"
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
python "$WT/tools/legal/motioncheck/make_motioncheck.py" "$OUT/motioncheck.gd" >/dev/null || exit 1
STAND="chest:0,1.45,1.3,1.30:35;left:45,1.40,1.2,1.28:36;side:90,1.30,1.3,1.25:38;below:0,0.95,1.2,1.25:42;over:15,2.20,0.65,1.30:38"
FLOORV="low:0,0.55,1.9,0.25:45;lowside:90,0.55,1.9,0.25:45;top:25,2.0,1.4,0.25:50"
until $T take godot "$N" --wait 60 >/dev/null 2>&1; do :; done
cd $WT/godot
for clip in "$@"; do
  case $clip in death|death_back|get_up|lie_side_wake|sit_log|sit_back_heels) V="$FLOORV";; *) V="${VIEWS:-$STAND}";; esac
  case $clip in dash|leap|vault|vault_back|bull_rush|chain_haul|death|death_back|get_up|lie_side_wake|sit_log|sit_back_heels) F=1;; *) F="";; esac
  env FOV=38 OUTFIT="$O" HAIR=ponytail SPREAD=1 FRAMES=${FRAMES:-10} VIEWS="$V" FOLLOW="$F" $EXTRA \
    timeout 300 "$G" --path . --resolution ${RES:-960x540} --fixed-fps 60 -s "$OUT/motioncheck.gd" -- "her/$clip" "$OUT/${O}_${clip}.png" \
    </dev/null >"$OUT/log_${O}_${clip}.txt" 2>&1
  echo "$clip $(ls "$OUT" | grep -c "^${O}_${clip}_.*png")"
done
$T give godot "$N" >/dev/null
echo CLEANDONE
