param([string]$out, [string]$jobs = 'job_own.json', [string]$lights = '', [string]$skin = '', [string]$draw = '', [string]$size = '1024', [string]$keyshadow = '', [switch]$import, [switch]$noturn)
# Portraits.cs run on a job list (face7\<jobs>) into face7\<out>: LIGHTS=k,f,r, SKIN=name=v,..., DEBUGDRAW=view.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
$G = 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
if (-not $noturn) { python $T take godot "face: portrait probe" --wait 120 | Out-Null }
if ($import) { & $G --headless --path "$w\godot" --import *> "$sc\import_pk.log"; "import exit $LASTEXITCODE" }
$env:JOBS = "$sc\$jobs"; $env:OUT = "$sc\$out"; $env:SIZE = $size; $env:LIGHTS = $lights; $env:SKIN = $skin; $env:DEBUGDRAW = $draw; $env:KEYSHADOW = $keyshadow
New-Item -ItemType Directory -Force "$sc\$out" | Out-Null
& $G --path "$w\godot" --resolution 1280x720 --script res://tools_scenes/portraits.gd *> "$sc\$out\log.txt"
$env:JOBS = ''; $env:OUT = ''; $env:SIZE = ''; $env:LIGHTS = ''; $env:SKIN = ''; $env:DEBUGDRAW = ''; $env:KEYSHADOW = ''
if (-not $noturn) { python $T give godot "face: portrait probe" | Out-Null }
"[$out] " + ((Get-Content "$sc\$out\log.txt" | Select-String -Pattern '^PORTRAIT|ERROR|Exception' | Select-Object -First 6) -join ' | ')
