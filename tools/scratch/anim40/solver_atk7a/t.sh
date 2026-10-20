# t.sh "HR5, HR7 = a, b" "HH6, HH10, HP6, HP10 = ..."
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40/tools/anim
sed -i "s/^HR5, HR7 = .*/$1/; s/^HH6, HH10, HP6, HP10 = .*/$2/" clips/axe.py
python build.py --no-pack axe_fore axe_heavy axes_right >/dev/null
cd ../scratch/anim40/solver_atk7a
for c in axe_fore axe_heavy axes_right; do python hr.py $c --base self --frames 4-12 | awk '{printf "%s ", ($1=="axe_fore"||$1=="axe_heavy"||$1=="axes_right")?"\n"$1":":$1"/"$2"/"$3"/s"$15}'; python hr.py $c --base run_reaver --bf 9 --frames 4-12 | awk '{printf "%s ", ($1=="axe_fore"||$1=="axe_heavy"||$1=="axes_right")?"\n run:":$1"/"$2"/"$3"/s"$15}'; done; echo
