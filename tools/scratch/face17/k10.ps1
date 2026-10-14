# k10: the sky ambient at the Look
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'vixen') { $runs += "a0_$f|$f|--look-ambient 0", "a5_$f|$f|--look-ambient 0.5" }
& "$SC\look.ps1" -tag k10 -secs 10 -runs $runs
"K10 DONE $(Get-Date -Format HH:mm)"
