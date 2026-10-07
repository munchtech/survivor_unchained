param([string]$tag = 'v12f', [string]$turn = '-15')
# One godot turn: whether her skin's screen-space scattering blurs her paint at the Look (unshaded and lit, scatter
# on and off), Doe and her own face square to the camera; and the world's SSS scale halved.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag scatter" --wait 600 | Out-Null
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail', '--turn', $turn)
$doe = @('--preset', 'doe', '--skin', 'rose', '--eyes', 'chestnut')
& "$sc\shot.ps1" "${tag}_u_doe_s0" 8 @look @doe --unshaded --no-taa --tonemap linear --grade off --skinparam scatter=0 | Out-Null
& "$sc\shot.ps1" "${tag}_w_doe_s0" 8 @look @doe --rig-white --skinparam scatter=0 | Out-Null
& "$sc\shot.ps1" "${tag}_w_doe_s0_notaa" 8 @look @doe --rig-white --skinparam scatter=0 --no-taa | Out-Null
& "$sc\shot.ps1" "${tag}_w_own_s0" 8 @look --rig-white --skinparam scatter=0 | Out-Null
& "$sc\shot.ps1" "${tag}_l_own_s0" 8 @look --skinparam scatter=0 | Out-Null
& "$sc\shot.ps1" "${tag}_l_own" 8 @look | Out-Null
python $TP give godot "face: $tag scatter" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
