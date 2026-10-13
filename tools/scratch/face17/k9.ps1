# k9: what greys the jaw shade: rim off, edge off, fill off
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'vixen') { $runs += "r0_$f|$f|--rig 1.3,0.22,0.8,0", "e0_$f|$f|--rig 1.3,0.22,0,0.55", "f0_$f|$f|--rig 1.3,0,0.8,0.55" }
& "$SC\look.ps1" -tag k9 -secs 10 -runs $runs
"K9 DONE $(Get-Date -Format HH:mm)"
