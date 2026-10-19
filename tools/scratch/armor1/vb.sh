#!/bin/bash
# vb.sh <tag> [K=V ...]: a full build (all four outfits + her body, --body) into $X/prop/<tag>/art, under a blender turn.
# The build also rewrites godot/art/outfit/ (textures; a fixed path): restored from git after, unless KEEP_TEX=1.
X=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-1/.shots/armor1
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-1
OSCR=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/181eef02-779f-45de-b419-31a949a4d27e/scratchpad/outfits
SRC=${SRC:-$OSCR/hs/heroine_built.blend}
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"; tag=$1; shift; O=$X/prop/$tag; mkdir -p $O/art
echo "$@ SRC=$SRC" > $O/env.txt
while :; do $T take blender "armor: build $tag" --wait 60 --root $WT >/dev/null 2>&1; r=$?; [ $r -eq 0 ] && break; [ $r -eq 2 ] && { echo STALE; exit 2; }; done
echo "blender $(date +%H:%M:%S)"
cd $WT
env "$@" timeout 7000 "/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b "$SRC" --python tools/assets/heroine_outfits.py -- "$(cygpath -m $O/art/x)" --body "$(cygpath -m $O/art/heroine.glb)" > $O/outfits.log 2>&1 < /dev/null
echo "blender exit $? $(date +%H:%M:%S)"
$T give blender "armor: build $tag" >/dev/null
mkdir -p $O/outfit_tex && cp -r godot/art/outfit/. $O/outfit_tex/
[ -n "$KEEP_TEX" ] || git checkout -- godot/art/outfit
grep -E "Error|Traceback|BODY|HIDES" $O/outfits.log | head -12
ls $O/art
echo VB_DONE
