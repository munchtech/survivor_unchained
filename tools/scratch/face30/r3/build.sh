#!/bin/sh
# Face 30 round 3: build braid, ponytail and pixie into $1 (blender turn held), then copy them (and chain.json) into godot/art/people.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0
cd $W
mkdir -p "$1"
python tools/turn.py take blender "face30: r3 build" --wait 3600 --root $W --stale-ok || exit 1
"/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_hair.py -- "$1" ponytail braid pixie > "$1/build.log" 2>&1
echo "blender exit $?"
python tools/turn.py give blender "face30: r3 build"
grep -n "chain\|tail\|braid:\|nape\|hairline\|STYLE\|WRITTEN\|Error\|Traceback" "$1/build.log" | head -40
