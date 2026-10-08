param([string]$blend, [string]$script, [string]$tag = 'one', [Parameter(ValueFromRemainingArguments = $true)] $rest)
# One short blender turn: SCRIPT run on BLEND (in tools/comfy/out/heroes unless a full path) with the rest as its args.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abe65bc929823a791'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\face10'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
if (-not (Test-Path $blend)) { $blend = "$w\tools\comfy\out\heroes\$blend" }
New-Item -ItemType Directory -Force "$sc\logs" | Out-Null
python $T take blender "face: $tag" --wait 900 | Out-Null
& $B -b $blend --python $script -- @rest *> "$sc\logs\$tag.log"
"[$tag] exit $LASTEXITCODE"
python $T give blender "face: $tag" | Out-Null
Get-Content "$sc\logs\$tag.log" | Select-String -Pattern "Traceback|Error|^[A-Z][A-Z ]+[ :]" | Select-Object -Last 15
