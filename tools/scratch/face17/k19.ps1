# k19: the jaw-edge rim: the fire's edge lamp higher
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'doe', 'own', 'saffron') { $runs += "u0_$f|$f|", "u8_$f|$f|--edge-up 0.8", "u13_$f|$f|--edge-up 1.3" }
& "$SC\look.ps1" -tag k19 -secs 10 -runs $runs
"K19 DONE $(Get-Date -Format HH:mm)"
