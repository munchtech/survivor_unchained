param([string]$tag = 'd1', [switch]$noimport, [string[]]$only = @())
# One godot turn: import, then her face unshaded (paint only) and every preset shaded with her eyes held open.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: diagnostics" --wait 90 | Out-Null
if (-not $noimport) {
    & 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\import.log"
    "import exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
}
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
& "$sc\shot.ps1" "${tag}_u_long" 8 --new --sex female --step 1 --part 1 --hair long --open-eyes --unshaded
& "$sc\shot.ps1" "${tag}_u_pony_r" 8 --new --sex female --step 1 --part 1 --hair ponytail --turn -40 --open-eyes --unshaded
& "$sc\shot.ps1" "${tag}_long" 8 --new --sex female --step 1 --part 1 --hair long --open-eyes
foreach ($p in $presets) {
    if ($p.id -eq 'own') { continue }
    if ($only.Count -and $only -notcontains $p.id) { continue }
    & "$sc\shot.ps1" "${tag}_p_$($p.id)" 8 --new --sex female --step 1 --part 1 --hair ponytail --preset $p.id --skin $p.skin --eyes $p.eyes --open-eyes
    & "$sc\shot.ps1" "${tag}_u_$($p.id)" 8 --new --sex female --step 1 --part 1 --hair ponytail --preset $p.id --skin $p.skin --eyes $p.eyes --open-eyes --unshaded
}
python $T give godot "face: diagnostics" | Out-Null
"done $(Get-Date -Format HH:mm)"
