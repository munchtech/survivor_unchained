param([string]$faces, [string]$name, [string]$targets, [string]$outdir, [string]$angles = "0,20,30,40")
# Render a face at several turns, read each view's landmarks, anchor them on her mesh with the targets' moves:
# $outdir\a_<angle>.npz each.
$L = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face"
$W = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abfa9bb430ec2391e"
$PY = "C:\Users\munch\AppData\Local\facefit\.venv\Scripts\python.exe"
$B = "C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe"
New-Item -ItemType Directory -Force $outdir | Out-Null
$one = "$outdir\face.json"
$f = Get-Content $faces -Raw | ConvertFrom-Json
@{ $name = $f.$name } | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $one
& $B -b --python "$W\tools\assets\face_lab.py" -- render $one $outdir $angles 2>&1 | Select-String -Pattern "Error|Traceback" | Select-Object -First 5
foreach ($a in $angles.Split(",")) {
    & $PY "$W\tools\assets\face_fit.py" marks "$outdir\${name}_$a.png" "$outdir\lm_$a.json" whole "$outdir\_cams.json" "${name}_$a" 2>$null | Out-Null
    & $B -b --python "$W\tools\assets\face_lab.py" -- anchor "$outdir\lm_$a.json" "$outdir\a_$a.npz" $targets $one $name 2>&1 | Select-String -Pattern "ANCHORS|Error|Traceback" | Select-Object -First 3
}
