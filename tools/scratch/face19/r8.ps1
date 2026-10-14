# Round r8, the skin judge batch (face 19): ears re-toned from the render (heroine_ears.py --render), Vixen/Moonlit/Fey
# soft tones at the fair faces' median, the edge lamp at 1.3 m by default, the neck sheet at today/-1/-2/-3, play by day
# and by night (own, Sunborn).
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|", "${f}_t40|$f|--turn 40", "e_$f|$f|--turn 40 --hair pixie" }
$runs += "own_bust|own|--zoom 0.55", "own_full|own|--zoom 0"
foreach ($n in '0', '-1', '-2', '-3') { $runs += "nk${n}_f|own|--zoom 0.55 --neck-cm $n", "nk${n}_p|own|--zoom 0.55 --turn 90 --neck-cm $n", "pf_nk$n|raw|--quick warden --sex female --zone waystation --time day --cam 12 --facing 0 --neck-cm $n" }
foreach ($t in 'day', 'night') {
    $runs += "pl_own_$t|raw|--quick warden --sex female --zone waystation --time $t --cam 6 --facing 0"
    $runs += "pl_sunborn_$t|raw|--quick warden --sex female --preset sunborn --skin brown --eyes sloe --zone waystation --time $t --cam 6 --facing 0"
}
& "$SC\look.ps1" -tag r8 -import -secs 10 -runs $runs
"R8 DONE $(Get-Date -Format HH:mm)"
