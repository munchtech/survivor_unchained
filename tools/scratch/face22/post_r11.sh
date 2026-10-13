# After r11.ps1: numbers (S/r11/numbers_r11.txt) and the sheets. Run from the worktree root with bash.
PY=/c/Users/munch/AppData/Local/facefit/.venv/Scripts/python.exe
S='C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f19\r11'
T=tools/scratch; N="$S\numbers_r11.txt"; q() { grep -v "^W0\|^I0\|INFO\|WARNING\|^\s*$"; }
{ echo "== meas.py r11 (cheek, jaw, lit neck vs portrait)"; $PY $T/face17/meas.py r11 2>&1 | q
  echo; echo "== neckx.py r11: (a) rows, (b) far neck vs portrait neck-side shade"; $PY $T/face21/neckx.py r11 2>&1 | q
  echo; echo "== fullm.py (f)"; $PY $T/face21/fullm.py r10_own_full r11_own_full 2>&1 | q; } > "$N"
cp godot/.shots/r11_neckx.jpg "$S\r11_neckx.jpg" 2>/dev/null
$PY $T/face17/sheet3.py r11 "$S" > /dev/null 2>&1
$PY $T/face17/jawcrop.py "$S\jaw_r11.jpg" r11_vixen vixen_11 r11_fey fey_11 r11_moonlit moonlit_11 r11_own own_her_23 r11_highborn highborn_11 > /dev/null 2>&1
$PY $T/face17/edgecrop.py "$S\edge_r11.jpg" r11_own r11_highborn r11_moonlit r11_vixen > /dev/null 2>&1
for f in godot/.shots/r9_pf_nk*.png; do cp "$f" "${f/r9_pf_nk/r11_pf_nk}"; done
$PY $T/face19/neck_sheet2.py r11 "$S\neck_sheet.jpg" > /dev/null 2>&1
ls "$S"
