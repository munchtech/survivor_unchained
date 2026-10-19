#!/bin/bash
# shadow.sh <outdir>: heroine_shadow.png rebuilt twice (HAIRLINE_ACROSS=0 into <outdir>/old, =1 into <outdir>/new), one blender turn.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1941eef2c79c45fe
SRC=${SRC:-/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/181eef02-779f-45de-b419-31a949a4d27e/scratchpad/outfits/hs/heroine_built.blend}
O=$1; mkdir -p $O/old $O/new; cd $W
python tools/turn.py take blender "touchup: scalp shade" --wait 3600 --root $W --stale-ok >/dev/null || exit 1
for v in old new; do
  a=0; [ $v = new ] && a=1
  HAIRLINE_ACROSS=$a SHADOW_ONLY=1 "/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b "$SRC" --python tools/assets/heroine_features.py -- "$(cygpath -m $O/$v)" > $O/$v.log 2>&1 < /dev/null
  echo "$v exit $?"; grep -n "SCALP\|Error\|Traceback" $O/$v.log | head -3
done
python tools/turn.py give blender "touchup: scalp shade" >/dev/null
