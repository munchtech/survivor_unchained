param([string]$tag = 'v12a', [switch]$nowhite, [switch]$noplay, [switch]$nobook, [switch]$grainx, [switch]$noimport)
# One godot turn: (import if asked), every face under the white rig, the Look's default and the nine presets, her
# turned 40 degrees, the book by day and night, play zoom; with -grainx, the grain probes (no TAA, mip bias).
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag batch" --wait 600 | Out-Null
if (-not $noimport) {
    & 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\logs\import_$tag.log"
}
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes')
if (-not $nowhite) {
    & "$sc\shot.ps1" "${tag}_white" 8 @look --hair ponytail --rig-white | Out-Null
    foreach ($p in $presets) {
        if ($p.id -eq 'own') { continue }
        & "$sc\shot.ps1" "${tag}_w_$($p.id)" 8 @look --hair ponytail --rig-white --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
    }
}
& "$sc\shot.ps1" "${tag}_long" 8 @look --hair long | Out-Null
& "$sc\shot.ps1" "${tag}_pony" 8 @look --hair ponytail | Out-Null
& "$sc\shot.ps1" "${tag}_pony_r" 8 @look --hair ponytail --turn -40 | Out-Null
& "$sc\shot.ps1" "${tag}_pony_l" 8 @look --hair ponytail --turn 40 | Out-Null
foreach ($p in $presets) {
    if ($p.id -eq 'own') { continue }
    & "$sc\shot.ps1" "${tag}_p_$($p.id)" 8 @look --hair ponytail --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
}
if ($grainx) {
    & "$sc\shot.ps1" "${tag}_gx_notaa" 8 @look --hair ponytail --no-taa | Out-Null
    & "$sc\shot.ps1" "${tag}_gx_mb05" 8 @look --hair ponytail --mipbias -0.5 | Out-Null
    & "$sc\shot.ps1" "${tag}_gx_mb1" 8 @look --hair ponytail --mipbias -1 | Out-Null
    & "$sc\shot.ps1" "${tag}_gx_wnotaa" 8 @look --hair ponytail --rig-white --no-taa | Out-Null
    & "$sc\shot.ps1" "${tag}_gx_unlit" 8 @look --hair ponytail --unshaded | Out-Null
    & "$sc\shot.ps1" "${tag}_gx_unlit_notaa" 8 @look --hair ponytail --unshaded --no-taa | Out-Null
}
if (-not $nobook) {
    $base = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--open-eyes')
    & "$sc\shot.ps1" "${tag}_bk_pack" 9 @base --zone verge --time day --open inventory | Out-Null
    & "$sc\shot.ps1" "${tag}_bk_self" 9 @base --zone verge --time night --open character | Out-Null
    & "$sc\shot.ps1" "${tag}_bk_arts" 9 @base --zone verge --time day --open arts | Out-Null
}
if (-not $noplay) {
    $pz = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--auto', 'toward')
    & "$sc\shot.ps1" "${tag}_pz_day" 9 @pz --zone waystation --time day | Out-Null
    & "$sc\shot.ps1" "${tag}_pz_night" 9 @pz --zone waystation --time night | Out-Null
    & "$sc\shot.ps1" "${tag}_pz_verge" 9 @pz --zone verge --time day | Out-Null
    & "$sc\shot.ps1" "${tag}_pz_arena" 9 @pz --zone arena | Out-Null
    & "$sc\shot.ps1" "${tag}_pz_near" 9 @pz --zone waystation --time day --cam 12.5 | Out-Null
}
python $TP give godot "face: $tag batch" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
