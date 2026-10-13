# What lights the shade under her jaw: each light taken out in turn (own and highborn at the Look).
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn') {
  $runs += "${f}_nofill|$f|--rig 1.15,0,0.8,0.55", "${f}_noedge|$f|--rig 1.15,0.22,0,0.55", "${f}_norim|$f|--rig 1.15,0.22,0.8,0", "${f}_nokey|$f|--rig 0,0.22,0.8,0.55"
  $runs += "${f}_ks15|$f|--key-shadow 0.15", "${f}_high|$f|--key-at 0.4,1.8", "${f}_white|$f|--rig-white", "${f}_nossao|$f|--ssao off"
}
$runs += "own_dark|own|--rig 0,0,0,0 --bounce 0"
& "$SC\look.ps1" -tag d1 -import -runs $runs
"D1 DONE $(Get-Date -Format HH:mm)"
