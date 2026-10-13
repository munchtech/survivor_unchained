# k11: soft_tone probes
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'vixen') { $runs += "h_$f|$f|--skin-set *:soft_tone=0.5/0.5/0.5", "w_$f|$f|--skin-set *:soft_tone=1.3/1.0/0.75" }
& "$SC\look.ps1" -tag k11 -secs 10 -runs $runs
"K11 DONE $(Get-Date -Format HH:mm)"
