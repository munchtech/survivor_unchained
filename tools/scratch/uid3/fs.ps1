param([string]$sheet, [string]$out, [string]$cam = "face", [string]$yaw = "0", [string]$res = "1600x900", [string]$w = "420")
$d = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3'
$env:SHEET = Join-Path $d $sheet
$env:OUT = Join-Path $d $out
$env:CAM = $cam
$env:YAW = $yaw
if (Test-Path $env:OUT) { Get-ChildItem $env:OUT -Filter *.png | ForEach-Object { [System.IO.File]::Delete($_.FullName) } }
& "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe" --path "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a69858664f1d3dd29\godot" --resolution $res --script res://tools_scenes/face_sheet.gd 2>&1 | Select-String -Pattern "ERROR|Exception" | Select-Object -First 8
python (Join-Path $d "contact.py") $env:OUT $w
