# k6: all ten at -3 cm, body lift 1 (a_) and 1.6 (b_), the lift gated by facing (-0.15..0.15)
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "a_$f|$f|--neck-cm -3 --body-lift 1", "b_$f|$f|--neck-cm -3 --body-lift 1.6" }
& "$SC\look.ps1" -tag k6 -secs 10 -runs $runs
"K6 DONE $(Get-Date -Format HH:mm)"
