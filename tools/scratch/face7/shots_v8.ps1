param([string]$tag = 'v8', [switch]$nocal, [switch]$noplay, [string[]]$only = @())
# One godot turn: her default face (the four-column side-by-side), every preset at the Look's close-up (the ten-face
# sheet, each under its reference), her irises dyed through a range (the eye calibration), her at play zoom, and her
# paint unshaded. Eyes held open (--open-eyes): no blink caught.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$s4 = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$g = "$w\godot\.shots"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: $tag shots" --wait 120 | Out-Null
if (-not $only.Count) {
    & "$sc\shot.ps1" "${tag}_long" 8 --new --sex female --step 1 --part 1 --hair long --open-eyes | Out-Null
    & "$sc\shot.ps1" "${tag}_pony" 8 --new --sex female --step 1 --part 1 --hair ponytail --open-eyes | Out-Null
    & "$sc\shot.ps1" "${tag}_pony_r" 8 --new --sex female --step 1 --part 1 --hair ponytail --turn -40 --open-eyes | Out-Null
    & "$sc\shot.ps1" "${tag}_u_long" 8 --new --sex female --step 1 --part 1 --hair long --open-eyes --unshaded | Out-Null
}
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
foreach ($p in $presets) {
    if ($p.id -eq 'own') { continue }
    if ($only.Count -and $only -notcontains $p.id) { continue }
    & "$sc\shot.ps1" "${tag}_p_$($p.id)" 8 --new --sex female --step 1 --part 1 --hair ponytail --preset $p.id --skin $p.skin --eyes $p.eyes --open-eyes | Out-Null
}
if (-not $nocal) {
    $cal = 'paint,#0c0c0c,#1a1a1a,#2a2a2a,#3c3c3c,#565656,#787878,#a0a0a0,#3a2014,#20304a,#304a24,#6a3a1c,#4a6a8a,#8a6a4a'
    & "$sc\shot.ps1" "${tag}_eyecal" 8 --new --sex female --step 1 --part 1 --hair ponytail --open-eyes --eyecycle $cal --every 1 --count 14 | Out-Null
}
if (-not $noplay) {
    foreach ($c in 12.5, 22, 31) {
        & "$sc\shot.ps1" "${tag}_play_c$c" 9 --quick warden --sex female --hair long --zone arena --people dead --auto toward --cam $c | Out-Null
    }
}
python $T give godot "face: $tag shots" | Out-Null
"shots done $(Get-Date -Format HH:mm)"
python "$sc\sheets.py" $tag
