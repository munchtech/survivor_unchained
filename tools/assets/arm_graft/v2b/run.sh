# Body 2 variant B: her ORIGINAL arm densified (her own UVs and paint, no bake), resculpted, weights fixed, left = mirrored right.
#   bash run.sh <work dir> [tag]        (knobs for shape.py by env; see shape.py K)
# her.npz = b_dump of heroine_built.blend -> dense.py -> shape.py -> b_write.py -> armor_src/heroine_built_armB.blend
# -> the nude body + warden export under <work dir>/../export.lock (exp.sh), the neck graft npz restored.
set -eu
WK=$1; TAG=${2:-b}
A=$(cd "$(dirname "$0")" && pwd); W=$(cd "$A/../../../.." && pwd)
BL=C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe; SRC=C:/Users/munch/Desktop/survivorsunchained_inputs/armor_src
TURN="python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
if [ ! -f "$WK/her.npz" ]; then $TURN take blender "body2 B: dump" --wait 900; "$BL" -b $SRC/heroine_built.blend --python $A/../b_dump.py -- "$WK/her.npz" | grep DUMPED; $TURN give blender "body2 B: dump"; fi
[ -f "$WK/dense.npz" ] || python $A/dense.py "$WK/her.npz" "$WK/dense.npz" 0.0075 | grep -vE "^  (pass|worst)"
python $A/shape.py "$WK/dense.npz" "$WK/shape_$TAG.npz" > "$WK/shape_$TAG.txt"; grep -E "moved|weights|onto" "$WK/shape_$TAG.txt"
$TURN take blender "body2 B: write blend" --wait 900
"$BL" -b $SRC/heroine_built.blend --python $A/b_write.py -- "$WK/shape_$TAG.npz" $SRC/heroine_built_armB.blend 2>&1 | grep -E "IMAGES|WROTE|SAVED|rror" || true
$TURN give blender "body2 B: write blend"
bash $A/exp.sh $SRC/heroine_built_armB.blend "$WK/exp_$TAG" "$(dirname "$WK")"
