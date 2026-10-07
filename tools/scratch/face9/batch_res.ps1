param([string]$tag = 'v12d', [string]$turn = '-15')
# One godot turn: Doe and her own face square to the camera at the Look, unshaded (no TAA) and lit, at 1080 and 2160:
# what the screen's size and the render's filtering do to fine features.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag resolution" --wait 600 | Out-Null
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail', '--turn', $turn)
$doe = @('--preset', 'doe', '--skin', 'rose', '--eyes', 'chestnut')
& "$sc\shot.ps1" "${tag}_u_doe" 8 @look @doe --unshaded --no-taa | Out-Null
& "$sc\shotr.ps1" "${tag}_u_doe_4k" 8 '3840x2160' @look @doe --unshaded --no-taa | Out-Null
& "$sc\shot.ps1" "${tag}_l_doe" 8 @look @doe | Out-Null
& "$sc\shotr.ps1" "${tag}_l_doe_4k" 8 '3840x2160' @look @doe | Out-Null
& "$sc\shot.ps1" "${tag}_u_own" 8 @look --unshaded --no-taa | Out-Null
& "$sc\shotr.ps1" "${tag}_u_own_4k" 8 '3840x2160' @look --unshaded --no-taa | Out-Null
python $TP give godot "face: $tag resolution" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
