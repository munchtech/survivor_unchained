# Round r11 (face 22, skin solver): HerKeyTone to the lit neck, HerEdgeTone (edge_tone) on the far side of her neck; r9's pose.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|", "${f}_t40|$f|--turn 40", "e_$f|$f|--turn 40 --hair pixie" }
$runs += "own_bust|own|--zoom 0.55", "own_full|own|--zoom 0"
foreach ($n in '0', '-1', '-2', '-3') { $runs += "nk${n}_f|own|--zoom 0.55 --neck-cm $n --mark-bones --mark-offset 0.075,0.085", "nk${n}_p|own|--zoom 0.55 --turn 90 --neck-cm $n --mark-bones --mark-offset 0.075,0.085" }
& "$SC\look.ps1" -tag r11 -secs 10 -runs $runs
"R11 DONE $(Get-Date -Format HH:mm)"
