# wexp.sh <P.npy> <VG.npy> <tag> : write armroot blend, export body+warden to g2/exp_<tag>, restore neck graft npz
set -u
W=C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-7
G=C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/543ece4a-9bcd-4cea-b6df-915822bec5eb/scratchpad/armor18/g2
B=C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe
SRC=C:/Users/munch/Desktop/survivorsunchained_inputs/armor_src
cd $W
python tools/turn.py take blender "body1 g2b: write+export $3" --wait 2400 --root $W 2>&1 | tail -1
$B -b $SRC/heroine_built_armroot_g1.blend --python $G/w_write.py -- $1 $2 $G/names.npy $SRC/heroine_built_armroot.blend 2>&1 | grep -E "MOVED|WEIGHTS|SAVED|Error|rror:" 
mkdir -p $G/exp_$3
( time NAPE=0 $B -b $SRC/heroine_built_armroot.blend --python tools/assets/heroine_outfits.py -- $G/exp_$3/x --body $G/exp_$3/heroine.glb --only warden ) > $G/exp_$3.log 2>&1
git checkout -- tools/assets/heroine_neck_graft.npz
python tools/turn.py give blender "body1 g2b: write+export $3" --root $W 2>&1 | tail -1
ls $G/exp_$3; tail -4 $G/exp_$3.log
