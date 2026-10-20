#!/bin/bash
# anim41: motion --outfits on the 17 axe clips, before (clips_before) and after, split in two, plus the 3 wand clips after.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40
cd $W; O=tools/scratch/anim40/chk; B=tools/scratch/anim40/fist/out/clips_before
A1="axe_back axe_fore axe_heavy axes_heavy axes_left axes_right chain_haul chain_strike idle_reaver"
A2="idle_reaver_break reaver_show run_reaver run_reaver_axes sprint_reaver sprint_reaver_axes stop_reaver_l stop_reaver_r"
python tools/anim/motion.py $A1 --outfits --folder $B > $O/m_before1.txt 2>&1 &
python tools/anim/motion.py $A2 --outfits --folder $B > $O/m_before2.txt 2>&1 &
python tools/anim/motion.py $A1 --outfits > $O/m_after1.txt 2>&1 &
python tools/anim/motion.py $A2 --outfits > $O/m_after2.txt 2>&1 &
python tools/anim/motion.py cast_flick run_arcanist_wand sprint_arcanist_wand --outfits > $O/m_wand_after.txt 2>&1 &
wait; echo MOTION DONE
