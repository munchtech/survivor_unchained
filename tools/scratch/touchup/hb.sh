#!/bin/bash
# hb.sh <outdir> <style...>: build hair styles into <outdir> (its head_tex seeded with the shipped atlas and scalp), under a blender turn.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1941eef2c79c45fe
SRC=${SRC:-/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/181eef02-779f-45de-b419-31a949a4d27e/scratchpad/outfits/hs/heroine_built.blend}
O=$1; shift; mkdir -p $O/head_tex
cp $W/godot/art/people/head_tex/hair_strands.png $W/godot/art/people/head_tex/hair_scalp.png $O/head_tex/
cd $W
python tools/turn.py take blender "touchup: hair $*" --wait 3600 --root $W --stale-ok >/dev/null || exit 1
"/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b "$SRC" --python tools/assets/heroine_hair.py -- "$(cygpath -m $O)" "$@" > $O/build.log 2>&1 < /dev/null
echo "blender exit $?"
python tools/turn.py give blender "touchup: hair $*" >/dev/null
grep -n "braid:\|WRITTEN\|Error\|Traceback" $O/build.log | head
