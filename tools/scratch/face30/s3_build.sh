#!/bin/sh
# Face 30 S3: build ponytail and braid into $1 (blender turn held).
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0
cd $W
python tools/turn.py take blender "face30: s3 build" --wait 3600 --root $W || exit 1
"/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_hair.py -- "$1" ponytail braid > "$1/build.log" 2>&1
echo "blender exit $?"
python tools/turn.py give blender "face30: s3 build"
grep -n "chain margin\|tail:\|braid:\|tendrils\|hairline\|STYLE\|WRITTEN\|Error\|Traceback" "$1/build.log" | head -30
