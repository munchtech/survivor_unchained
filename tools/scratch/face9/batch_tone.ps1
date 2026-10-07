param([string]$tag = 'v12e', [string]$turn = '-15')
# One godot turn: Doe and her own face square to the camera at the Look through other tone curves and without the
# grade: what the world's AgX and its grade do to a face's darks.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag tone" --wait 600 | Out-Null
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail', '--turn', $turn)
$doe = @('--preset', 'doe', '--skin', 'rose', '--eyes', 'chestnut')
& "$sc\shot.ps1" "${tag}_u_doe_lin" 8 @look @doe --unshaded --no-taa --tonemap linear --grade off | Out-Null
& "$sc\shot.ps1" "${tag}_u_doe_agx_nog" 8 @look @doe --unshaded --no-taa --grade off | Out-Null
& "$sc\shot.ps1" "${tag}_u_doe_lin_g" 8 @look @doe --unshaded --no-taa --tonemap linear | Out-Null
& "$sc\shot.ps1" "${tag}_l_doe_lin" 8 @look @doe --tonemap linear --grade off | Out-Null
& "$sc\shot.ps1" "${tag}_w_doe_lin" 8 @look @doe --rig-white --tonemap linear --grade off | Out-Null
& "$sc\shot.ps1" "${tag}_w_doe" 8 @look @doe --rig-white | Out-Null
& "$sc\shot.ps1" "${tag}_u_own_lin" 8 @look --unshaded --no-taa --tonemap linear --grade off | Out-Null
& "$sc\shot.ps1" "${tag}_w_own_lin" 8 @look --rig-white --tonemap linear --grade off | Out-Null
& "$sc\shot.ps1" "${tag}_w_own" 8 @look --rig-white | Out-Null
python $TP give godot "face: $tag tone" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
