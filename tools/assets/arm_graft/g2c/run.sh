# Body 1 g2c: the whole arm-root chain from the ORIGINAL blend (armor 18, 22 Oct 2026).
#   bash run.sh <work dir> <weights source dump.npz> <VG_v1.npy> <people dir for the skeleton> [tag]
# graft (ARM_TO=wrist, forearm loop cuts FA_CUT=0.5; the trap cut as g1: TRAP=0.5, TRAP_CL=0.3) -> b_write -> b_dump -> post.py (G2b weights carried, shape field + pit fairing)
# -> g2b/w_write.py -> heroine_built_armroot.blend; then the body + warden export (NAPE=0) and the neck graft npz restored.
set -eu
WK=$1; WSRC=$2; WVG=$3; PEOPLE=$4; TAG=${5:-g2c}
W=$(cd "$(dirname "$0")/../../../.." && pwd); A=$W/tools/assets/arm_graft
B=C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe
SRC=C:/Users/munch/Desktop/survivorsunchained_inputs/armor_src
export ARM_GRAFT_WORK=$(cygpath -w "$WK") ARM_TO=wrist WRIST_TF=${WRIST_TF:-0.98} WRIST_HW=${WRIST_HW:-0.6} TRAP=${TRAP:-0.5} TRAP_CL=${TRAP_CL:-0.3} WRIST_TC=${WRIST_TC:-0.85} WRIST_CORNER=${WRIST_CORNER:-1} GAP=${GAP:-0.008} UNT=${UNT:-30} ELBOW_IT=${ELBOW_IT:-0} TOP_IT=${TOP_IT:-80} TOP_PHI1=${TOP_PHI1:-60}
[ -f "$WK/her.npz" ] || "$B" -b $SRC/heroine_built.blend --python $A/b_dump.py -- "$WK/her.npz"
[ -n "${SKIP_GRAFT:-}" ] || python $W/tools/assets/heroine_arm_graft.py
"$B" -b $SRC/heroine_built.blend --python $A/b_write.py -- "$WK/graft_data.npz" "$WK/graft.blend" 2>&1 | grep -E "SAVED|rror" || true
"$B" -b "$WK/graft.blend" --python $A/b_dump.py -- "$WK/gd.npz" 2>&1 | grep -E "DUMPED|rror" || true
python $A/g2c/post.py "$WK/gd.npz" "$WSRC" "$WVG" "$PEOPLE" "$WK/post"
"$B" -b "$WK/graft.blend" --python $A/g2b/w_write.py -- "$WK/post/P.npy" "$WK/post/VG.npy" "$WK/post/names.npy" $SRC/heroine_built_armroot.blend 2>&1 | grep -E "MOVED|WEIGHTS|SAVED|rror" || true
# g2e: the patch's UVs re-laid (cap + arm islands) and her paint re-baked into copies (armor_src/armroot_tex), packed into the armroot blend
if [ -z "${SKIP_G2E:-}" ]; then
  python $A/g2e/plan.py "$ARM_GRAFT_WORK"
  "$B" -b $SRC/heroine_built.blend --python $A/g2e/b_img.py -- "$ARM_GRAFT_WORK" 2>&1 | grep -E "IMG|rror" || true
  "$B" -b $SRC/heroine_built_armroot.blend --python $A/g2e/b_unwrap.py -- "$ARM_GRAFT_WORK" 2>&1 | grep -E "UNWRAP|rror" || true
  F0_1=${F0_1:-0.72} python $A/g2e/bake.py "$ARM_GRAFT_WORK" "$(cygpath -w $SRC/armroot_tex)"
  "$B" -b $SRC/heroine_built_armroot.blend --python $A/g2e/b_apply.py -- "$ARM_GRAFT_WORK" "$(cygpath -w $SRC/armroot_tex)" 2>&1 | grep -E "IMAGE|SAVED|rror" || true
fi
mkdir -p "$WK/exp_$TAG"
( cd $W && NAPE=0 "$B" -b $SRC/heroine_built_armroot.blend --python tools/assets/heroine_outfits.py -- "$WK/exp_$TAG/x" --body "$WK/exp_$TAG/heroine.glb" --only warden ) > "$WK/exp_$TAG.log" 2>&1
( cd $W && git checkout -- tools/assets/heroine_neck_graft.npz )
ls "$WK/exp_$TAG"; tail -3 "$WK/exp_$TAG.log"
