# t9.sh "<AXES_L>" "<AXE_HANG dict>" [-v]
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40/tools/anim
python - "$1" "$2" <<'PY'
import re,sys
f='clips/run.py'; s=open(f).read()
s=re.sub(r'^AXES_L = .*$', 'AXES_L = '+sys.argv[1], s, flags=re.M)
s=re.sub(r'^AXE_HANG = .*$', 'AXE_HANG = '+sys.argv[2], s, flags=re.M)
open(f,'w').write(s)
PY
python build.py --no-pack run_reaver_axes > /tmp/b9.txt 2>&1 || tail -5 /tmp/b9.txt
python ../scratch/anim40/solver_atk7c/m7c.py run_reaver_axes $3
python audit.py run_reaver_axes 2>&1 | grep -i "hand_l\|flagged" | tail -4
