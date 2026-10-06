param([string]$outdir, [string]$angles = "0,20,30,40")
# Her own face (FACE) rendered at several turns, its landmarks read, and anchored on her mesh with every
# slider target's moves: $outdir\a_<angle>.npz each (for face_presets.py fit).
$W = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6784044c82f101d9'
$PY = 'C:\Users\munch\AppData\Local\facefit\.venv\Scripts\python.exe'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
New-Item -ItemType Directory -Force $outdir | Out-Null
'{"her": {}}' | Set-Content -Encoding ascii "$outdir\face.json"
& $PY "$W\tools\assets\face_presets.py" targets "$outdir\targets.json"
& $B -b --python "$W\tools\assets\face_lab.py" -- render "$outdir\face.json" $outdir $angles 2>&1 | Select-String -Pattern "Error|Traceback" | Select-Object -First 5
foreach ($a in $angles.Split(",")) {
    & $PY "$W\tools\assets\face_fit.py" marks "$outdir\her_$a.png" "$outdir\lm_$a.json" whole "$outdir\_cams.json" "her_$a" 2>$null | Out-Null
    & $B -b --python "$W\tools\assets\face_lab.py" -- anchor "$outdir\lm_$a.json" "$outdir\a_$a.npz" "$outdir\targets.json" "$outdir\face.json" her 2>&1 | Select-String -Pattern "ANCHORS|Error|Traceback" | Select-Object -First 3
}
