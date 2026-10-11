# Round r1: the new rig (fill 1/0.98/0.96, bounce 0.045, key at side 0.55 up 1.25, shadow on) on all ten; profiles; key variants.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|" }
foreach ($f in 'own', 'highborn', 'sunborn') { $runs += "${f}_t40|$f|--turn 40" }
$runs += "own_t80|own|--turn 80"
$runs += "own_kA|own|--key-at 0.35,1.4", "own_kB|own|--key-at 0.8,1.1", "highborn_kA|highborn|--key-at 0.35,1.4", "highborn_kB|highborn|--key-at 0.8,1.1"
$runs += "own_bust|own|--zoom 0.55"
& "$SC\look.ps1" -tag r1 -import -runs $runs
"R1 DONE $(Get-Date -Format HH:mm)"
