# Round r7 (the lit neck's key-only body lift, the soft lamps' shade tone per face, trims k14; ears reshot; neck sheet with
# play facing the camera): the judge batch.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|", "s3_$f|$f|--neck-cm -3" }
foreach ($f in 'own', 'highborn', 'sunborn', 'saffron') { $runs += "${f}_t40|$f|--turn 40" }
$runs += "own_t80|own|--turn 80", "own_bust|own|--zoom 0.55", "own_full|own|--zoom 0"
$runs += "own_was|own|--body-lift 1 --soft-tone 1,1,1", "highborn_was|highborn|--body-lift 1 --soft-tone 1,1,1", "own_untrim|own|--tone-trim off", "highborn_untrim|highborn|--tone-trim off"
foreach ($n in '0', '-1.5', '-2', '-3') { $runs += "nk${n}_f|own|--zoom 0.55 --neck-cm $n", "nk${n}_p|own|--zoom 0.55 --turn 90 --neck-cm $n", "pf_nk$n|raw|--quick warden --sex female --zone waystation --time day --cam 12 --facing 0 --neck-cm $n" }
$runs += "play12_nk0|raw|--quick warden --sex female --zone waystation --time day --cam 12 --neck-cm 0"
$runs += "pf6|raw|--quick warden --sex female --zone waystation --time day --cam 6 --facing 0", "pf6_was|raw|--quick warden --sex female --zone waystation --time day --cam 6 --facing 0 --body-lift 1 --soft-tone 1,1,1"
$runs += "doe_eu13|doe|--edge-up 1.3", "doe_ta|doe|--skin-set *:terminator=0.2/0.15/0.1", "sunborn_eu13|sunborn|--edge-up 1.3", "hardwon_eu13|hardwon|--edge-up 1.3"
& "$SC\look.ps1" -tag r7 -secs 10 -runs $runs
"R7 DONE $(Get-Date -Format HH:mm)"
