param([string]$tag = 'v12g', [string]$turn = '-15')
# One godot turn, the no-refit fixes tried at the Look (square to the camera): her skin's scattering at 0.1 and 0.2,
# Doe's brows raised by the brows_height slider, Sunborn's upper lip by lips_upper, Highborn's lid at rest, and her
# irises a little larger.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag tries" --wait 600 | Out-Null
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--turn', $turn)
$open = @('--open-eyes')
$doe = @('--preset', 'doe', '--skin', 'rose', '--eyes', 'chestnut')
$sun = @('--preset', 'sunborn', '--skin', 'brown', '--eyes', 'sloe')
$high = @('--preset', 'highborn', '--skin', 'fair', '--eyes', 'frost')
& "$sc\shot.ps1" "${tag}_own_s10" 8 @look @open --skinparam scatter=0.1 | Out-Null
& "$sc\shot.ps1" "${tag}_own_s20" 8 @look @open --skinparam scatter=0.2 | Out-Null
& "$sc\shot.ps1" "${tag}_w_own_s10" 8 @look @open --rig-white --skinparam scatter=0.1 | Out-Null
& "$sc\shot.ps1" "${tag}_w_doe_s10" 8 @look @open @doe --rig-white --skinparam scatter=0.1 | Out-Null
& "$sc\shot.ps1" "${tag}_doe_bh06" 8 @look @open @doe --skinparam scatter=0.1 --face brows_height=0.6 | Out-Null
& "$sc\shot.ps1" "${tag}_doe_bh10" 8 @look @open @doe --skinparam scatter=0.1 --face brows_height=1.0 | Out-Null
& "$sc\shot.ps1" "${tag}_doe_s10" 8 @look @open @doe --skinparam scatter=0.1 | Out-Null
& "$sc\shot.ps1" "${tag}_sun_s10" 8 @look @open @sun --skinparam scatter=0.1 | Out-Null
& "$sc\shot.ps1" "${tag}_sun_lu06" 8 @look @open @sun --skinparam scatter=0.1 --face lips_upper=0.6 | Out-Null
& "$sc\shot.ps1" "${tag}_sun_lu10" 8 @look @open @sun --skinparam scatter=0.1 --face lips_upper=1.0 | Out-Null
& "$sc\shot.ps1" "${tag}_high_s10" 8 @look @open @high --skinparam scatter=0.1 | Out-Null
& "$sc\shot.ps1" "${tag}_high_l15" 8 @look @high --skinparam scatter=0.1 --lids 0.15 | Out-Null
& "$sc\shot.ps1" "${tag}_high_l30" 8 @look @high --skinparam scatter=0.1 --lids 0.3 | Out-Null
& "$sc\shot.ps1" "${tag}_own_ir13" 8 @look @open --skinparam scatter=0.1 --eyeparam iris_r=0.13 | Out-Null
python $TP give godot "face: $tag tries" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
