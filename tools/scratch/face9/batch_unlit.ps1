param([string]$tag = 'v12b', [string[]]$ids = @('doe', 'highborn'))
# One godot turn: the Look's close-up unshaded (paint as it is, no TAA), hers and some presets', front and turned.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag unlit" --wait 600 | Out-Null
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
$look = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail', '--unshaded', '--no-taa')
& "$sc\shot.ps1" "${tag}_u_own" 8 @look | Out-Null
foreach ($p in $presets) {
    if ($ids -notcontains $p.id) { continue }
    & "$sc\shot.ps1" "${tag}_u_$($p.id)" 8 @look --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
}
python $TP give godot "face: $tag unlit" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
