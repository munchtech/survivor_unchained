param([string]$tag = 'ss', [string[]]$scales = @('0.15', '0.4'), [string]$quality = '2')
# Godot's screen-space scattering made wider (override.cfg, taken away after): her throat under the key alone.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: sss scale" --wait 120 | Out-Null
foreach ($s in $scales) {
    "[rendering]`nenvironment/subsurface_scattering/subsurface_scattering_quality=$quality`nenvironment/subsurface_scattering/subsurface_scattering_scale=$s`n" | Set-Content -Encoding ascii "$w\godot\override.cfg"
    & "$sc\pk.ps1" "${tag}_$s" -noturn -lights '1,0,0'
    & "$sc\pk.ps1" "${tag}_${s}_all" -noturn
}
Remove-Item "$w\godot\override.cfg" -Force
python $T give godot "face: sss scale" | Out-Null
"sss scale done"
