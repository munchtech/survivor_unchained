# num.sh TAG [faces]: meas.py (cheek, jaw, lit neck vs portrait) and neckx.py ((a) rows, (b) far neck) on TAG's front shots.
# Run from the worktree root with bash; the facefit venv.
PY=/c/Users/munch/AppData/Local/facefit/.venv/Scripts/python.exe; T=tools/scratch
q() { grep -v "^W0\|^I0\|INFO\|WARNING\|^\s*$\|clip%"; }
tag=$1; shift; f=$(echo "$@" | tr ' ' ',')
$PY $T/face17/meas.py $tag $f 2>&1 | q | awk '{print $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, "|", $12, $13, $14, $15, $16, $17, $18, $19, $20}'
$PY $T/face21/neckx.py $tag "$@" 2>&1 | q
