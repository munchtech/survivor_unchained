#!/bin/bash
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-1
O=$WT/.shots/armor1/list; mkdir -p $O
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
while :; do $T take blender "armor: list pieces" --wait 60 >/dev/null 2>&1; r=$?; [ $r -eq 0 ] && break; done
cd $WT
LIST_OUT="$(cygpath -m $O/pieces.json)" timeout 3000 "/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b "/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/181eef02-779f-45de-b419-31a949a4d27e/scratchpad/outfits/hs/heroine_built.blend" --python tools/scratch/armor1/list.py -- "$(cygpath -m $O/x)" > $O/list.log 2>&1 < /dev/null
echo "exit $?"
$T give blender "armor: list pieces" >/dev/null
grep -E "Error|Traceback|LISTED" $O/list.log | head
