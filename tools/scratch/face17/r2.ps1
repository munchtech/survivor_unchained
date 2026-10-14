# Round r2: key light size 0.3 (default now) vs 0.2, key energy 1.15 vs 1.3; window catchlight; four faces.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'vixen', 'fey', 'doe') {
  $runs += "${f}|$f|", "${f}_e13|$f|--rig 1.3,0.22,0.8,0.55", "${f}_s2|$f|--key-shadow 0.2 --rig 1.25,0.22,0.8,0.55"
}
& "$SC\look.ps1" -tag r2 -import -runs $runs
"R2 DONE $(Get-Date -Format HH:mm)"
