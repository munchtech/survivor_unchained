#!/bin/bash
# Waits for a Godot turn, tests the motion check's new codes (calibration, false positives,
# the warden's sprint) from the repo tools into the scratchpad, and gives the turn back.
NAME="legal: test the check's new codes (aab20546)"
TURN="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
until $TURN take godot "$NAME" >/dev/null 2>&1; do sleep 60; done
echo "turn taken $(date +%H:%M)"
T=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-aab20546fe06daa89/tools/legal/motioncheck
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal"
# The tools run in the main checkout's imported project (the worktree has no import).
export OUT="$L/codes1"
mkdir -p "$OUT"
cp "$T"/*.py "$T"/run.sh "$OUT/" 2>/dev/null
ROOTFIX=/c/Users/munch/Desktop/survivorsunchained
python "$T/make_motioncheck.py" "$OUT/motioncheck.gd" >/dev/null
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
cd "$ROOTFIX/godot" || { $TURN give godot "$NAME"; exit 1; }
STAND="chest:0,1.45,1.3,1.30:35;left:45,1.40,1.2,1.28:36;side:90,1.30,1.3,1.25:38;below:0,0.95,1.2,1.25:42"
env FOV=38 HAIR=ponytail SPREAD=1 MARKS=1 FRAMES=1 VIEWS="chest:0,1.45,1.3,1.30:35;below:0,0.95,1.2,1.25:42;side:90,1.30,1.3,1.25:38" \
  timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- her/idle_warden "$OUT/calib/calib_idle.png" </dev/null >"$OUT/log_calib.txt" 2>&1
for o in warden arcanist ranger reaver; do
  env FOV=38 OUTFIT="$o" HAIR=ponytail SPREAD=1 LINEAR=1 FRAMES=4 VIEWS="$STAND" \
    timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- her/sprint_warden "$OUT/fp/fp${o}_sprint.png" </dev/null >"$OUT/log_fp_${o}.txt" 2>&1
done
env FOV=38 OUTFIT=warden HAIR=ponytail SPREAD=1 MARKS=1 FRAMES=16 VIEWS="$STAND" \
  timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- her/sprint_warden "$OUT/run/warden_sprint_warden.png" </dev/null >"$OUT/log_cup.txt" 2>&1
$TURN give godot "$NAME"
echo "turn given back $(date +%H:%M)"
grep -h "legal marks" "$OUT/log_calib.txt" "$OUT/log_cup.txt"
grep -h -E "SCRIPT ERROR|Parse Error|ERROR: .*shader" "$OUT"/log_*.txt | sort | uniq | head
echo TESTDONE
