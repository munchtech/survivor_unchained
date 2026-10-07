param([string]$tag = 'sp1', [string]$zoom = '0.62')
# One godot turn: what speckles her breasts. Her bust at the Look (the portrait's light), as merged (scatter 0.38)
# and at her new scatter 0.1, with her body's grain tile off, its pores' relief off, her freckles off, and her
# paint alone (unshaded); and the book by day and by night at the owner's 2560x1440, as merged and without the grain.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag speckle" --wait 600 | Out-Null
$bust = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail', '--zoom', $zoom)
& "$sc\shot.ps1" "${tag}_bust_was" 8 @bust --skinparam scatter=0.38 | Out-Null
& "$sc\shot.ps1" "${tag}_bust" 8 @bust | Out-Null
& "$sc\shot.ps1" "${tag}_bust_g0" 8 @bust --grain 0 | Out-Null
& "$sc\shot.ps1" "${tag}_bust_g0_p0" 8 @bust --grain 0 --skinparam pore_depth=0 | Out-Null
& "$sc\shot.ps1" "${tag}_bust_g0_f0" 8 @bust --grain 0 --skinparam freckle_amount=0 | Out-Null
& "$sc\shot.ps1" "${tag}_bust_u" 8 @bust --unshaded --no-taa | Out-Null
& "$sc\shot.ps1" "${tag}_bust_u_g0" 8 @bust --unshaded --no-taa --grain 0 | Out-Null
$base = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--open-eyes')
& "$sc\shotr.ps1" "${tag}_bk_day_was" 9 '2560x1440' @base --zone verge --time day --open inventory --skinparam scatter=0.38 | Out-Null
& "$sc\shotr.ps1" "${tag}_bk_day_g0" 9 '2560x1440' @base --zone verge --time day --open inventory --grain 0 | Out-Null
& "$sc\shotr.ps1" "${tag}_bk_night_was" 9 '2560x1440' @base --zone verge --time night --open character --skinparam scatter=0.38 | Out-Null
& "$sc\shotr.ps1" "${tag}_bk_night_g0" 9 '2560x1440' @base --zone verge --time night --open character --grain 0 | Out-Null
python $TP give godot "face: $tag speckle" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
