#!/bin/bash
# lab.sh TAG CALLING [extra args...] : the survivor standing still, a pack at arm's length, a burst of frames tiled into scratchpad/TAG.jpg
cd /c/Users/munch/Desktop/survivorsunchained/godot
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
T=$1; C=$2; shift 2
dotnet build SurvivorUnchained.csproj -v q -nologo 2>&1 | grep -E " error |rror\(s\)" | grep -v " 0 Error"
rm -f .shots/${T}_*
"$G" --path . -- --quick $C --zone arena --people pack ${HORDE:---horde 14:wolf --dist 2.5 --spread 1.5} --cam 8 --auto idle --shot $T --seconds ${SEC:-2.5} --every ${EVERY:-0.033} --count ${COUNT:-16} "$@" > /tmp/lab_$T.log 2>&1
grep -iE "exception|SHADER ERROR" /tmp/lab_$T.log | head -5
cd .shots && python $S/grid.py $S/$T.jpg 4 ${T}_*.png
