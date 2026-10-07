#!/bin/bash
# The check's own calibration on this worktree's build, in one Godot turn: calib (codes on her,
# no outfit: they must read back), tuckcalib (each outfit's tucked skin), fp (each outfit
# without codes: nothing may read as a code).   bash calib.sh <tag>
TAG="$1"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-afb34c385770877d3
L=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/74e72383-70c7-41d5-8e96-2fad2ed58481/scratchpad/legal
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
N="outfits lead: motion check calibration ($TAG)"
until $T take godot "$N" --wait 60 >/dev/null 2>&1; do :; done
echo "turn taken $(date +%H:%M:%S)"
for ph in ${PHASES:-calib fp tuckcalib}; do
  OUT="$L/$TAG/$ph" PROJECT=$WT/godot bash "$WT/tools/legal/motioncheck/run.sh" "$ph" >"$L/$TAG.$ph.txt" 2>&1
  echo "$ph done $(date +%H:%M:%S)"
done
$T give godot "$N" >/dev/null
echo "turn given back $(date +%H:%M:%S)"
grep -h "legal marks" "$L/$TAG"/*/log_*.txt | sort | uniq | head -8
grep -h -E "SCRIPT ERROR|Parse Error|SHADER ERROR" "$L/$TAG"/*/log_*.txt | sort | uniq | head -10
for ph in ${PHASES:-calib fp tuckcalib}; do echo "== $ph"; python "$WT/tools/legal/motioncheck/count.py" "$L/$TAG/$ph" 6 | sed -n '5,30p'; done
echo CALIBDONE
