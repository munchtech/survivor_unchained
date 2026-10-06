param([string]$jobs, [string]$out, [string]$size = "640")
# Portraits.cs on a job list: JOBS (json in uid3) to OUT (a folder in uid3), then a contact sheet.
$d = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3'
$env:JOBS = Join-Path $d $jobs
$env:OUT = Join-Path $d $out
$env:SIZE = $size
if (Test-Path $env:OUT) { Get-ChildItem $env:OUT -Filter *.png | ForEach-Object { [System.IO.File]::Delete($_.FullName) } }
& "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe" --path "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a69858664f1d3dd29\godot" --resolution 1280x720 --script res://tools_scenes/portraits.gd 2>&1 | Select-String -Pattern "ERROR|Exception|PORTRAIT" | Select-Object -First 30 | ForEach-Object { $_.Line }
python (Join-Path $d "contact.py") $env:OUT 320
