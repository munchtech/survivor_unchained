# Body 2 B: export the nude body (+ warden, as g2c/run.sh's last step) from a source blend, under the shared lock.
#   bash exp.sh <source.blend> <out dir> <lock dir parent>
set -u
SRCB=$1; OUT=$2; LK=$3/export.lock
W=$(cd "$(dirname "$0")/../../../.." && pwd); BL=C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe
until mkdir "$LK" 2>/dev/null; do echo "lock busy"; sleep 60; done
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take blender "body2 B: export" --wait 900
mkdir -p "$OUT"
( cd $W && NAPE=0 "$BL" -b "$SRCB" --python tools/assets/heroine_outfits.py -- "$OUT/x" --body "$OUT/heroine.glb" --only warden ) > "$OUT.log" 2>&1
echo "exit $?"
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give blender "body2 B: export"
git -C $W checkout -- tools/assets/heroine_neck_graft.npz
rmdir "$LK"
ls -la "$OUT"; grep -iE "error|traceback" "$OUT.log" | head -5; tail -2 "$OUT.log"
