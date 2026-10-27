# Body 2 A: every target number on an exported glb dir (heroine.glb inside), written to <dir>/m_*.txt
#   bash meas_a.sh <exp dir>
set -u
D=$1; DW=$(cygpath -w "$D")
B=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/23290ad1-ed63-4a0d-8e12-ac0911d16c27/scratchpad/body2
V=$(cd "$(dirname "$0")" && pwd); A=$V/..
( cd $B/d_a && ANIM_PEOPLE="$DW" python sh.py A > "$D/m_sh.txt" 2>&1 ) &
( cd $B/d_b && TAGS=mine MINE_GLB="$DW\heroine.glb" python $V/m3f.py > "$D/m_m3.txt" 2>&1 ) &
( cd $A/g2a && python run_base.py "$DW" A > "$D/m_crease.txt" 2>&1 ) &
( cd $B/d_b && python $V/hp_lr.py "$DW\heroine.glb" > "$D/m_hplr.txt" 2>&1 ) &
( cd $B/d_c && python -c "import sys; sys.path.insert(0,'.'); import m; m.BODIES['graft']=r'$DW\heroine.glb'; exec(open('f.py').read())" > "$D/m_widths.txt" 2>&1 ) &
( cd $B/d_c && python $V/proud_a.py "$DW\heroine.glb" > "$D/m_proud.txt" 2>&1 ) &
wait; echo MEAS_DONE
