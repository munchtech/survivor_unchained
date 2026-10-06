param([string]$sheet, [string]$out, [string]$cam = "face", [string]$yaw = "0", [string]$res = "1600x900", [string]$clip = "", [string]$outfit = "")
# FaceSheet from my worktree: SHEET json in face2, OUT folder in face2.
$d = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$env:SHEET = Join-Path $d $sheet
$env:OUT = Join-Path $d $out
$env:CAM = $cam
$env:YAW = $yaw
$env:CLIP = $clip
$env:OUTFIT = $outfit
if (Test-Path $env:OUT) { Get-ChildItem $env:OUT -Filter *.png | ForEach-Object { [System.IO.File]::Delete($_.FullName) } }
& "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe" --path "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994\godot" --resolution $res --script res://tools_scenes/face_sheet.gd 2>&1 | Select-String -Pattern "ERROR|Exception" | Select-Object -First 8
