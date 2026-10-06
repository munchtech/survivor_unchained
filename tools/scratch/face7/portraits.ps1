param([string]$kinds = '', [switch]$noimport, [switch]$noshots)
# Creation's portraits in one godot turn: import, creation_portraits.py (female), then the Look's parts and the calling.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: portraits" --wait 120 | Out-Null
if (-not $noimport) {
    & 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\import_portraits.log"
    "import exit $LASTEXITCODE"
}
$k = if ($kinds) { $kinds.Split(',') } else { @() }
python "$w\tools\assets\creation_portraits.py" @k --sex female --raw "$sc\portraits_raw" 2>&1
if (-not $noshots) {
    foreach ($p in 0, 1, 2, 3, 4) {
        & "$sc\shot.ps1" "look_part$p" 8 --new --sex female --step 1 --part $p | Out-Null
    }
    & "$sc\shot.ps1" "look_calling" 8 --new --sex female --step 0 | Out-Null
}
python $T give godot "face: portraits" | Out-Null
"done $(Get-Date -Format HH:mm)"
