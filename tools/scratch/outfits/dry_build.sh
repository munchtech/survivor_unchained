#!/bin/bash
# The outfits build run into a scratch folder (not the worktree), in a Blender turn: to read its
# log and compare its outputs with the committed ones without touching the worktree's art.
#   bash dry_build.sh <tag> [extra args for heroine_outfits.py, e.g. --only reaver]
TAG="$1"; shift
WT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"  # (this worktree)
S="${OSCR:?set OSCR, the outfits scratch folder}/hs"
D="$S/dry_$TAG"; mkdir -p "$D/godot/art/people"
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
W="outfits lead: dry build ($TAG)"
until $T take blender "$W" --wait 60 >/dev/null 2>&1; do :; done
echo "blender turn $(date +%H:%M:%S)"
cd "$D"
timeout 7000 "/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b "$S/heroine_built.blend" --python "$WT/tools/assets/heroine_outfits.py" -- godot/art/people/x --body godot/art/people/heroine.glb "$@" > "$D/outfits.log" 2>&1
echo "blender exit $?"
$T give blender "$W" >/dev/null
echo "blender done $(date +%H:%M:%S)"
grep -E "Error|Traceback|NIPPLE|LANDMARKS|BODY|OUTFIT |PLATE CUP|HIDES" "$D/outfits.log" | head -30
echo DRYDONE
