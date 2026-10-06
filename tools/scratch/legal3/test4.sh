#!/bin/bash
# Second short Godot batch: the posed-tip landmarks re-checked on calibration, the credits
# screen's AI section and licence pages, and the Quaternius bodies' textures dumped.
NAME="legal: landmark check (af0973d5)"
TURN="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
until $TURN take godot "$NAME" --wait 30 >/dev/null 2>&1; do :; done
echo "turn taken $(date +%H:%M:%S)"
T=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af0973d59a5b2817a/tools/legal/motioncheck
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal3"
OUT="$L/${RUNTAG:-t4}"
mkdir -p "$OUT/calib" "$OUT/run"
python "$T/make_motioncheck.py" "$OUT/motioncheck.gd" >/dev/null
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
cd /c/Users/munch/Desktop/survivorsunchained/godot || { $TURN give godot "$NAME"; exit 1; }
STAND="chest:0,1.45,1.3,1.30:35;left:45,1.40,1.2,1.28:36;side:90,1.30,1.3,1.25:38;below:0,0.95,1.2,1.25:42"
env FOV=38 HAIR=ponytail SPREAD=1 MARKS=1 FRAMES=1 VIEWS="chest:0,1.45,1.3,1.30:35;below:0,0.95,1.2,1.25:42;side:90,1.30,1.3,1.25:38" \
  timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- her/idle_warden "$OUT/calib/calib_idle.png" </dev/null >"$OUT/log_calib.txt" 2>&1
env FOV=38 OUTFIT=warden HAIR=ponytail SPREAD=1 MARKS=1 FRAMES=4 VIEWS="$STAND" \
  timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- her/sprint_warden "$OUT/run/warden_sprint_warden.png" </dev/null >"$OUT/log_cup.txt" 2>&1
echo "motion done $(date +%H:%M:%S)"
$TURN give godot "$NAME"
echo "turn given back $(date +%H:%M:%S)"
grep -h "legal marks\|legal dump" "$OUT"/log_*.txt
grep -h -E "SCRIPT ERROR|Parse Error|SHADER ERROR" "$OUT"/log_*.txt | sort | uniq | head -20
ls "$OUT"
echo TESTDONE
