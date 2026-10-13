# Round r10 (face 21, skin solver): HerKeyTone (key_tone) on the fair faces; r9's pose (chin up 12). Usage: r10.ps1 [-quick]
param([switch]$quick)
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratch'
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
if ($quick) { & "$SC\look.ps1" -tag s10b -secs 10 -runs @("own|own|", "vixen|vixen|", "own_full|own|--zoom 0"); "S10B DONE"; return }
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|", "${f}_t40|$f|--turn 40", "e_$f|$f|--turn 40 --hair pixie" }
$runs += "own_bust|own|--zoom 0.55", "own_full|own|--zoom 0"
& "$SC\look.ps1" -tag r10 -secs 10 -runs $runs
"R10 DONE $(Get-Date -Format HH:mm)"
