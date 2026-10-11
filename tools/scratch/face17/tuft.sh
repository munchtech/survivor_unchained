#!/bin/bash
# tuft.sh TAG: arcanist chain_haul with the ponytail, the outfits judge's plain views (o3/plain.sh), in this worktree.
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0
D=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/91211d34-e079-4956-a2a0-7b52c04594a8/scratchpad/f18/tuft
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
STAND="${VIEWSET:-chest:0,1.45,1.3,1.30:35;over:15,2.20,0.65,1.30:38}"
python $WT/tools/legal/motioncheck/make_motioncheck.py $D/motioncheck.gd >/dev/null || exit 1
$T take godot "face: tuft $1" --wait 1800 >/dev/null 2>&1
cd $WT/godot
if [ -n "$IMPORT" ]; then timeout 1500 "$G" --headless --path . --import >"$D/import_$1.txt" 2>&1; echo "import $?"; fi
env FOV=38 OUTFIT="arcanist" HAIR=${STYLE:-ponytail} SPREAD=1 FRAMES=${NF:-10} VIEWS="$STAND" FOLLOW="1" \
  timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$D/motioncheck.gd" -- "her/${CLIP:-chain_haul}" "$D/$1.png" </dev/null >"$D/log_$1.txt" 2>&1
echo "exit $?"
$T give godot "face: tuft $1" >/dev/null
ls $D | grep "^$1" | head -30
