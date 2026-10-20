# tw.sh "<WAND_L tuple>": rebuild the wand run and sprint with it, measure
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40/tools/anim
python - "$1" <<'PY'
import re,sys
f='clips/run.py'; s=open(f).read()
s=re.sub(r'^WAND_L = .*$', 'WAND_L = '+sys.argv[1], s, flags=re.M)
open(f,'w').write(s)
PY
python build.py --no-pack run_arcanist_wand sprint_arcanist_wand > /dev/null 2>&1
for c in run_arcanist_wand sprint_arcanist_wand; do python ../scratch/anim40/solver_atk7c/m7c.py $c $2; done
