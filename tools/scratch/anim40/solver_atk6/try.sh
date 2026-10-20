# try.sh "<AXES_L tuple>" "<thumb tuple>": rebuild run_reaver_axes with these and print the left axe head (+Y mount)
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40
python - "$1" "$2" <<'PY'
import re,sys
f='tools/anim/clips/run.py'; s=open(f).read()
s=re.sub(r'^AXES_L = .*$', 'AXES_L = '+sys.argv[1], s, flags=re.M)
s=re.sub(r'def axe_trail\(thumb=\(.*?\)\):', 'def axe_trail(thumb='+sys.argv[2]+'):', s)
open(f,'w').write(s)
PY
python tools/anim/build.py --no-pack run_reaver_axes > /dev/null 2>&1
cd tools/anim && python ../scratch/anim40/solver_atk6/axl.py run_reaver_axes | sed -n '1p;4p;7p;10p;13p;16p'
