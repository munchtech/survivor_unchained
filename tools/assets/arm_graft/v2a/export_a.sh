# Body 2 A: the gate export of heroine_built_armA.blend (nude body + warden, NAPE=0) under body2/export.lock and a Blender turn.
#   bash export_a.sh <out dir> [tag]
set -u
OUT=$1; TAG=${2:-A}
B=C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/23290ad1-ed63-4a0d-8e12-ac0911d16c27/scratchpad/body2
W=C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-7; M=C:/Users/munch/Desktop/survivorsunchained
BL=C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe; SRC=C:/Users/munch/Desktop/survivorsunchained_inputs/armor_src
until mkdir "$B/export.lock" 2>/dev/null; do sleep 60; done
python $M/tools/turn.py take blender "body2 A: export $TAG" --wait 900 | tail -1
mkdir -p "$OUT"
( cd $W && NAPE=0 "$BL" -b $SRC/heroine_built_armA.blend --python tools/assets/heroine_outfits.py -- "$OUT/x" --body "$OUT/heroine.glb" --only warden ) > "$OUT/export.log" 2>&1
( cd $W && git checkout -- tools/assets/heroine_neck_graft.npz )
python $M/tools/turn.py give blender "body2 A: export $TAG" | tail -1
rmdir "$B/export.lock"
ls -la "$OUT/heroine.glb"; tail -2 "$OUT/export.log"; git -C $W status --short tools/assets/heroine_neck_graft.npz
echo EXPORT_DONE
