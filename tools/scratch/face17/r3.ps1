# Round r3: the rig (key 1.3, size 0.3, high and frontal; fill 1/0.98/0.96; bounce 0.045), the tone trims, the window
# catchlight, ears re-laid; all ten, turned 40 and 80, own untrimmed; the neck lengths (Look and play) with the nape weld.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|" }
foreach ($f in 'own', 'highborn', 'sunborn', 'saffron') { $runs += "${f}_t40|$f|--turn 40" }
$runs += "own_t80|own|--turn 80", "own_untrim|own|--tone-trim off", "highborn_untrim|highborn|--tone-trim off"
$runs += "own_bust|own|--zoom 0.55", "own_full|own|--zoom 0"
foreach ($n in '0', '-1.5', '-3') { $runs += "nk${n}_f|own|--zoom 0.55 --neck-cm $n", "nk${n}_p|own|--zoom 0.55 --turn 90 --neck-cm $n" }
foreach ($n in '0', '-1.5', '-3') { $runs += "play12_nk$n|raw|--quick warden --sex female --zone waystation --time day --cam 12 --neck-cm $n" }
& "$SC\look.ps1" -tag r3 -import -secs 10 -runs $runs
"R3 DONE $(Get-Date -Format HH:mm)"
