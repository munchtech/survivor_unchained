# r.sh "RUN_OFF0, RUN_LP0 = ..." "RUN_DH, RUN_BL = ..." "RUN_HDH, RUN_HBL = ..."
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40/tools/anim
[ -n "$1" ] && sed -i "s/^RUN_OFF0, RUN_LP0 = .*/$1/" clips/axe.py
[ -n "$2" ] && sed -i "s/^RUN_DH, RUN_BL = .*/$2/" clips/axe.py
[ -n "$3" ] && sed -i "s/^RUN_HDH, RUN_HBL = .*/$3/" clips/axe.py
python build.py --no-pack axe_fore_run axe_heavy_run >/dev/null
cd ../scratch/anim40/solver_atk7a; python rr.py axe_fore_run 0,1,2,5,7,9,11; python rr.py axe_heavy_run 6,8,10
