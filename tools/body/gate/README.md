# P1 gate (5 Nov): the bare A|B reshoot

`gate.sh` = F2's shot commands (A = shipped body, B = `--body p1 --p1-probe`), takes and gives back the godot turn.
`sheet.py captions.json <outdir>` lays the 1:1 sheet + four 1:1 pairs; `python tools/half.py <outdir>/GATE_sheet.png`
makes `GATE_sheet_half.jpg`. `gate.json`: each shot's hash, camera and the p1 retarget numbers. Sheet and pairs live in
`C:\Users\munch\Desktop\survivorsunchained_inputs\body_p1\` (shots are git-ignored in `godot/.shots/`).
