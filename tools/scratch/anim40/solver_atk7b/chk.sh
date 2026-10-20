cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40/tools/anim
S=../scratch/anim40/solver_atk7b
git show HEAD:tools/anim/clips/arts.py > clips/arts.py; git show HEAD:tools/anim/clips/actions.py > clips/actions.py
python build.py --no-pack chain_strike cast_flick > /dev/null
python motion.py chain_strike cast_flick --outfits > $S/motion_before.txt 2>&1
python audit.py chain_strike cast_flick > $S/audit_before.txt 2>&1
cp $S/arts_new.py clips/arts.py; cp $S/actions_new.py clips/actions.py
python build.py --no-pack chain_strike cast_flick > /dev/null
python motion.py chain_strike cast_flick --outfits > $S/motion_after.txt 2>&1
python audit.py chain_strike cast_flick > $S/audit_after.txt 2>&1
python fistfit.py axe > $S/fist_axe.txt 2>&1; python fistfit.py wand > $S/fist_wand.txt 2>&1
python armscheck.py chain_strike --sets axe --outfit reaver --jobs 3 > $S/arms_after.txt 2>&1
echo CHK DONE
